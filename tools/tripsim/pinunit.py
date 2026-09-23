"""Pin units U0..U5 (ARCHITECTURE.md §7): a TX half (consumer) and an RX half (producer).

Implemented so far: TX LEVEL/OE/GAP/SYNC/SETN commands and SHIFT for DATA tokens;
RX SHIFT_RX and EDGE_TS. LINKED_RX, COND_EDGE, CLKGEN and PULSE raise
NotImplementedError until they are modelled (needed for I2C, SPI and WS2812 kernels).

Time: "edge t" is the clock edge at the end of clock t; a pad output changed at edge t
is visible from clock t+1. The TX cursor is kept in 1/256-clock units so fractional
bit periods never drift (§7.3).
"""

from dataclasses import dataclass
from typing import Optional

from . import isa

CMD_LEVEL, CMD_OE, CMD_CLK, CMD_GAP, CMD_SYNC, CMD_SETN = 1, 2, 3, 4, 5, 6


@dataclass
class PinConfig:
    pin_a: Optional[int] = None     # pad index (chip.PAD_*), drive and/or sample
    pin_b: Optional[int] = None     # link / condition input
    txmode: str = "level"           # level | shift | clkgen | pulse
    rxmode: str = "off"             # off | shift_rx | linked_rx | edge_ts | cond_edge
    period: float = 1.0             # bit period in clocks (16.8 fixed point in hardware)
    presc: int = 1                  # clocks per tick for LEVEL/OE/GAP delays (1..256)
    nbits: int = 8                  # TX shift length (SETN changes it)
    rx_nbits: Optional[int] = None  # RX shift length; None = same as nbits (ISA.md §9 question)
    order: str = "lsb"              # lsb | msb
    od: bool = False                # open drain: 1 releases (OE=0), 0 drives low
    idle: int = 1
    sampleofs: float = 0.5          # SHIFT_RX: first sample, fraction of a period after the start edge
    autorearm: bool = True

    @property
    def period_q8(self):
        q = round(self.period * 256)
        if not 256 <= q < (1 << 24):
            raise ValueError("period must be in [1, 65536) clocks")
        return q


