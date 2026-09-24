"""Reference USB low-speed host (USB 2.0 chapters 7-8, 9.4), written from the specification, not
from TRIPWIRE firmware or its BITSYNC model. Feasibility testing only.

- Low speed: 1.5 Mbit/s; J = D- high / D+ low (idle, the device's pull-up on D-), K = the opposite,
  SE0 = both low. NRZI: a 0 is a change of state, a 1 is none; a 0 is stuffed after six 1s.
- A packet: SYNC (0x80, sent LSB first as 00000001), PID (4 bits + their complement), then for
  tokens 7-bit address + 4-bit endpoint + CRC-5, for data packets the data + CRC-16; then EOP =
  SE0 for 2 bits, J for 1 bit. CRC-5: x^5 + x^2 + 1, CRC-16: x^16 + x^15 + x^2 + 1, both reflected,
  initial all ones, sent complemented, LSB first.
- Control transfers: SETUP + DATA0(8) -> ACK; data stage IN -> DATAx -> ACK; status stage.
Clock-level: step(dp, dm) -> (dp, dm, oe) the host drives; `delays` records the device's
turnaround after each of our EOPs (in bit times).
"""

SETUP, OUT, IN, DATA0, DATA1, ACK, NAK = 0x2D, 0xE1, 0x69, 0xC3, 0x4B, 0xD2, 0x5A


def crc5(addr, endp):
    c = 0x1F
    v = addr | endp << 7
    for i in range(11):
        c = (c >> 1) ^ 0x14 if (c ^ (v >> i)) & 1 else c >> 1
    return c ^ 0x1F


def crc16(data):
    c = 0xFFFF
    for byte in data:
        for i in range(8):
            c = (c >> 1) ^ 0xA001 if (c ^ (byte >> i)) & 1 else c >> 1
    return c ^ 0xFFFF


def token(pid, addr, endp, bad_crc=False):
    v = addr | endp << 7 | (crc5(addr, endp) ^ (1 if bad_crc else 0)) << 11
    return [0x80, pid, v & 0xFF, v >> 8]


def data_packet(pid, payload, bad_crc=False):
    c = crc16(payload) ^ (0x0100 if bad_crc else 0)
    return [0x80, pid] + list(payload) + [c & 0xFF, c >> 8]


J, K, SE0 = (0, 1), (1, 0), (0, 0)      # (dp, dm)


def line_states(packet):
    bits, run = [], 0
    for byte in packet:
        for i in range(8):
            b = (byte >> i) & 1
            bits.append(b)
            run = run + 1 if b else 0
            if run == 6:
                bits.append(0)
                run = 0
    level, out = J, []
    for b in bits:
        if b == 0:
            level = K if level == J else J
        out.append(level)
    return out + [SE0, SE0, J]


