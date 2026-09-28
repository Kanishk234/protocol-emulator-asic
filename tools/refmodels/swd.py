"""SWD target (Arm Serial Wire Debug, DP + one AP): independent reference model (held-out H3).

Written from the Arm Debug Interface Architecture Specification ADIv5 (IHI 0031), not from any
WARP design. Stepped once per system clock with the host's SWCLK and SWDIO drive; returns the
target's SWDIO drive (None = not driving). The line is push-pull with turnaround periods, idling
high through a pull-up when nobody drives.

  - The target samples SWDIO on rising SWCLK edges and changes its own output just after a
    rising edge (valid for the host to sample before the next rising edge).
  - Line reset: >= 50 clocks with SWDIO high. The JTAG-to-SWD sequence is a line reset, the
    16 bits 0xE79E (LSB first), another line reset; then idle (low) cycles.
  - A packet: 8 request bits (start 1, APnDP, RnW, A[2], A[3], even parity of those four,
    stop 0, park 1), one turnaround cycle, ACK (3 bits LSB first: OK 001, WAIT 010, FAULT 100)
    driven by the target; then for an OK read: 32 data bits + even parity from the target and a
    turnaround; for an OK write: a turnaround, then 32 data bits + parity from the host. WAIT and
    FAULT: a turnaround and no data phase. A request with bad parity, stop or park gets no
    response (the target does not drive).
  - DP registers: 0x0 read DPIDR, write ABORT (clears the sticky FAULT); 0x4 CTRL/STAT;
    0x8 SELECT (write: APSEL[31:24], APBANKSEL[7:4]); 0xC RDBUFF (read: the last AP read).
  - AP reads are posted: an AP read returns the previous AP read's value and captures the new
    one for the next AP read or RDBUFF.

`wait_next` makes the next that many AP accesses answer WAIT; `fault_next` makes the next AP
access answer FAULT and sets the sticky fault (every AP access answers FAULT until ABORT).
`log` records ("line_reset",), ("swd_mode",), and (kind, addr, value) for each OK access;
`errors` records protocol violations seen (e.g. a data parity error, a bus conflict).
"""

JTAG_TO_SWD = 0xE79E
OK, WAIT, FAULT = 0b001, 0b010, 0b100


def parity(v):
    p = 0
    while v:
        p ^= v & 1
        v >>= 1
    return p


class Target:
    def __init__(self, dpidr=0x2BA01477, ap_regs=None):
        self.dpidr = dpidr
        self.ctrl = 0
        self.select = 0
        self.rdbuff = 0
        self.ap = dict(ap_regs or {})
        self.sticky_fault = False
        self.wait_next = 0
        self.fault_next = 0
        self.log, self.errors = [], []
        self.prev_clk = 0
        self.drive = None
        self.ones = 0
        self.mode = "jtag"            # jtag (after power-up), swd
        self.shift = 0                # recent bits (for 0xE79E)
        self.nbits = 0
        self.phase = "idle"           # idle, req, turn1, ack, rdata, turn2, turn3, wdata
        self.req = []
        self.bits = []
        self.out = []                 # bits the target sends, one per rising edge
        self.after = None

    # ---- helpers
    def _apaddr(self, a):
        return ((self.select >> 24) & 0xFF, ((self.select >> 4) & 0xF) << 4 | a)

    def _start(self, bits):
        apndp, rnw, a2, a3, par, stop, park = bits[1:8]
        if par != (apndp ^ rnw ^ a2 ^ a3) or stop != 0 or park != 1:
            if bits != [1] * 8:                    # all ones: part of a line reset, not an error
                self.errors.append("bad request %r" % (bits,))
            self.phase = "idle"
            return
        a = (a3 << 3) | (a2 << 2)
        if apndp and self.sticky_fault:
            ack = FAULT
        elif apndp and self.fault_next:
            self.fault_next -= 1
            self.sticky_fault = True
            ack = FAULT
        elif apndp and self.wait_next:
            self.wait_next -= 1
            ack = WAIT
        else:
            ack = OK
        self.cur = (apndp, rnw, a, ack)
        self.phase = "turn1"

    def _read_value(self, apndp, a):
        if not apndp:
            v = {0x0: self.dpidr, 0x4: self.ctrl, 0x8: self.select, 0xC: self.rdbuff}[a]
            self.log.append(("dp_read", a, v))
            return v
        posted = self.rdbuff
        self.rdbuff = self.ap.get(self._apaddr(a), 0)
        self.log.append(("ap_read", self._apaddr(a), self.rdbuff))
        return posted

    def _write_value(self, apndp, a, v):
        if not apndp:
            if a == 0x0:
                self.sticky_fault = False      # ABORT
            elif a == 0x4:
                self.ctrl = v
            elif a == 0x8:
                self.select = v
            self.log.append(("dp_write", a, v))
        else:
            self.ap[self._apaddr(a)] = v
            self.log.append(("ap_write", self._apaddr(a), v))

    # ---- one system clock
    def step(self, swclk, host_drive):
        """host_drive: the host's SWDIO drive (None = released). Returns the target's drive."""
        line = host_drive if host_drive is not None else (self.drive if self.drive is not None else 1)
        if host_drive is not None and self.drive is not None:
            self.errors.append("bus conflict")
        rising = swclk and not self.prev_clk
        self.prev_clk = swclk
        if rising:
            self._rise(line)
        return self.drive

    def _rise(self, bit):
        # line reset / mode switch, watched on every rising edge the host drives
        self.ones = self.ones + 1 if bit else 0
        self.shift = ((self.shift >> 1) | (bit << 15)) & 0xFFFF
        if self.ones >= 50 and self.phase in ("idle", "req"):
            if self.ones == 50:
                self.log.append(("line_reset",))
            self.phase = "idle"
            self.drive = None
            return
        if self.mode == "jtag":
            if self.shift == JTAG_TO_SWD:
                self.mode = "swd"
                self.log.append(("swd_mode",))
            return
        ph = self.phase
        if ph == "idle":
            if bit == 1:
                self.req = [1]
                self.phase = "req"
        elif ph == "req":
            self.req.append(bit)
            if len(self.req) == 8:
                self._start(self.req)
        elif ph == "turn1":                        # turnaround: the target drives ACK next
            apndp, rnw, a, ack = self.cur
            self.out = [(ack >> i) & 1 for i in range(3)]
            if ack == OK and rnw:
                v = self._read_value(apndp, a)
                self.out += [(v >> i) & 1 for i in range(32)] + [parity(v)]
            self.drive = self.out.pop(0)
            self.phase = "send"
        elif ph == "send":
            if self.out:
                self.drive = self.out.pop(0)
            else:
                self.drive = None                  # turnaround back to the host
                apndp, rnw, a, ack = self.cur
                if ack == OK and not rnw:
                    self.phase = "wdata"           # its first cycle is the turnaround
                    self.bits = []
                else:
                    self.phase = "trn"             # this turnaround cycle carries no bit
        elif ph == "trn":
            self.phase = "idle"
        elif ph == "wdata":
            self.bits.append(bit)
            if len(self.bits) == 1:
                self.bits = []                     # the host's turnaround cycle
                self.phase = "wdata2"
        elif ph == "wdata2":
            self.bits.append(bit)
            if len(self.bits) == 33:
                v = sum(b << i for i, b in enumerate(self.bits[:32]))
                if self.bits[32] != parity(v):
                    self.errors.append("write data parity")
                else:
                    apndp, rnw, a, ack = self.cur
                    self._write_value(apndp, a, v)
                self.phase = "idle"
