"""L1 pin-unit test library: configuration encoding, a cycle-exact driver/monitor, expected-value helpers.

Clock numbering (ARCHITECTURE.md §14 conventions): clock n is the cycle that edge n ends. The monitor
runs once per clock, at the falling edge (mid-clock): it applies that clock's pad and token drives, then
reads (ReadOnly) the combinational outputs of the clock (`tx_take`, `rx_ld`) and the registered ones.
So in the log of clock n:
  - `take` = the head token is taken at edge n;
  - `a` / `line` = the pad register value during clock n (an action "at edge k" shows from clock k+1);
  - `load` = the RX half loads its producer at edge n.
A pad value driven for clock t reaches the unit (through the 2-FF synchroniser, P1) in clock t+2.

Expected values in the tests are written from the §14 rules, not from any implementation.
"""

import pathlib
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Event, FallingEdge, ReadOnly, RisingEdge

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
import tripwire_spec as S  # noqa: E402  (generated from spec/tripwire.yaml)

DATA, CTRL, EVENT, ERR = (S.TAGS[t] for t in ("DATA", "CTRL", "EVENT", "ERR"))
CMD = S.PIN_CMD
PAD = S.PADS
NONE = 31
WORDS = 22


def enum(field, name):
    return S.PIN_CFG_ENUMS[field][name]


def q8(x):
    """A time in clocks as the 16.8 register value."""
    return round(x * 256)


def encode(**f):
    """Configuration block words from field values as stored (use q8() for times, value - 1 for m1)."""
    vals = dict(pin_a=NONE, pin_b=NONE, pin_c=NONE, pin_s=NONE, pin_n=NONE, period=q8(1))
    vals.update(f)
    block = 0
    for name, v in vals.items():
        bit, width, _ = S.PIN_CFG_FIELDS[name]
        assert 0 <= v < 1 << width, (name, v)
        block |= v << bit
    return [(block >> (16 * w)) & 0xFFFF for w in range(WORDS)]


def ctrl(op, arg=0):
    return (CTRL, CMD[op] << 12 | arg)


def level(v, d=0):
    return ctrl("LEVEL", v << 11 | d)


class PinTb:
    def __init__(self, dut):
        self.dut = dut
        self.n = -1                  # current clock (monitor)
        self.log = []                # one dict per clock
        self.tokens = []             # [(tag, data, not_before_clock)]
        self.takes = []              # [(clock, tag, data)]
        self.loads = []              # [(clock, tag, data)]
        self.pad_sched = {}          # clock -> {pad: value}
        self.pads = 0xFFFFFF         # pads_ext (pull-ups)
        self.hook = None             # f(tb) called each clock before the drives are applied
        self.pokes = {}              # clock -> {signal: value}, applied in that clock
        self._tick = Event()

    async def start(self, words, live=True, sub_ready=True, pads=0xFFFFFF):
        d = self.dut
        cocotb.start_soon(Clock(d.clk, 20, unit="ns").start())
        self.pads = pads
        for s, v in (("rst_n", 0), ("live", 0), ("we", 0), ("waddr", 0), ("wdata", 0), ("pads_ext", pads),
                     ("tx_avail", 0), ("tx_tag", 0), ("tx_data", 0), ("sub_en", 1),
                     ("sub_ready", int(sub_ready)), ("clr_late", 0), ("clr_overrun", 0)):
            getattr(d, s).value = v
        for _ in range(4):
            await RisingEdge(d.clk)
        d.rst_n.value = 1
        await self.write(words)
        d.live.value = int(live)
        cocotb.start_soon(self._monitor())
        await FallingEdge(d.clk)
        await ReadOnly()

    async def write(self, words):
        """Host writes of the whole block, one word per clock (§14 H1)."""
        d = self.dut
        for w, v in enumerate(words):
            await FallingEdge(d.clk)
            d.we.value, d.waddr.value, d.wdata.value = 1, w, v
        await FallingEdge(d.clk)
        d.we.value = 0
        for _ in range(3):
            await FallingEdge(d.clk)

    def send(self, *toks, at=0):
        """Queue tokens (tag, data); the first is not offered before clock `at`."""
        for i, (tag, data) in enumerate(toks):
            self.tokens.append((tag, data, at if i == 0 else 0))

    def drive(self, clock, pad, value):
        self.pad_sched.setdefault(clock, {})[pad] = value

    def drive_bits(self, start, pad, bits, clocks_per_bit):
        """Drive `bits` on `pad`, bit i from clock start + floor(i * clocks_per_bit)."""
        for i, b in enumerate(bits):
            self.drive(start + int(i * clocks_per_bit), pad, b)

    async def _monitor(self):
        d = self.dut
        head = None
        while True:
            await FallingEdge(d.clk)
            self.n += 1
            n = self.n
            if self.hook:
                self.hook(self)
            for pad, v in self.pad_sched.pop(n, {}).items():
                self.pads = (self.pads & ~(1 << pad)) | (v << pad)
            d.pads_ext.value = self.pads
            for sig, v in self.pokes.pop(n, {}).items():
                getattr(d, sig).value = v
            if head is None and self.tokens and self.tokens[0][2] <= n:
                head = self.tokens.pop(0)
            if head is not None:
                d.tx_avail.value, d.tx_tag.value, d.tx_data.value = 1, head[0], head[1]
            else:
                d.tx_avail.value = 0
            await ReadOnly()
            rec = dict(n=n, take=int(d.tx_take.value), load=int(d.rx_ld.value), tok=int(d.rx_tok.value),
                       a=int(d.a_out.value), aoe=int(d.a_oe.value), nn=int(d.n_out.value),
                       noe=int(d.n_oe.value), line=int(d.line.value), late=int(d.late.value),
                       ovr=int(d.overrun.value), valid=int(d.p_valid.value))
            self.log.append(rec)
            if rec["take"]:
                self.takes.append((n, head[0], head[1]))
                head = None
            if rec["load"]:
                self.loads.append((n, rec["tok"] >> 16, rec["tok"] & 0xFFFF))
            ev, self._tick = self._tick, Event()
            ev.set()

    def poke(self, clock, **sigs):
        """Set harness inputs (e.g. clr_late=1) for one clock, then back to 0."""
        self.pokes.setdefault(clock, {}).update(sigs)
        self.pokes.setdefault(clock + 1, {}).update({k: 0 for k in sigs})

    async def until(self, clock):
        """Wait until the log holds clock `clock` (drives for later clocks go through the queues)."""
        while len(self.log) <= clock:
            await self._tick.wait()

    async def settle(self, clocks=1):
        await self.until(self.n + clocks)

    async def until_taken(self, count, limit=100000):
        start = self.n
        while len(self.takes) < count:
            assert self.n - start < limit, f"only {len(self.takes)} of {count} tokens taken"
            await self.settle()

    def line(self, pad, n):
        return self.log[n]["line"] >> pad & 1

    def changes(self, pad, since=0):
        """[(clock, new value)] of a pad line from clock `since` on (first clock of each new value)."""
        out, prev = [], None
        for r in self.log[since:]:
            v = r["line"] >> pad & 1
            if prev is not None and v != prev:
                out.append((r["n"], v))
            prev = v
        return out


def edge(t256):
    """The edge on which an action at time t (1/256 clocks) lands (P4: t >> 8)."""
    return t256 >> 8
