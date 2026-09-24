"""Reference SMBus device with Packet Error Checking, written from the SMBus 3.x specification
(PEC = CRC-8, polynomial x^8 + x^2 + x + 1, initial 0, over every byte of the transaction
including address bytes), not from TRIPWIRE firmware. Built on the I2C target model.

Supported: Write Byte/Word with PEC, Read Byte/Word with PEC (command code selects a register).
"""

from .i2c import I2CTarget


def crc8(data, crc=0):
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


class SMBusDevice(I2CTarget):
    def __init__(self, addr, regs=None, **kw):
        super().__init__(addr, **kw)
        self.regs = dict(regs or {})                # command code -> 16-bit word
        self.tx = []                                # every byte of the transaction so far
        self.writes = []                            # (command, data bytes, pec_ok)
        self._served = 0

    def step(self, scl, sda):
        before = len(self.log)
        out = super().step(scl, sda)
        for entry in self.log[before:]:
            if entry == ("STOP",):
                self._end()
            elif entry[0] == "ADDR" and entry[2]:
                self.tx.append(entry[1])
                if entry[1] & 1:                    # a read: serve the word and its PEC
                    cmd = self.tx[1] if len(self.tx) > 1 else 0
                    word = self.regs.get(cmd, 0)
                    lo, hi = word & 0xFF, word >> 8
                    self.read_data = [lo, hi, crc8(self.tx + [lo, hi])]
                    self.tx += [lo, hi]
        while len(self.received) > self._served:     # bytes written to us
            self.tx.append(self.received[self._served])
            self._served += 1
        return out

    def _end(self):
        if self.tx and not self.tx[0] & 1 and len(self.tx) >= 3 and not any(t & 1 for t in self.tx[:1]):
            if self.tx.count(self.tx[0] | 1) == 0:     # a write transaction (no read address)
                cmd, body, pec = self.tx[1], self.tx[2:-1], self.tx[-1]
                ok = crc8(self.tx[:-1]) == pec
                self.writes.append((cmd, body, ok))
                if ok and len(body) == 2:
                    self.regs[cmd] = body[0] | body[1] << 8
        self.tx = []
