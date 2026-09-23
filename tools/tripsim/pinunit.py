"""Pin units U0..U5 (ARCHITECTURE.md §7): a TX half (consumer) and an RX half (producer).

Modelled:
- TX: LEVEL/OE/GAP/SYNC/SETN commands; DATA tokens shifted at PERIOD (timed) or on
  edges of pin B (linked, tx_edge).
- RX: SHIFT_RX, EDGE_TS, LINKED_RX (sample A on rx_edge of B, optional tail bit), and
  COND_EDGE (START/STOP: A changes while B is high), combinable with LINKED_RX.
Not yet: CLKGEN, PULSE (raise NotImplementedError).

Time: "edge t" is the clock edge at the end of clock t; a pad output changed at edge t
is visible from clock t+1. The TX cursor is kept in 1/256-clock units so fractional
bit periods never drift (§7.3). Rule numbers refer to ARCHITECTURE.md §14.
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
    rxmode: str = "off"             # off | shift_rx | linked_rx | edge_ts
    cond_edge: bool = False         # also emit START/STOP EVENTs (A changes while B high)
    period: float = 1.0             # bit period in clocks (16.8 fixed point in hardware)
    presc: int = 1                  # clocks per tick for LEVEL/OE/GAP delays (1..256)
    nbits: int = 8                  # TX shift length (SETN changes it)
    rx_nbits: Optional[int] = None  # RX shift length; None = same as nbits (ISA.md §9 question)
    rx_tail: int = 0                # LINKED_RX: after rx_nbits, emit the next bit as its own token
    order: str = "lsb"              # lsb | msb
    od: bool = False                # open drain: 1 releases (OE=0), 0 drives low
    idle: int = 1
    sampleofs: float = 0.5          # SHIFT_RX: first sample, fraction of a period after the start edge
    autorearm: bool = True
    rx_edge: str = "rise"           # LINKED_RX sampling edge of pin B
    tx_edge: Optional[str] = None   # linked TX shift: change pin A on this edge of pin B
    tx_preload: bool = False        # linked TX: put out bit 0 at once, the rest on TX_EDGE (SPI CPHA=0)
    tx_accept: int = 0xF            # tag mask (bit = tag); other tokens are taken and dropped (D-011)
    stretch: bool = False           # CLKGEN: wait for pin A to read high before timing the high phase

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
        if self.cfg.txmode == "pulse":
            raise NotImplementedError("TX mode pulse not modelled yet")
        if self.cfg.stretch:
            raise NotImplementedError("CLKGEN STRETCH not modelled yet")
        self.reset_state()

    def reset_state(self):
        c = getattr(self, "cfg", PinConfig())
        self.level = c.idle             # TX output register
        self.oe = 1
        self.cursor_q8 = 0
        self.tx_nbits = c.nbits
        self.actions = []               # timed: pending (edge, kind, value), sorted by edge
        self.linked_bits = []           # linked: bits still to put out, one per tx_edge
        self.linked_end = False         # linked: return to IDLE on the next tx_edge
        self._tx_apply = []
        self._rx = "wait_idle"
        self._rx_t0_q8 = 0
        self._rx_bits = []
        self._rx_tail = False
        self._prev_a = None
        self._prev_b = None
        self._prev_b_tx = None

    # -------------------------------------------------------------- pads
    def pad_drive(self):
        """(value, oe) this unit drives on pin A, from the registered output."""
        if self.cfg.od:
            return 0, int(self.level == 0)
        return self.level, self.oe

    @staticmethod
    def _edge(prev, cur, kind):
        if prev is None or cur is None or prev == cur:
            return False
        return (cur == 1) if kind == "rise" else (cur == 0)

    # ---------------------------------------------------------------- TX
    def _linked(self):
        return self.cfg.txmode == "shift" and self.cfg.tx_edge is not None

    def _tx_ready(self, now):
        timed_done = all(t <= now + 1 for t, _, _ in self.actions)
        if self._linked():
            return timed_done and not self.linked_bits   # a pending return-to-idle may be replaced
        return timed_done

    def compute_tx(self, now, b=None):
        """b: synchronised level of pin B this clock (for linked shifts)."""
        apply = self._tx_apply = []
        port = self.tx_port
        if port is not None and port.avail():
            tag, data = port.head()
            if not (self.cfg.tx_accept >> tag) & 1:
                port.take()                    # D-011: not for this unit; drop at once, never block
                self.stats["tx_filtered"] = self.stats.get("tx_filtered", 0) + 1
            elif self._tx_ready(now):
                port.take()
                self.stats["tx_tokens"] += 1
                self._accept(now, tag, data)
        due = [a for a in self.actions if a[0] <= now]
        self.actions = [a for a in self.actions if a[0] > now]
        apply.extend(due)
        if self._linked() and self._edge(self._prev_b_tx, b, self.cfg.tx_edge):
            # §14 P6: a linked shift changes pin A at the edge of the clock that sees pin B's edge
            if self.linked_bits:
                apply.append((now, "level", self.linked_bits.pop(0)))
                self.linked_end = not self.linked_bits
            elif self.linked_end:
                apply.append((now, "level", self.cfg.idle))
                self.linked_end = False
        self._prev_b_tx = b

    def _accept(self, now, tag, data):
        c = self.cfg
        earliest_q8 = (now + 1) << 8          # §14 P3: accept at clock n, earliest pad edge n+1
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
            elif op == CMD_CLK and c.txmode == "clkgen":
                # n periods: leading edge (to !IDLE) at start + i*P, trailing edge at + P/2
                n, p = arg & 0xFF, c.period_q8
                start_q8 = max(self.cursor_q8, earliest_q8)
                for i in range(n):
                    self._schedule((start_q8 + i * p) >> 8, "level", 1 - c.idle)
                    self._schedule((start_q8 + i * p + p // 2) >> 8, "level", c.idle)
                self.cursor_q8 = start_q8 + n * p
            else:
                self.stats["bad_tokens"] += 1
        elif tag in (isa.TAG_DATA, isa.TAG_EVENT) and c.txmode == "level":
            start_q8 = max(self.cursor_q8, earliest_q8)   # LEVEL mode: drive data[0]
            self.cursor_q8 = start_q8
            self._schedule(start_q8 >> 8, "level", data & 1)
        elif tag == isa.TAG_DATA:
            n = self.tx_nbits
            bits = [(data >> i) & 1 for i in range(n)] if c.order == "lsb" else \
                   [(data >> (n - 1 - i)) & 1 for i in range(n)]
            if self._linked():
                # CPHA=0: bit 0 goes out at once only if the unit is idle. If the previous
                # shift is still waiting for its final edge, that edge carries bit 0 (§14 P9).
                if c.tx_preload and not self.linked_end:
                    self._schedule(earliest_q8 >> 8, "level", bits[0])
                    bits = bits[1:]
                self.linked_bits = bits
                self.linked_end = not bits
            else:  # timed shift
                start_q8 = max(self.cursor_q8, earliest_q8)
                p = c.period_q8
                for i, bit in enumerate(bits):
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
    def compute_rx(self, now, a, b=None):
        """a, b: synchronised levels of pins A and B this clock (None if not attached)."""
        c = self.cfg
        if a is not None:
            if c.cond_edge and self._prev_b == 1 and b == 1 and self._prev_a is not None and a != self._prev_a:
                # START: A falls while B high (data[15] = 1); STOP: A rises (data[15] = 0)
                self._emit(isa.TAG_EVENT, ((1 - a) << 15) | (now & 0x7FFF))
                self._rx_bits, self._rx_tail = [], False
            elif c.rxmode == "edge_ts":
                if self._prev_a is not None and a != self._prev_a:
                    self._emit(isa.TAG_EVENT, (a << 15) | (now & 0x7FFF))
            elif c.rxmode == "shift_rx":
                self._shift_rx(now, a)
            elif c.rxmode == "linked_rx" and self._edge(self._prev_b, b, c.rx_edge):
                self._linked_rx(a)
        self._prev_a, self._prev_b = a, b

    def _linked_rx(self, a):
        c = self.cfg
        if self._rx_tail:
            self._rx_tail = False
            self._emit(isa.TAG_DATA, a << 15)          # tail bit (e.g. I2C ACK) in data[15]
            return
        self._rx_bits.append(a)
        n = c.rx_nbits or c.nbits
        if len(self._rx_bits) == n:
            bits = self._rx_bits if c.order == "lsb" else self._rx_bits[::-1]
            self._emit(isa.TAG_DATA, sum(bit << k for k, bit in enumerate(bits)))
            self._rx_bits = []
            self._rx_tail = bool(c.rx_tail)

    def _shift_rx(self, now, sample):
        c = self.cfg
        n = c.rx_nbits or c.nbits
        if self._rx == "wait_idle":
            if sample == c.idle:
                self._rx = "armed"
        elif self._rx == "armed":
            if sample != c.idle:               # start edge detected this clock
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
