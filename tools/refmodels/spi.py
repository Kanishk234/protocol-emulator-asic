"""SPI reference model: a cycle-level SPI target (peripheral) and a waveform decoder.

Written from the SPI mode definitions, independent of any WARP RTL:
- CPOL = idle level of SCK. The *leading* edge leaves the idle level, the *trailing* edge returns to it.
- CPHA = 0: data is sampled on the leading edge and changed on the trailing edge; the first bit
  is on the line as soon as CS goes low.
- CPHA = 1: data is changed on the leading edge and sampled on the trailing edge.
- Bits are MSB first, 8 per byte. CS is active low.

Signals are given as one value per system clock.
"""

from dataclasses import dataclass, field
from typing import Iterator, List, Sequence, Tuple


@dataclass
class Target:
    """An SPI target that answers with `responses` (one byte per 8 SCK cycles, cycling
    through the list) and records every byte it receives, grouped per CS-low transaction."""

    cpol: int
    cpha: int
    responses: Sequence[int] = (0x00,)
    transactions: List[List[int]] = field(default_factory=list)

    def __post_init__(self):
        self._cs_n = 1
        self._sck = self.cpol
        self._resp = self._responses()
        self._miso = 1  # a released line reads high (pull-up)
        self._tx = 0
        self._rx = 0
        self._nbits = 0
        self._sent = 0
        self._fresh = False  # a response byte is loaded but none of its bits was sampled yet

    def _responses(self) -> Iterator[int]:
        while True:
            for r in self.responses:
                yield r & 0xFF

    def _load(self):
        self._tx = next(self._resp)
        self._sent = 0
        self._fresh = True

    def _out_next(self):
        self._miso = (self._tx >> (7 - self._sent)) & 1
        self._sent += 1

    def step(self, cs_n: int, sck: int, mosi: int) -> int:
        """Advance one system clock with the controller's lines; return MISO for this clock."""
        if self._cs_n == 1 and cs_n == 0:  # transaction starts
            self.transactions.append([])
            self._rx = 0
            self._nbits = 0
            if self._fresh:
                self._sent = 0  # reuse a byte that was put on the line but never read (CPHA 0)
            else:
                self._load()
            if self.cpha == 0:
                self._out_next()
        if cs_n == 1:
            self._miso = 1
        elif sck != self._sck:  # also when CS fell in this same clock
            leading = self._sck == self.cpol
            sample = leading if self.cpha == 0 else not leading
            if sample:
                self._fresh = False
                self._rx = ((self._rx << 1) | (mosi & 1)) & 0xFF
                self._nbits += 1
                if self._nbits == 8:
                    self.transactions[-1].append(self._rx)
                    self._nbits = 0
            else:
                # change edge (CPHA 0: trailing, CPHA 1: leading): next bit, or the next
                # response byte's MSB once all 8 bits of the current one are out
                if self._sent == 8:
                    self._load()
                self._out_next()
        self._cs_n = cs_n
        self._sck = sck
        return self._miso


def decode(cs_n: Sequence[int], sck: Sequence[int], mosi: Sequence[int], miso: Sequence[int],
           cpol: int, cpha: int) -> List[List[Tuple[int, int]]]:
    """Decode (mosi_byte, miso_byte) pairs per CS-low transaction, sampling both data lines on
    the mode's sampling edge. Incomplete bytes at the end of a transaction are dropped."""
    out: List[List[Tuple[int, int]]] = []
    prev_cs, prev_sck = 1, cpol
    mo = mi = n = 0
    for c, s, o, i in zip(cs_n, sck, mosi, miso):
        if prev_cs == 1 and c == 0:
            out.append([])
            mo = mi = n = 0
        if c == 0 and s != prev_sck:  # also when CS fell in this same clock
            leading = prev_sck == cpol
            if leading == (cpha == 0):
                mo = ((mo << 1) | o) & 0xFF
                mi = ((mi << 1) | i) & 0xFF
                n += 1
                if n == 8:
                    out[-1].append((mo, mi))
                    mo = mi = n = 0
        prev_cs, prev_sck = c, s
    return out


def idle_ok(cs_n: Sequence[int], sck: Sequence[int], cpol: int) -> bool:
    """SCK sits at its idle level (CPOL) whenever CS is high."""
    return all(s == cpol for c, s in zip(cs_n, sck) if c == 1)
