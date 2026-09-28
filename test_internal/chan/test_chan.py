"""L1-CHAN: the generated fabric and the producer registers against the §14 F1-F7 rules.

Every clock the harness drives that clock's inputs at the falling edge, reads the design (ReadOnly) and
compares every output with a reference model written from ARCHITECTURE.md §4 and §14 F1-F7 (not from any
implementation), then advances the model to the next clock. The directed tests add end-to-end checks
(delivery exactly once and in order, DROPPED counts, release timing) on top.

Clock numbering as §14: in clock n the design shows the state at the start of clock n; takes, loads and
configuration writes driven in clock n act at edge n.
"""

import pathlib
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
import tripwire_spec as S  # noqa: E402  (generated from spec/tripwire.yaml)

PROD, CONS = S.FABRIC_PRODUCERS, S.FABRIC_CONSUMERS
NP, NC = len(PROD), len(CONS)
SRC = [[PROD.index(x) for x in S.LEGAL_SOURCES[c]] for c in CONS]   # port c: sel -> producer
DATA, CTRL, EVENT, ERR = (S.TAGS[t] for t in ("DATA", "CTRL", "EVENT", "ERR"))
ALL_TAGS = 0xF
HOST_IN = PROD.index("HOST_IN")


def bits(x, i, w=1):
    return (x >> (w * i)) & ((1 << w) - 1)


class Model:
    """§4.2-4.4 and §14 F1-F7, one clock at a time."""

    def __init__(self):
        self.valid = [0] * NP
        self.seq = [0] * NP
        self.tok = [0] * NP
        self.en = [0] * NC
        self.tap = [0] * NC
        self.sel = [0] * NC
        self.acc = [0] * NC
        self.last = [0] * NC
        self.dropped = [0] * NC

    def src(self, c, sel=None):
        sel = self.sel[c] if sel is None else sel
        return SRC[c][sel] if sel < len(SRC[c]) else None

    def comb(self, load_req):
        """Outputs during this clock (from the state at its start and this clock's load requests)."""
        present, avail, head = [0] * NC, [0] * NC, [0] * NC
        for c in range(NC):
            p = self.src(c)
            if p is None:
                continue
            head[c] = self.tok[p]
            present[c] = int(self.en[c] and self.valid[p] and self.last[c] != self.seq[p])       # F1
            avail[c] = int(present[c] and bits(self.acc[c], self.tok[p] >> 16))                  # F7
        all_taken = [1] * NP
        for c in range(NC):
            p = self.src(c)
            if p is not None and self.en[c] and not self.tap[c] and self.last[c] != self.seq[p]:
                all_taken[p] = 0                                                                 # §4.4
        free = [int(not self.valid[p] or all_taken[p]) for p in range(NP)]                       # F3
        load = [int(bits(load_req, p) and free[p]) for p in range(NP)]
        return dict(present=present, avail=avail, head=head, all_taken=all_taken, free=free, load=load)

    def step(self, o, tok_in, take, cfg, clr):
        """Edge: takes first, then loads (F4); configuration writes (F5)."""
        for c in range(NC):
            p = self.src(c)
            took = o["avail"][c] and bits(take, c)                                               # F2
            filtered = o["present"][c] and not o["avail"][c]                                     # F7
            drop = self.tap[c] and o["avail"][c] and not bits(take, c) and o["load"][p] if p is not None else 0
            if cfg is not None and bits(cfg[0], c):
                we_mask, en, tap, sel, acc = cfg
                w = self.src(c, sel)
                self.en[c], self.tap[c], self.sel[c], self.acc[c] = en, tap, sel, acc
                self.last[c] = self.seq[w] if w is not None else 0                               # F5
            else:
                if took or filtered or drop:
                    self.last[c] = self.seq[p]
                if drop:
                    self.dropped[c] = min(255, self.dropped[c] + 1)                              # F4
                elif bits(clr, c):
                    self.dropped[c] = 0
        for p in range(NP):
            if o["load"][p]:
                self.valid[p], self.seq[p], self.tok[p] = 1, self.seq[p] ^ 1, tok_in[p]          # F6