class PinUnit:
    def __init__(self, idx, tx_port, rx_prod):
        self.idx = idx
        self.tx_port = tx_port
        self.rx_prod = rx_prod
        self.cfg = PinConfig()
        self.reset_state()
        self.flags = {"LATE": 0, "OVERRUN": 0}
        self.stats = {"tx_tokens": 0, "rx_tokens": 0, "overruns": 0, "bad_tokens": 0}

    def configure(self, **kw):
        self.cfg = PinConfig(**kw)
        for mode in ("clkgen", "pulse"):
            if self.cfg.txmode == mode:
                raise NotImplementedError(f"TX mode {mode} not modelled yet")
        if self.cfg.rxmode in ("linked_rx", "cond_edge"):
            raise NotImplementedError(f"RX mode {self.cfg.rxmode} not modelled yet")
        self.reset_state()

    def reset_state(self):
        c = getattr(self, "cfg", PinConfig())
        self.level = c.idle             # TX output register
        self.oe = 1
        self.cursor_q8 = 0
        self.tx_nbits = c.nbits
        self.actions = []               # pending (edge, kind, value), sorted by edge
        self._tx_apply = []
        self._rx = "wait_idle"
        self._rx_t0_q8 = 0
        self._rx_bits = []
        self._rx_prev = None
        self._rx_load = None

    # -------------------------------------------------------------- pads
    def pad_drive(self):
        """(value, oe) this unit drives on pin A, from the registered output."""
        if self.cfg.od:
            return 0, int(self.level == 0)
        return self.level, self.oe

    # ---------------------------------------------------------------- TX
    def _tx_ready(self, now):
        return all(t <= now + 1 for t, _, _ in self.actions)

    def compute_tx(self, now):
        apply = self._tx_apply = []
        port = self.tx_port
        if port is not None and port.avail() and self._tx_ready(now):
            tag, data = port.head()
            port.take()
            self.stats["tx_tokens"] += 1
            self._accept(now, tag, data)
        due = [a for a in self.actions if a[0] <= now]
        self.actions = [a for a in self.actions if a[0] > now]
        apply.extend(due)

    def _accept(self, now, tag, data):
        c = self.cfg
        earliest_q8 = (now + 1) << 8          # accept at clock n, earliest pad edge n+1 (§5.5)
        if tag == isa.TAG_CTRL:
            op, arg = data >> 12, data & 0x0FFF
            if op in (CMD_LEVEL, CMD_OE):
                delay = arg & 0x7FF
                t_q8 = self.cursor_q8 + delay * c.presc * 256
                if t_q8 < earliest_q8:
                    if delay:
                        self.flags["LATE"] = 1
                    t_q8 = earliest_q8
                self.cursor_q8 = t_q8
                kind = "level" if op == CMD_LEVEL else "oe"
                self._schedule(t_q8 >> 8, kind, (arg >> 11) & 1)
            elif op == CMD_GAP:
                self.cursor_q8 += arg * c.presc * 256
            elif op == CMD_SYNC:
                self.cursor_q8 = earliest_q8
            elif op == CMD_SETN:
                n = arg & 0x1F
                self.tx_nbits = n if 1 <= n <= 16 else 16
            elif op == CMD_CLK:
                raise NotImplementedError("CLK command (CLKGEN) not modelled yet")
            else:
                self.stats["bad_tokens"] += 1
        elif tag == isa.TAG_DATA:
            start_q8 = max(self.cursor_q8, earliest_q8)
            if c.txmode == "level":
                self.cursor_q8 = start_q8
                self._schedule(start_q8 >> 8, "level", data & 1)
            else:  # shift
                n, p = self.tx_nbits, c.period_q8
                for i in range(n):
                    bit = (data >> i) & 1 if c.order == "lsb" else (data >> (n - 1 - i)) & 1
                    self._schedule((start_q8 + i * p) >> 8, "level", bit)
                end_q8 = start_q8 + n * p
                self._schedule(end_q8 >> 8, "level", c.idle)
                self.cursor_q8 = end_q8
        else:
            self.stats["bad_tokens"] += 1

    def _schedule(self, edge, kind, value):
        self.actions.append((edge, kind, value))
        self.actions.sort(key=lambda a: a[0])   # stable: same-edge actions keep command order

    # ---------------------------------------------------------------- RX
    def compute_rx(self, now, sample):
        """sample: synchronised level of pin A this clock (or None if not attached)."""
        c = self.cfg
        self._rx_load = None
        if c.rxmode == "off" or sample is None:
            self._rx_prev = sample
            return
        if c.rxmode == "edge_ts":
            if self._rx_prev is not None and sample != self._rx_prev:
                self._emit(isa.TAG_EVENT, (sample << 15) | (now & 0x7FFF))
        elif c.rxmode == "shift_rx":
            n = c.rx_nbits or c.nbits
            if self._rx == "wait_idle":
                if sample == c.idle:
                    self._rx = "armed"
            elif self._rx == "armed":
                if sample != c.idle:           # start edge detected this clock
                    self._rx = "shift"
                    self._rx_t0_q8 = (now << 8) + round(c.sampleofs * c.period_q8)
                    self._rx_bits = []
            if self._rx == "shift":
                i = len(self._rx_bits)
                if now == (self._rx_t0_q8 + i * c.period_q8) >> 8:
                    self._rx_bits.append(sample)
                    if len(self._rx_bits) == n:
                        bits = self._rx_bits if c.order == "lsb" else self._rx_bits[::-1]
                        self._emit(isa.TAG_DATA, sum(b << k for k, b in enumerate(bits)))
                        self._rx = "wait_idle" if c.autorearm else "off"
        self._rx_prev = sample

    def _emit(self, tag, data):
        if self.rx_prod.free():
            self.rx_prod.load(tag, data)
            self.stats["rx_tokens"] += 1
        else:                                   # §4.5: pins never wait; keep the old token
            self.flags["OVERRUN"] = 1
            self.stats["overruns"] += 1

    # -------------------------------------------------------------- commit
    def commit(self):
        for _, kind, value in self._tx_apply:
            if kind == "level":
                self.level = value
            else:
                self.oe = value
        self._tx_apply = []
