"""L1 pad owners (trw_pins, ARCHITECTURE.md §7.1, §10): reset leaves every pad undriven; only the owning
unit's pin A (else pin N) output reaches a pad; host pads ignore owner writes; owners read back."""

import pathlib
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
import tripwire_spec as S  # noqa: E402

NU = 6
HOST = {S.PADS["uo3"] - 8, S.PADS["uo6"] - 8}          # MISO, IRQ (spec `pads.host`)


def expect(own, pa, pn, a, aoe, n, noe):
    out = oe = 0
    for i in range(16):
        u = own[i]
        if u >= NU:
            continue
        if pa[u] == i + 8:
            out |= ((a >> u) & 1) << i
            oe |= ((aoe >> u) & 1) << i
        elif pn[u] == i + 8:
            out |= ((n >> u) & 1) << i
            oe |= ((noe >> u) & 1) << i
    return out, oe


@cocotb.test()
async def test_owners_and_mux(dut):
    rng = random.Random(6)
    assert HOST == {3, 6}
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    for s in ("own_we", "own_waddr", "own_wdata", "own_raddr", "a_out", "a_oe", "n_out", "n_oe", "pin_a", "pin_n"):
        getattr(dut, s).value = 0
    dut.rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    own = [7] * 16
    for it in range(1500):
        await FallingEdge(dut.clk)
        pa = [rng.choice((rng.randrange(8, 24), 31, rng.randrange(0, 8))) for _ in range(NU)]
        pn = [rng.choice((rng.randrange(8, 24), 31)) for _ in range(NU)]
        a, aoe, n, noe = (rng.randrange(1 << NU) for _ in range(4))
        dut.pin_a.value = sum(p << (5 * u) for u, p in enumerate(pa))
        dut.pin_n.value = sum(p << (5 * u) for u, p in enumerate(pn))
        dut.a_out.value, dut.a_oe.value, dut.n_out.value, dut.n_oe.value = a, aoe, n, noe
        w = rng.random() < 0.5
        wa, wd = rng.randrange(16), rng.randrange(8)
        dut.own_we.value, dut.own_waddr.value, dut.own_wdata.value = int(w), wa, wd
        ra = rng.randrange(16)
        dut.own_raddr.value = ra
        await ReadOnly()
        got = (int(dut.pad_out.value), int(dut.pad_oe.value))
        assert got == expect(own, pa, pn, a, aoe, n, noe), f"clock {it}"
        assert int(dut.own_q.value) == own[ra]
        if it == 0:
            assert got == (0, 0), "after reset no pad may be driven"
        if w and wa not in HOST:
            own[wa] = wd
        await RisingEdge(dut.clk)
    assert all(own[h] == 7 for h in HOST)
