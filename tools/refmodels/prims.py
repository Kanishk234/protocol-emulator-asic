"""Reference models of the G1 hard primitives (ARCHITECTURE.md §8, cycle-exact spec v2).

Written from the specification only, not from the RTL (src/.. / arch/.. primitives). Each model
is a clocked object: `outputs(**inputs)` gives the combinational outputs for the current state,
`clock(**inputs)` applies one clock edge. Tests and the RTL's cocotb/formal checks drive both.
"""

from dataclasses import dataclass


@dataclass
class Timer:
    """wp_timer: loadable down-counter. Config RELOAD (16 bit), ONESHOT."""
    reload: int
    oneshot: bool = False
    count: int = 0
    armed: bool = False

    def __post_init__(self):
        if not 0 <= self.reload < 1 << 16:
            raise ValueError("RELOAD is 16 bits")

    def outputs(self, en=0, **_):
        return {"tc": int(bool(en) and self.armed and self.count == 0)}

    def clock(self, rst=0, load=0, half=0, en=0):
        if rst:
            self.count, self.armed = self.reload, True
        elif load:
            self.count, self.armed = (self.reload >> 1) if half else self.reload, True
        elif en and self.armed:
            if self.count == 0:
                self.count = self.reload
                self.armed = not self.oneshot
            else:
                self.count -= 1


@dataclass
class Shift:
    """wp_shift: 8-bit shift register with a step count. Config LEN (1-15), MSB_FIRST."""
    length: int
    msb_first: bool = True
    sr: int = 0
    n: int = 0

    def __post_init__(self):
        if not 1 <= self.length <= 15:
            raise ValueError("LEN is 1..15")

    def outputs(self, **_):
        return {"sout": (self.sr >> 7) & 1 if self.msb_first else self.sr & 1,
                "q": self.sr, "done": int(self.n == self.length)}

    def clock(self, rst=0, load=0, d=0, step=0, sin=0):
        if rst:
            self.sr, self.n = 0, 0
        elif load:
            self.sr, self.n = d & 0xFF, 0
        elif step:
            if self.msb_first:
                self.sr = ((self.sr << 1) | (sin & 1)) & 0xFF
            else:
                self.sr = ((sin & 1) << 7) | (self.sr >> 1)
            if self.n != self.length:
                self.n += 1
