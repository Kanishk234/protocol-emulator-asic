"""Reference JTAG target: an IEEE 1149.1 TAP controller with a 4-bit IR, written from the
standard, not from TRIPWIRE firmware.

- TMS and TDI are sampled on the rising edge of TCK; TDO changes on the falling edge.
- The 16-state TAP machine; Test-Logic-Reset selects IDCODE.
- Capture-IR loads 0b0001 (the two LSBs must be 01). Capture-DR loads the selected register.
- Shift: LSB first, TDO = bit 0 of the shift register (driven from the falling edge after the
  state is entered).
- Instructions: IDCODE (0b1110, 32 bits), USER (0b1000, 32-bit read/write register),
  BYPASS (0b1111 and any other code, 1 bit).
Clock-level: step(tck, tms, tdi) -> tdo.
"""

IDCODE, USER, BYPASS = 0b1110, 0b1000, 0b1111
NEXT = {  # state: (next if TMS=0, next if TMS=1)
    "TLR": ("RTI", "TLR"), "RTI": ("RTI", "SDS"),
    "SDS": ("CDR", "SIS"), "CDR": ("SDR", "E1D"), "SDR": ("SDR", "E1D"), "E1D": ("PDR", "UDR"),
    "PDR": ("PDR", "E2D"), "E2D": ("SDR", "UDR"), "UDR": ("RTI", "SDS"),
    "SIS": ("CIR", "TLR"), "CIR": ("SIR", "E1I"), "SIR": ("SIR", "E1I"), "E1I": ("PIR", "UIR"),
    "PIR": ("PIR", "E2I"), "E2I": ("SIR", "UIR"), "UIR": ("RTI", "SDS"),
}


class JTAGTarget:
    def __init__(self, idcode=0x4BA00477):
        self.idcode = idcode
        self.state = "TLR"
        self.ir = IDCODE
        self.user = 0
        self.tdo = 1
        self._sr = 0
        self._len = 0
        self._prev = 0
        self.states = []                    # every state entered (for checks)

    def _dr_len(self):
        return {IDCODE: 32, USER: 32}.get(self.ir, 1)

    def step(self, tck, tms, tdi):
        if tck and not self._prev:
            self._rise(tms, tdi)
        elif not tck and self._prev and self.state in ("SDR", "SIR"):
            self.tdo = self._sr & 1         # TDO changes on the falling edge
        self._prev = tck
        return self.tdo

    def _rise(self, tms, tdi):
        st = self.state
        if st in ("SDR", "SIR"):            # shift happens on the rise that leaves or stays
            self._sr = (self._sr >> 1) | (tdi << (self._len - 1))
        nxt = NEXT[st][tms]
        if nxt == "TLR":
            self.ir = IDCODE
        elif nxt == "CIR":
            self._sr, self._len = 0b0001, 4
        elif nxt == "CDR":
            self._len = self._dr_len()
            self._sr = {IDCODE: self.idcode, USER: self.user}.get(self.ir, 0)
        elif nxt == "UIR":
            self.ir = self._sr & 0xF
        elif nxt == "UDR" and self.ir == USER:
            self.user = self._sr
        self.state = nxt
        self.states.append(nxt)
