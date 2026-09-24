"""Reference LIN 2.x responder (slave) node, written from the LIN 2.2A specification, not from
TRIPWIRE firmware.

- Bytes are UART frames (start 0, 8 data bits LSB first, stop 1) at the bus bit rate.
- A header: break (dominant >= 11 bit times at the responder), break delimiter, sync 0x55,
  protected ID = ID[5:0] | P0 << 6 | P1 << 7, P0 = ID0^ID1^ID2^ID4, P1 = ~(ID1^ID3^ID4^ID5).
- Response: n data bytes and a checksum = ~(sum with end-around carry); the enhanced checksum
  includes the PID, the classic one (IDs 60/61) does not.
Clock-level: step(bus) -> drive (1 = recessive).
"""


def pid_of(fid):
    b = [(fid >> i) & 1 for i in range(6)]
    p0 = b[0] ^ b[1] ^ b[2] ^ b[4]
    p1 = 1 - (b[1] ^ b[3] ^ b[4] ^ b[5])
    return fid | p0 << 6 | p1 << 7


def checksum(fid, data):
    s = pid_of(fid) if fid not in (60, 61) else 0
    for d in data:
        s += d
        if s > 255:
            s -= 255
    return (~s) & 0xFF


class LINResponder:
    def __init__(self, bit_clocks, publish=None, subscribe=None, bad_checksum=()):
        self.T = float(bit_clocks)
        self.publish = dict(publish or {})          # ID -> data bytes we send
        self.subscribe = dict(subscribe or {})      # ID -> n bytes we expect
        self.bad = set(bad_checksum)                # IDs whose checksum we corrupt
        self.headers = []                           # (ID, parity_ok)
        self.received = []                          # (ID, data, checksum_ok)
        self.drive = 1
        self._bus = 1
        self._gen = self._run()
        next(self._gen)

    def step(self, bus):
        self._bus = bus
        next(self._gen)
        return self.drive

    def _wait(self, n):
        for _ in range(int(round(n))):
            yield

    def _fall(self):
        while self._bus == 0:
            yield
        while self._bus == 1:
            yield

    def _byte(self):
        """A UART frame starting at the falling edge we are at; returns (byte, stop_ok)."""
        yield from self._wait(self.T / 2)
        bits = []
        for _ in range(9):
            yield from self._wait(self.T)
            bits.append(self._bus)
        return sum(b << i for i, b in enumerate(bits[:8])), bits[8] == 1

    def _send(self, data):
        for byte in data:
            for b in [0] + [(byte >> i) & 1 for i in range(8)] + [1]:
                self.drive = b
                yield from self._wait(self.T)
        self.drive = 1

    def _run(self):
        yield
        while True:
            yield from self._fall()
            low = 0
            while self._bus == 0:
                low += 1
                yield
            if low < 11 * self.T:
                continue                            # not a break
            yield from self._fall()
            sync, _ = yield from self._byte()
            if sync != 0x55:
                continue
            yield from self._fall()
            pid, _ = yield from self._byte()
            fid = pid & 0x3F
            ok = pid == pid_of(fid)
            self.headers.append((fid, ok))
            if not ok:
                continue
            if fid in self.publish:
                data = self.publish[fid]
                cks = checksum(fid, data) ^ (0x01 if fid in self.bad else 0)
                yield from self._wait(self.T)       # response space
                yield from self._send(list(data) + [cks])
            elif fid in self.subscribe:
                data = []
                for _ in range(self.subscribe[fid] + 1):
                    yield from self._fall()
                    b, _ = yield from self._byte()
                    data.append(b)
                self.received.append((fid, data[:-1], data[-1] == checksum(fid, data[:-1])))
