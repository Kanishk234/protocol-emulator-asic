"""Reference CAN 2.0 node (parts A and B: 11- and 29-bit IDs, data and remote frames), written
from the Bosch CAN 2.0 specification, not from TRIPWIRE firmware or the BITSYNC model:
- NRZ, dominant 0 / recessive 1 on a wired-AND bus.
- Standard frame: SOF, ID[10:0], RTR, IDE=0, r0, DLC[3:0], data, CRC-15.
  Extended frame: SOF, ID[28:18], SRR=1, IDE=1, ID[17:0], RTR, r1, r0, DLC, data, CRC-15.
  Remote frames (RTR=1) carry a DLC but no data. Then CRC delimiter, ACK slot, ACK delimiter,
  7-bit EOF. SOF..CRC are bit-stuffed (a complement after 5 equal bits).
- CRC-15: x^15 + x^14 + x^10 + x^8 + x^7 + x^4 + x^3 + 1 over SOF..data (destuffed).
- Bus idle after 11 recessive bits. Bit timing: hard sync on SOF, resync limited to SJW, not while
  this node transmits a dominant bit.
- Arbitration (ID, RTR; for extended frames also SRR, IDE): a transmitter reading dominant where it
  sent recessive becomes a receiver.
- Errors (this node is always error-active): a stuff error, or a transmitter's bit error outside
  arbitration and the ACK slot, starts a 6-bit dominant error flag at the next bit; a missing ACK
  starts it at the ACK delimiter; a receiver's CRC error starts it after the ACK delimiter. After
  an error the node waits for 11 recessive bits; a transmitter retries its frame (up to `retries`).
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


def _bits(value, n):
    return [(value >> (n - 1 - i)) & 1 for i in range(n)]


def frame_fields(can_id, data, ext=False, rtr=False, dlc=None):
    dlc = len(data) if dlc is None else dlc
    if ext:
        bits = [0] + _bits(can_id >> 18, 11) + [1, 1] + _bits(can_id & 0x3FFFF, 18) + [int(rtr), 0, 0]
    else:
        bits = [0] + _bits(can_id, 11) + [int(rtr), 0, 0]
    bits += _bits(dlc, 4)
    if not rtr:
        for byte in data:
            bits += _bits(byte, 8)
    return bits + _bits(crc15(bits), 15)


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


def frame_line_bits(can_id, data, ext=False, rtr=False, dlc=None):
    """Everything this node drives for a frame (the ACK slot recessive)."""
    return stuff(frame_fields(can_id, data, ext, rtr, dlc)) + [1, 1, 1] + [1] * 7


class CANNode:
    def __init__(self, period, sp=0.75, sjw=None, send=(), corrupt_crc=False, retries=8, ack=True):
        self.T = float(period)
        self.sp = sp
        self.sjw = self.T / 8 if sjw is None else sjw
        self.pending = [self._norm(f) for f in send]
        self.corrupt_crc = corrupt_crc          # True: once; an int n: the next n frames
        self.retries = retries
        self.ack = ack                          # False: never ACK (a node that only listens)
        self.received = []                      # dicts: id, data, ext, rtr, dlc, crc_ok
        self.results = []                       # (id, "acked" | "noack" | "lost" | "error")
        self.errors = []                        # (kind, raw bit) of errors this node detected
        self.drive = 1
        self.t = 0
        self.start = 0.0
        self.sampled = True
        self.synced = False
        self.prev = 1
        self.idle = 11
        self.mode = "idle"                      # idle | rx | tx | err
        self._flag_left = 0
        self._flag_wait = None
        self._tries = 0
        self._reset_rx()

    @staticmethod
    def _norm(f):
        if isinstance(f, dict):
            return f
        can_id, data = f
        return {"id": can_id, "data": list(data), "ext": False, "rtr": False, "dlc": None}

    def queue(self, can_id, data=(), ext=False, rtr=False, dlc=None):
        self.pending.append({"id": can_id, "data": list(data), "ext": ext, "rtr": rtr, "dlc": dlc})

    def _reset_rx(self):
        self.raw, self.bits, self.run, self.last = 0, [], 0, None
        self.need = None
        self.after = None
        self.arb_end = 12

    def _begin(self, t):
        self.start, self.sampled, self.synced = float(t), False, False
        self._reset_rx()

    def step(self, bus):
        if self.pending and not isinstance(self.pending[0], dict):
            self.pending = [self._norm(f) for f in self.pending]   # tests may assign (id, data) pairs
        t = self.t
        if t >= self.start + self.T:
            self.start += self.T
            self.sampled, self.synced = False, False
            self._bit_start(t)
        if self.prev == 1 and bus == 0:
            if self.mode == "idle" and self.idle >= 11:
                self.mode = "rx"
                self._begin(t)
            elif self.mode in ("rx", "tx") and not self.synced and not (self.mode == "tx" and self.drive == 0):
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

    # ---------------------------------------------------------------- errors
    def _error(self, kind, wait_bits=0):
        """Start an active error flag after `wait_bits` more bit starts."""
        if self.mode == "err":
            return
        self.errors.append((kind, self.raw))
        if self.mode == "tx":
            self.results.append((self.pending[0]["id"], "error" if kind != "ack" else "noack"))
            self._tries += 1
            if self._tries > self.retries:
                self.pending.pop(0)
                self._tries = 0
        self.mode = "err"
        self._flag_wait = wait_bits
        self.drive = 1

    def _bit_start(self, t):
        if self.mode == "err":
            if self._flag_wait is not None:
                if self._flag_wait == 0:
                    self._flag_wait, self._flag_left = None, 6
                else:
                    self._flag_wait -= 1
            if self._flag_left:
                self.drive = 0
                self._flag_left -= 1
            else:
                self.drive = 1
                if self._flag_wait is None:
                    self.mode, self.idle = "idle", 0     # error delimiter + intermission: 11 recessive
            return
        if self.mode == "idle" and self.pending and self.idle >= 11:
            f = self.pending[0]
            fields = frame_fields(f["id"], f["data"], f["ext"], f["rtr"], f["dlc"])
            if self.corrupt_crc:
                fields[-1] ^= 1
                if self.corrupt_crc is True:
                    self.corrupt_crc = False
                else:
                    self.corrupt_crc -= 1
            self.tx_bits = stuff(fields) + [1, 1, 1] + [1] * 7
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

    # ---------------------------------------------------------------- receive
    def _sample(self, b):
        self.idle = self.idle + 1 if b == 1 else 0
        if self.mode in ("idle", "err"):
            return
        sent = self.drive
        self.raw += 1
        if self.after is None:                          # stuffed part: destuff and parse
            if self.run == 5:
                if b == self.last:
                    self._error("stuff")
                    return
                self.last, self.run = b, 1
                self._check_tx(b, sent)
                return
            self.run = self.run + 1 if b == self.last else 1
            self.last = b
            self.bits.append(b)
            n = len(self.bits)
            if n == 14 and self.bits[13] == 1:
                self.arb_end = 32                       # extended: SRR, IDE, ID[17:0], RTR arbitrate
            if (n == 19 and self.bits[13] == 0) or (n == 39 and self.bits[13] == 1):
                rtr = self.bits[12] if n == 19 else self.bits[32]
                dlc = int("".join(map(str, self.bits[n - 4:n])), 2)
                self.need = n + (0 if rtr else 8 * min(dlc, 8)) + 15
            if self.mode == "tx" and n <= self.arb_end and sent == 1 and b == 0:
                self.mode = "rx"                        # lost arbitration
                self.results.append((self.pending[0]["id"], "lost"))
                self.drive = 1
                return
            if self._check_tx(b, sent):
                return
            if self.need and n == self.need:
                body, crc = self.bits[:-15], self.bits[-15:]
                self.crc_ok = crc15(body) == int("".join(map(str, crc)), 2)
                self.ack_it = self.mode == "rx" and self.crc_ok and self.ack
                self.after = 0
            return
        if self.after == 0 and self.run == 5:           # a stuff bit can follow the CRC sequence
            self.run = 0
            if b == self.last:
                self._error("stuff")
                return
            self._check_tx(b, sent)
            return
        self.after += 1                                 # 1 = CRC delim, 2 = ACK slot, 3 = ACK delim, 4.. EOF
        if self.after == 2 and self.mode == "tx":
            if b == 1:
                self._error("ack")                      # flag from the ACK delimiter
                return
            self.acked = True
            return
        if self.after in (1, 3) or self.after >= 4:
            if b == 0 and not (self.mode == "rx" and self.after == 10):
                self._error("form")
                return
        if self.after == 3 and self.mode == "rx" and not self.crc_ok:
            self._error("crc", wait_bits=0)             # flag right after the ACK delimiter
            return
        if self.after == 10:                            # end of EOF
            self._end()

    def _check_tx(self, b, sent):
        if self.mode == "tx" and b != sent:
            self._error("bit")
            return True
        return False

    def _end(self):
        body = self.bits
        if self.mode == "tx":
            self.results.append((self.pending[0]["id"], "acked"))
            self.pending.pop(0)
            self._tries = 0
        else:
            ext = body[13] == 1
            if ext:
                can_id = int("".join(map(str, body[1:12] + body[14:32])), 2)
                rtr, d0 = body[32], 35
            else:
                can_id = int("".join(map(str, body[1:12])), 2)
                rtr, d0 = body[12], 15
            dlc = int("".join(map(str, body[d0:d0 + 4])), 2)
            n = 0 if rtr else min(dlc, 8)
            data = [int("".join(map(str, body[d0 + 4 + 8 * k:d0 + 12 + 8 * k])), 2) for k in range(n)]
            self.received.append({"id": can_id, "data": data, "ext": ext, "rtr": bool(rtr),
                                  "dlc": dlc, "crc_ok": self.crc_ok})
        self.mode, self.drive, self.acked = "idle", 1, False
        self.ack_it = False
