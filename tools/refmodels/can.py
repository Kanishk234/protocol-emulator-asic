"""CAN 2.0A node: independent reference model (held-out protocol H4, phase 4).

Written from the Bosch CAN Specification 2.0 (part A, base frame format), not from any WARP
design. Stepped once per system clock with the bus level; returns the node's drive
(0 = dominant, 1 = recessive); the bus is the wired-AND of all drives.

  - Data frame: SOF (dominant), 11-bit identifier (MSB first), RTR (dominant for data), IDE
    (dominant), r0 (dominant), DLC (4 bits), 0-8 data bytes (MSB first), CRC-15 (polynomial
    0x4599 over SOF..data, MSB first), CRC delimiter (recessive), ACK slot (the transmitter
    sends recessive, every receiver that received the frame correctly overwrites it with
    dominant), ACK delimiter, 7 recessive EOF bits, then 3 bits of intermission.
  - Bit stuffing from SOF through the CRC: after 5 consecutive equal bits the transmitter
    inserts one bit of the opposite level; receivers remove it (a 6th equal bit is a stuff
    error).
  - Arbitration: a node that sends recessive in the identifier (or RTR) and reads dominant
    stops transmitting and receives the frame.
  - Bit timing: `bit_clocks` system clocks per bit; a node synchronizes hard on the recessive to
    dominant edge that starts a frame and samples each bit at `sample` of the bit time (this
    model does not resynchronize within a frame; nodes in the tests share one clock).

`send(ident, data)` queues a frame; `received` lists (ident, data) of frames received without
error; `sent` lists frames transmitted and acknowledged; `lost` counts arbitration losses;
`errors` lists detected errors (stuff, CRC, form, bit, no ACK).
"""


def crc15(bits):
    crc = 0
    for b in bits:
        nxt = b ^ ((crc >> 14) & 1)
        crc = (crc << 1) & 0x7FFF
        if nxt:
            crc ^= 0x4599
    return crc


def frame_bits(ident, data):
    """SOF through the CRC, before stuffing."""
    bits = [0]
    bits += [(ident >> (10 - i)) & 1 for i in range(11)]
    bits += [0, 0, 0]                                 # RTR, IDE, r0
    bits += [(len(data) >> (3 - i)) & 1 for i in range(4)]
    for b in data:
        bits += [(b >> (7 - i)) & 1 for i in range(8)]
    c = crc15(bits)
    return bits + [(c >> (14 - i)) & 1 for i in range(15)]


def stuff(bits):
    out, run, last = [], 0, None
    for b in bits:
        out.append(b)
        run = run + 1 if b == last else 1
        last = b
        if run == 5:
            out.append(1 - b)
            last, run = 1 - b, 1
    return out


