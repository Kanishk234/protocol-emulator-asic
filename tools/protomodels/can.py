"""Reference CAN 2.0A node (classic CAN, 11-bit IDs), written from the Bosch CAN 2.0 spec,
part A, not from TRIPWIRE firmware or the BITSYNC model:
- NRZ, dominant 0 / recessive 1 on a wired-AND bus.
- Frame: SOF, ID[10:0], RTR, IDE, r0, DLC[3:0], data (min(DLC, 8) bytes), CRC-15
  (x^15 + x^14 + x^10 + x^8 + x^7 + x^4 + x^3 + 1), then CRC delimiter, ACK slot,
  ACK delimiter, 7-bit EOF. SOF..CRC are bit-stuffed (a complement after 5 equal bits).
- Bus idle after 11 recessive bits (ACK delimiter + EOF + 3-bit intermission).
- Bit timing: hard sync on the SOF edge, resync on recessive-to-dominant edges limited to SJW,
  not while this node transmits a dominant bit; sample point at SP of the bit.
- Arbitration: a transmitter that reads dominant where it sent recessive, in the ID or RTR
  bit, becomes a receiver. Receivers with a correct CRC drive the ACK slot dominant.
Clock-level: step(bus) -> drive level (1 = recessive).
"""

CRC15_POLY = 0x4599


def crc15(bits):
    crc = 0
    for b in bits:
        top = (crc >> 14) & 1
        crc = (crc << 1) & 0x7FFF
        if top ^ b:
            crc ^= CRC15_POLY
    return crc


def frame_fields(can_id, data):
    dlc = len(data)
    bits = [0] + [(can_id >> (10 - i)) & 1 for i in range(11)] + [0, 0, 0]
    bits += [(dlc >> (3 - i)) & 1 for i in range(4)]
    for byte in data:
        bits += [(byte >> (7 - i)) & 1 for i in range(8)]
    crc = crc15(bits)
    return bits + [(crc >> (14 - i)) & 1 for i in range(15)]


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


def frame_line_bits(can_id, data):
    """Everything this node drives for a frame (the ACK slot recessive)."""
    return stuff(frame_fields(can_id, data)) + [1, 1, 1] + [1] * 7


class CANNode:
    def __init__(self, period, sp=0.75, sjw=None, send=(), corrupt_crc=False):
        self.T = float(period)
        self.sp = sp
        self.sjw = self.T / 8 if sjw is None else sjw
        self.pending = [(i, list(d)) for i, d in send]
        self.corrupt_crc = corrupt_crc
        self.received = []              # dicts: id, data, crc_ok
        self.results = []               # (id, "acked" | "noack" | "lost" | "error")
        self.drive = 1
        self.t = 0                      # clock count
        self.start = 0.0                # current bit start (clocks)
        self.sampled = True
        self.synced = False
        self.prev = 1
        self.idle = 11                  # recessive bits seen (bus idle at >= 11)
        self.mode = "idle"              # idle | rx | tx
        self._reset_rx()

    def _reset_rx(self):
        self.raw, self.bits, self.run, self.last = 0, [], 0, None
        self.need = None                # destuffed bits up to the end of the CRC field
        self.after = None               # line bits after the CRC field
        self.stuff_err = False

    def _begin(self, t):
        self.start, self.sampled, self.synced = float(t), False, False
        self._reset_rx()

    def step(self, bus):
        t = self.t
        # bit boundary
        if t >= self.start + self.T:
            self.start += self.T
            self.sampled, self.synced = False, False
            self._bit_start(t)
        # edges
        if self.prev == 1 and bus == 0:
            if self.mode == "idle" and self.idle >= 11:
                self.mode = "rx"
                self._begin(t)
            elif self.mode != "idle" and not self.synced and not (self.mode == "tx" and self.drive == 0):
                e = t - self.start
                if e < self.sp * self.T:
                    self.start += min(e, self.sjw)
                else:
                    self.start -= min(self.start + self.T - t, self.sjw)
                self.synced = True
        self.prev = bus
        if not self.sampled and t >= self.start + self.sp * self.T:
            self.sampled = True
            self._sample(bus)
        self.t += 1
        return self.drive

    def _bit_start(self, t):
        if self.mode == "idle" and self.pending and self.idle >= 11:
            can_id, data = self.pending[0]
            self.tx_bits = frame_line_bits(can_id, data)
            if self.corrupt_crc:
                self._corrupt()
            self.tx_i = 0
            self.mode = "tx"
            self._begin(t)
        if self.mode == "tx":
            self.drive = self.tx_bits[self.tx_i] if self.tx_i < len(self.tx_bits) else 1
            self.tx_i += 1
        elif self.mode == "rx" and self.after == 1 and self.ack_it:
            self.drive = 0                              # ACK slot
        else:
            self.drive = 1

    def _corrupt(self):
        fields = frame_fields(*self.pending[0])
        fields[-1] ^= 1
        self.tx_bits = stuff(fields) + [1, 1, 1] + [1] * 7

    def _sample(self, b):
        self.idle = self.idle + 1 if b == 1 else 0
        if self.mode == "idle":
            return
        sent = self.drive
        self.raw += 1
        if self.after is None:                          # stuffed part: destuff and parse
            if self.run == 5:
                if b == self.last:
                    self.stuff_err = True
                    self._end("error")
                    return
                self.last, self.run = b, 1
                self._check_tx(b, sent)
                return
            self.run = self.run + 1 if b == self.last else 1
            self.last = b
            self.bits.append(b)
            n = len(self.bits)
            if n == 19:
                dlc = int("".join(map(str, self.bits[15:19])), 2)
                self.need = 19 + 8 * min(dlc, 8) + 15
            if self.mode == "tx" and n <= 12 and sent == 1 and b == 0:
                self.mode = "rx"                        # lost arbitration
                self.results.append((self.pending[0][0], "lost"))
                self.drive = 1
                return
            self._check_tx(b, sent)
            if self.need and n == self.need:
                body, crc = self.bits[:-15], self.bits[-15:]
                self.crc_ok = crc15(body) == int("".join(map(str, crc)), 2)
                self.ack_it = self.mode == "rx" and self.crc_ok
                self.after = 0
            return
        if self.after == 0 and self.run == 5:           # a stuff bit can follow the CRC sequence
            self.run = 0
            self._check_tx(b, sent)
            return
        self.after += 1                                 # 1 = CRC delim, 2 = ACK slot, ...
        if self.after == 2 and self.mode == "tx":
            self.acked = b == 0
        if self.after == 10:                            # end of EOF
            self._end()

    def _check_tx(self, b, sent):
        if self.mode == "tx" and b != sent:
            self._end("error")

    def _end(self, why=None):
        body = self.bits
        if self.mode == "tx":
            res = why or ("acked" if getattr(self, "acked", False) else "noack")
            self.results.append((self.pending[0][0], res))
            if res == "acked":
                self.pending.pop(0)
        elif why is None:
            dlc = int("".join(map(str, body[15:19])), 2)
            data = [int("".join(map(str, body[19 + 8 * k:27 + 8 * k])), 2) for k in range(min(dlc, 8))]
            self.received.append({"id": int("".join(map(str, body[1:12])), 2), "data": data,
                                  "crc_ok": self.crc_ok})
        self.mode, self.drive, self.acked = "idle", 1, False
        self.ack_it = False
