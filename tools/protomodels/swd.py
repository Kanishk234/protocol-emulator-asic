"""Reference SWD target (an ADIv5 debug port), written from the ARM Debug Interface v5
specification and the CMSIS-DAP bit sequences, not from TRIPWIRE firmware.

Cycle k of SWCLK = low half, rise k, high half, fall k. The target samples SWDIO on rising
edges and changes it just after rising edges; the host samples during the low half (at the
fall before the next rise).
- Request: 8 bits sampled at rises 1..8 (start 1, APnDP, RnW, A[2:3], parity, stop 0, park 1).
- Turnaround: rise 9; the target drives ACK[0..2] after rises 9, 10, 11 (OK = 1,0,0).
- Read OK: data bits 0..31 after rises 12..43, parity after rise 44, released at rise 45.
- Write OK / WAIT / FAULT: released at rise 12; rises 12 and 13 are turnaround; a write's
  33 bits (data + parity) are sampled at rises 14..46.
- AP reads are posted: an AP read returns the previous AP read's value; DP RDBUFF returns the
  latest one.
Clock-level: step(swclk, swdio) -> (value, oe).
"""

OK, WAIT, FAULT = 0b001, 0b010, 0b100
DPIDR = 0x2BA01477


def parity(v):
    return bin(v).count("1") & 1


class SWDTarget:
    def __init__(self, wait_on=(), idcode=DPIDR):
        self.idcode = idcode
        self.wait_on = set(wait_on)         # transaction indices answered with WAIT
        self.dp = {0x4: 0, 0x8: 0}
        self.ap = {}
        self.rdbuff = 0
        self.log = []                       # (apndp, rnw, addr, value or None, ack, parity_ok)
        self.protocol_errors = 0
        self.value, self.oe = 1, 0
        self._prev_clk = 0
        self._state, self._bits, self._n = "idle", [], 0
        self._skip = 0
        self._out = []
        self._req = None
        self._count = 0

    def step(self, swclk, swdio):
        rise = swclk == 1 and self._prev_clk == 0
        self._prev_clk = swclk
        if rise:
            self._on_rise(swdio)
        return self.value, self.oe

    def _drive(self, bit):
        self.value, self.oe = bit, 1

    def _release(self):
        self.value, self.oe = 1, 0

    def _on_rise(self, dio):
        if self._skip:                      # turnaround rises: nobody samples
            self._skip -= 1
            if self._state == "ack":
                self._drive(self._out.pop(0))
                if not self._out:
                    self._state = "ack_done"
            return
        st = self._state
        if st == "idle":
            if dio == 1:                    # start bit
                self._state, self._bits = "req", [1]
        elif st == "req":
            self._bits.append(dio)
            if len(self._bits) == 8:
                self._request(self._bits)
        elif st == "ack":
            self._drive(self._out.pop(0))
            if not self._out:
                self._state = "ack_done"
        elif st == "ack_done":
            self._after_ack()
        elif st == "rdata":
            if self._out:
                self._drive(self._out.pop(0))
            else:                           # rise 45: release (turnaround)
                self._release()
                self._state = "idle"
        elif st == "wdata":
            self._bits.append(dio)
            if len(self._bits) == 33:
                v = sum(b << i for i, b in enumerate(self._bits[:32]))
                ok = parity(v) == self._bits[32]
                apndp, _, addr = self._req
                if ok:
                    self._write(apndp, addr, v)
                self.log.append((apndp, 0, addr, v, OK, ok))
                self._state = "idle"

    def _request(self, b):
        start, apndp, rnw, a2, a3, par, stop, park = b
        if start != 1 or stop != 0 or park != 1 or par != (apndp ^ rnw ^ a2 ^ a3):
            self.protocol_errors += 1       # no response; wait for the next start bit
            self._state = "idle"
            return
        addr = (a3 << 3) | (a2 << 2)
        self._req = (apndp, rnw, addr)
        ack = WAIT if self._count in self.wait_on else OK
        self._count += 1
        self._ack = ack
        self._out = [(ack >> i) & 1 for i in range(3)]
        self._state, self._skip = "ack", 1   # rise 9 (turnaround) drives ACK[0]

    def _after_ack(self):                   # rise 12
        apndp, rnw, addr = self._req
        if self._ack == OK and rnw:
            v = self._read(apndp, addr)
            self.log.append((apndp, 1, addr, v, OK, True))
            bits = [(v >> i) & 1 for i in range(32)] + [parity(v)]
            self._drive(bits.pop(0))
            self._out, self._state = bits, "rdata"
            return
        self._release()
        if self._ack == OK:
            self._state, self._bits, self._skip = "wdata", [], 1     # rise 13 turnaround
        else:
            self.log.append((apndp, rnw, addr, None, self._ack, True))
            self._state, self._skip = "idle", 1

    def _read(self, apndp, addr):
        if apndp:
            v, self.rdbuff = self.rdbuff, self.ap.get((self.dp[0x8] & 0xF0, addr), 0)
            return v
        if addr == 0x0:
            return self.idcode
        if addr == 0xC:
            return self.rdbuff
        return self.dp.get(addr, 0)

    def _write(self, apndp, addr, v):
        if apndp:
            self.ap[(self.dp[0x8] & 0xF0, addr)] = v
        elif addr in (0x4, 0x8):
            self.dp[addr] = v