class Harness:
    def __init__(self, dut):
        self.dut = dut
        self.m = Model()
        self.n = 0
        self.log = []          # per clock: dict(n, take=[(c, tok)], load=[(p, tok)])

    @classmethod
    async def start(cls, dut, clock=True):
        """Reset (and start the clock, once per test)."""
        h = cls(dut)
        if clock:
            cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
        for s in ("load_req", "tok_in", "take", "cfg_we", "cfg_en", "cfg_tap", "cfg_sel", "cfg_accept",
                  "clr_dropped"):
            getattr(dut, s).value = 0
        dut.rst_n.value = 0
        for _ in range(2):
            await RisingEdge(dut.clk)
        dut.rst_n.value = 1
        return h

    def pred(self, load_req=0):
        return self.m.comb(load_req)

    async def clock(self, load=None, take=0, cfg=None, clr=0):
        """One clock. load: {producer: token}; take: consumer bitmask (a take while not available is a
        no-op, as for the design); cfg: (port bitmask, en, tap, sel, accept); clr: DROPPED clear mask."""
        d, m = self.dut, self.m
        load = load or {}
        await FallingEdge(d.clk)
        load_req = sum(1 << p for p in load)
        tok_in = [load.get(p, 0) for p in range(NP)]
        d.load_req.value = load_req
        d.tok_in.value = sum(t << (18 * p) for p, t in enumerate(tok_in))
        d.take.value = take
        d.cfg_we.value = cfg[0] if cfg else 0
        if cfg:
            d.cfg_en.value, d.cfg_tap.value, d.cfg_sel.value, d.cfg_accept.value = cfg[1:]
        d.clr_dropped.value = clr
        await ReadOnly()
        o = m.comb(load_req)
        got = {s: int(getattr(d, s).value) for s in ("free", "load", "p_valid", "p_seq", "p_tok", "all_taken",
                                                      "avail", "head", "port_state", "dropped")}
        want = dict(
            free=self._pack(o["free"]), load=self._pack(o["load"]), p_valid=self._pack(m.valid),
            p_seq=self._pack(m.seq), p_tok=self._pack(m.tok, 18), all_taken=self._pack(o["all_taken"]),
            avail=self._pack(o["avail"]), head=self._pack([h if a else 0 for h, a in zip(o["head"], o["avail"])], 18),
            port_state=self._pack([a << 6 | s << 2 | t << 1 | e for a, s, t, e in zip(m.acc, m.sel, m.tap, m.en)], 10),
            dropped=self._pack(m.dropped, 8))
        # head is only meaningful while available
        got["head"] = self._pack([bits(got["head"], c, 18) if o["avail"][c] else 0 for c in range(NC)], 18)
        for k, v in want.items():
            assert got[k] == v, f"clock {self.n}: {k} = {got[k]:#x}, model {v:#x}"
        rec = dict(n=self.n, take=[(c, o["head"][c]) for c in range(NC) if o["avail"][c] and bits(take, c)],
                   load=[(p, tok_in[p]) for p in range(NP) if o["load"][p]], o=o)
        m.step(o, tok_in, take, cfg, clr)
        self.log.append(rec)
        self.n += 1
        await RisingEdge(d.clk)
        return rec

    @staticmethod
    def _pack(vals, w=1):
        return sum(v << (w * i) for i, v in enumerate(vals))

    async def connect(self, c, producer, tap=False, accept=ALL_TAGS):
        sel = SRC[c].index(producer)
        await self.clock(cfg=(1 << c, 1, int(tap), sel, accept))


def subscribers_of(p):
    return [c for c in range(NC) if p in SRC[c]]


@cocotb.test()
async def test_subscriber_combinations(dut):
    """L1-CHAN: every combination of 0-4 blocking + 0-2 tap subscribers on one producer (HOST_IN, which
    feeds 12 ports). Blocking subscribers get every token exactly once, in order; taps get a subsequence
    and DROPPED counts exactly what they missed; the producer never loads over an untaken blocking token."""
    rng = random.Random(1)
    first = True
    for nb in range(5):
        for nt in range(3):
            h = await Harness.start(dut, clock=first)
            first = False
            ports = rng.sample(subscribers_of(HOST_IN), nb + nt)
            blocking, taps = ports[:nb], ports[nb:]
            for c in blocking:
                await h.connect(c, HOST_IN)
            for c in taps:
                await h.connect(c, HOST_IN, tap=True)
            sent, got = [], {c: [] for c in ports}
            k = 0
            while len(sent) < 40:
                load = {}
                if rng.random() < 0.6:
                    load = {HOST_IN: (rng.randrange(4) << 16) | k}
                take = sum(1 << c for c in ports if rng.random() < (0.5 if c in blocking else 0.3))
                r = await h.clock(load=load, take=take)
                if r["load"]:
                    sent.append(r["load"][0][1])
                    k += 1
                for c, t in r["take"]:
                    got[c].append(t)
            for _ in range(60):                                # drain: blocking ports take everything
                r = await h.clock(take=sum(1 << c for c in blocking))
                for c, t in r["take"]:
                    got[c].append(t)
            for c in blocking:
                assert got[c] == sent, f"{nb}b+{nt}t: blocking {CONS[c]} got {len(got[c])} of {len(sent)}"
            for c in taps:
                it = iter(sent)
                assert all(t in it for t in got[c]), f"{CONS[c]}: not a subsequence"
                missed = len(sent) - len(got[c])
                last_unseen = int(bool(sent) and (not got[c] or got[c][-1] != sent[-1]))
                assert h.m.dropped[c] == missed - last_unseen, (CONS[c], h.m.dropped[c], missed)
            dut._log.info(f"{nb} blocking + {nt} tap: {len(sent)} tokens")