class USBLSHost:
    def __init__(self, bit_clocks=50e6 / 1.5e6):
        self.T = bit_clocks
        self.drive, self.oe = J, 0
        self.log = []                       # (what, detail)
        self.delays = []
        self.bus = J
        self._t = 0
        self._ops = []
        self._gen = self._run()
        next(self._gen)

    def step(self, dp, dm):
        self.bus = (dp, dm)
        self._t += 1
        next(self._gen)
        return self.drive[0], self.drive[1], self.oe

    # -------------------------------------------------------------- primitives
    def _wait(self, clocks):
        for _ in range(int(round(clocks))):
            yield

    def _send(self, packet):
        t = 0.0
        self.oe = 1
        for state in line_states(packet):
            self.drive = state
            n = round(t + self.T) - round(t)
            t += self.T
            yield from self._wait(n)
        self.oe, self.drive = 0, J
        self._eop_end = self._t

    def _recv(self, timeout_bits=18):
        """A device packet: list of bytes (SYNC included), or None on timeout / error."""
        waited = 0
        while self.bus == J or self.bus == (1, 1):
            yield
            waited += 1
            if waited > timeout_bits * self.T:
                return None
        self.delays.append((self._t - self._eop_end) / self.T)
        edge, prev_state, bits, run = self._t, J, [], 0
        next_sample = edge + self.T / 2
        last = self.bus
        while True:
            yield
            if self.bus != last and self.bus != SE0:
                next_sample = self._t + self.T / 2          # re-anchor on every transition
                last = self.bus
            if self._t >= next_sample:
                next_sample += self.T
                s = self.bus
                if s == SE0:
                    break
                b = 1 if s == prev_state else 0
                prev_state = s
                if run == 6:                                 # a stuffed 0
                    run = 0
                    if b != 0:
                        return None
                    continue
                run = run + 1 if b else 0
                bits.append(b)
        yield from self._wait(3 * self.T)                    # rest of the EOP
        data = [sum(bits[8 * k + i] << i for i in range(8)) for k in range(len(bits) // 8)]
        if not data or data[0] != 0x80 or len(data) < 2 or (data[1] ^ (data[1] >> 4)) & 15 != 15:
            return None
        return data

    def _gap(self):
        yield from self._wait(3 * self.T)

    # -------------------------------------------------------------- transfers
    def _control_in(self, addr, setup, max_len, corrupt_setup_once=False):
        """A control read (or no-data request if max_len == 0): returns the data, or None."""
        for attempt in range(3):
            yield from self._send(token(SETUP, addr, 0))
            yield from self._gap()
            bad = corrupt_setup_once and attempt == 0
            yield from self._send(data_packet(DATA0, setup, bad_crc=bad))
            hs = yield from self._recv()
            self.log.append(("setup", None if hs is None else hs[1]))
            if hs is not None and hs[1] == ACK:
                break
            yield from self._gap()
        else:
            return None
        got, toggle = [], 1
        while True:
            yield from self._gap()
            yield from self._send(token(IN, addr, 0))
            pkt = yield from self._recv()
            if pkt is None:
                self.log.append(("in", None))
                return None
            pid = pkt[1]
            if pid == NAK:
                self.log.append(("in", "NAK"))
                continue
            payload, crc = pkt[2:-2], pkt[-2] | pkt[-1] << 8
            ok = crc16(payload) == crc and pid == (DATA1 if toggle else DATA0)
            self.log.append(("in", pid, len(payload), ok))
            if not ok:
                return None
            yield from self._gap()
            yield from self._send([0x80, ACK])
            got += payload
            toggle ^= 1
            if len(payload) < 8 or len(got) >= max_len:
                break
        if max_len:                                          # status stage: OUT + DATA1(0)
            yield from self._gap()
            yield from self._send(token(OUT, addr, 0))
            yield from self._gap()
            yield from self._send(data_packet(DATA1, []))
            hs = yield from self._recv()
            self.log.append(("status", None if hs is None else hs[1]))
            if hs is None or hs[1] != ACK:
                return None
        return got

    def get_descriptor(self, addr, length=64, corrupt_setup_once=False):
        self._ops.append(("get", addr, length, corrupt_setup_once))

    def set_address(self, addr, new):
        self._ops.append(("set", addr, new))

    def bad_token(self, addr):
        self._ops.append(("badtok", addr))

    def _run(self):
        yield
        self.results = []
        while True:
            if not self._ops:
                yield
                continue
            op = self._ops.pop(0)
            yield from self._wait(10 * self.T)
            if op[0] == "get":
                setup = [0x80, 0x06, 0x00, 0x01, 0x00, 0x00, op[2] & 0xFF, op[2] >> 8]
                r = yield from self._control_in(op[1], setup, op[2], op[3])
                self.results.append(("get", op[1], r))
            elif op[0] == "set":
                setup = [0x00, 0x05, op[2], 0x00, 0x00, 0x00, 0x00, 0x00]
                r = yield from self._control_in(op[1], setup, 0)       # status: IN -> DATA1(0)
                self.results.append(("set", op[1], r))
            elif op[0] == "badtok":
                yield from self._send(token(IN, op[1], 0, bad_crc=True))
                pkt = yield from self._recv()
                self.results.append(("badtok", op[1], pkt))