class Node:
    def __init__(self, bit_clocks, sample=0.75):
        self.n = bit_clocks
        self.sp = max(1, int(bit_clocks * sample))
        self.queue, self.received, self.sent, self.errors = [], [], [], []
        self.lost = 0
        self._idle_bits = 11                          # bus integration: start idle
        self.phase = None                             # None (idle) or clock within the bit
        self.prev = 1
        self.drive = 1
        self._reset_frame()

    def send(self, ident, data=b""):
        self.queue.append((ident, list(data)))

    def _reset_frame(self):
        self.tx = None                                # stuffed bits being sent (transmitter)
        self.txi = 0
        self.transmitting = False
        self.rx = []                                  # destuffed bits SOF..CRC
        self.run, self.last = 0, None
        self.stage = "idle"                           # frame, crcdel, ack, ackdel, eof
        self.count = 0
        self.frame_ok = False

    def step(self, bus):
        # hard synchronization at a frame start (recessive -> dominant while idle)
        if self.stage == "idle" and self.phase is None:
            if self.prev == 1 and bus == 0 and self._idle_bits >= 11:
                self._start_rx_or_tx(synced=True)
            elif self.queue and self._idle_bits >= 11 and bus == 1:
                self._start_rx_or_tx(synced=False)    # start our own SOF now
        self.prev = bus
        if self.phase is None:
            if bus == 1:
                self._idle_clk = getattr(self, "_idle_clk", 0) + 1
                if self._idle_clk >= self.n:
                    self._idle_clk = 0
                    self._idle_bits += 1
            else:
                self._idle_clk = 0
                self._idle_bits = 0
            return self.drive
        self.phase += 1
        if self.phase == self.sp:
            self._sample(bus)
            if self.phase is None:                    # the frame ended at this sample
                return self.drive
        if self.phase >= self.n:
            self.phase = 0
            self._next_bit()
        return self.drive

    def _start_rx_or_tx(self, synced):
        self.phase = 0
        self._idle_bits = 0
        self.stage = "frame"
        if self.queue:
            ident, data = self.queue[0]
            self.tx = stuff(frame_bits(ident, data))
            self.txi = 0
            self.transmitting = True
            self.drive = self.tx[0]
        else:
            self.drive = 1

    def _next_bit(self):
        """At a bit boundary: put the next bit on the bus."""
        if self.stage in ("frame", "stuffend") and self.transmitting:
            self.txi += 1
            self.drive = self.tx[self.txi] if self.txi < len(self.tx) else 1
        elif self.stage == "ack" and not self.transmitting and self.frame_ok:
            self.drive = 0                            # acknowledge
        else:
            self.drive = 1

    def _sample(self, bus):
        st = self.stage
        if st == "frame":
            if self.transmitting and bus != self.drive:
                nbits = len(self.rx) + (0 if self.run < 5 else 0)
                if self.drive == 1 and 1 <= len(self.rx) <= 12:  # identifier or RTR
                    self.transmitting = False
                    self.drive = 1
                    self.lost += 1
                else:
                    self.errors.append("bit error")
                    return self._abort()
            # destuff
            if self.run == 5:
                if bus == self.last:
                    self.errors.append("stuff error")
                    return self._abort()
                self.last, self.run = bus, 1
                return
            self.run = self.run + 1 if bus == self.last else 1
            self.last = bus
            self.rx.append(bus)
            if len(self.rx) == 19:
                self.dlc = min(8, int("".join(map(str, self.rx[15:19])), 2))
            if len(self.rx) >= 19 and len(self.rx) == 19 + 8 * self.dlc + 15:
                self.frame_ok = crc15(self.rx) == 0
                if not self.frame_ok:
                    self.errors.append("crc error")
                # a stuff bit follows the CRC if it ended with 5 equal bits
                self.stage = "stuffend" if self.run == 5 else "crcdel"
        elif st == "stuffend":
            if bus == self.last:
                self.errors.append("stuff error")
                return self._abort()
            self.stage = "crcdel"
        elif st == "crcdel":
            if bus != 1:
                self.errors.append("form error (CRC delimiter)")
            self.stage = "ack"
        elif st == "ack":
            if self.transmitting:
                if bus == 0:
                    self.sent.append(self.queue.pop(0))
                else:
                    self.errors.append("no ACK")
            self.stage = "ackdel"
        elif st == "ackdel":
            if bus != 1:
                self.errors.append("form error (ACK delimiter)")
            if not self.transmitting and self.frame_ok:
                ident = int("".join(map(str, self.rx[1:12])), 2)
                data = [int("".join(map(str, self.rx[19 + 8 * i:27 + 8 * i])), 2) for i in range(self.dlc)]
                self.received.append((ident, data))
            self.stage = "eof"
            self.count = 0
        elif st == "eof":
            self.count += 1
            if self.count == 7 + 3:                   # EOF + intermission
                self._end()

    def _abort(self):
        self._end()

    def _end(self):
        self.phase = None
        self.drive = 1
        self._idle_bits = 11
        self._reset_frame()