@cocotb.test()
async def test_release_is_registered(dut):
    """F3: a take in clock n frees the producer only in clock n+1 (no combinational path back); F6: valid
    stays set after the take; F2: a taken token is not seen again."""
    h = await Harness.start(dut)
    c = CONS.index("L0.I0")
    u0 = PROD.index("U0.rx")
    await h.connect(c, u0)
    await h.clock(load={u0: 0x1234})
    r = await h.clock(take=1 << c, load={u0: 0x0001})     # take and a load request in the same clock
    assert r["take"] == [(c, 0x1234)] and not r["load"], "the load must wait for the next clock"
    r = await h.clock(load={u0: 0x0001})
    assert r["load"] == [(u0, 0x0001)] and not r["o"]["avail"][c] and h.m.valid[u0]
    r = await h.clock()
    assert r["o"]["avail"][c]


@cocotb.test()
async def test_tap_dropped_saturates_and_clears(dut):
    """F4: a tap that never takes counts every overwritten token, saturating at 255; clr_dropped clears it;
    the tap never holds the producer back (it loads every clock)."""
    h = await Harness.start(dut)
    c = CONS.index("HOST_OUT")
    p = PROD.index("L1.O0")
    await h.connect(c, p, tap=True)
    for i in range(300):
        r = await h.clock(load={p: i})
        assert r["load"], "a tap must never block its producer"
    assert h.m.dropped[c] == 255
    await h.clock(clr=1 << c)
    assert h.m.dropped[c] == 0


@cocotb.test()
async def test_accept_filter(dut):
    """F7: a token whose tag the port does not accept is never visible and is dropped at the edge as if
    taken, so a filtered blocking port releases the producer; accepted tags still arrive."""
    h = await Harness.start(dut)
    c = CONS.index("U2.tx")
    p = PROD.index("L0.O1")
    await h.connect(c, p, accept=1 << CTRL)
    await h.clock(load={p: EVENT << 16 | 7})
    r = await h.clock()
    assert not r["o"]["avail"][c] and r["o"]["present"][c]
    r = await h.clock(load={p: CTRL << 16 | 8})           # released by the drop at the previous edge
    assert r["load"]
    r = await h.clock(take=1 << c)
    assert r["take"] == [(c, CTRL << 16 | 8)]


@cocotb.test()
async def test_repoint_never_sees_a_stale_token(dut):
    """F5: enabling or re-pointing a port sets last_seq to the new source's seq, so an old token already in
    that producer is not delivered; the next one is."""
    h = await Harness.start(dut)
    c = CONS.index("L1.I1")
    a, b = PROD.index("U3.rx"), PROD.index("L2.O0")
    await h.clock(load={a: 0x0AAA, b: 0x0BBB})            # both hold a token nobody subscribed to
    await h.connect(c, a)
    r = await h.clock()
    assert not r["o"]["avail"][c]
    await h.connect(c, b)                                  # re-point
    r = await h.clock()
    assert not r["o"]["avail"][c]
    await h.clock(load={b: 0x0CCC})
    r = await h.clock(take=1 << c)
    assert r["take"] == [(c, 0x0CCC)]


@cocotb.test()
async def test_sel_beyond_the_list(dut):
    """A sel past the port's legal-source list selects nothing: never available, never blocks anyone."""
    h = await Harness.start(dut)
    c = CONS.index("U0.tx")                                # 7 sources
    await h.clock(cfg=(1 << c, 1, 0, len(SRC[c]), ALL_TAGS))
    for p in SRC[c]:
        await h.clock(load={p: 1})
    for p in SRC[c]:
        r = await h.clock(load={p: 2})
        assert r["load"] and not r["o"]["avail"][c]


@cocotb.test()
async def test_random_against_model(dut):
    """Random loads, takes, configuration writes and clears on all 13 producers and ports, compared with
    the model every clock (the harness asserts every output)."""
    rng = random.Random(7)
    h = await Harness.start(dut)
    for c in range(NC):
        await h.clock(cfg=(1 << c, 1, int(rng.random() < 0.3), rng.randrange(len(SRC[c])),
                           rng.choice((ALL_TAGS, ALL_TAGS, rng.randrange(16)))))
    for _ in range(6000):
        load = {p: rng.randrange(1 << 18) for p in range(NP) if rng.random() < 0.3}
        take = rng.randrange(1 << NC)
        cfg = None
        if rng.random() < 0.02:
            c = rng.randrange(NC)
            cfg = (1 << c, int(rng.random() < 0.9), int(rng.random() < 0.3), rng.randrange(len(SRC[c]) + 1),
                   rng.randrange(16))
        clr = (1 << rng.randrange(NC)) if rng.random() < 0.01 else 0
        await h.clock(load=load, take=take, cfg=cfg, clr=clr)
    delivered = sum(len(r["take"]) for r in h.log)
    assert delivered > 2000, delivered
    dut._log.info(f"{h.n} clocks, {delivered} tokens taken, "
                  f"{sum(len(r['load']) for r in h.log)} loads, DROPPED {h.m.dropped}")
