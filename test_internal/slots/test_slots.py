"""L1 slot store (trw_slots): host words land in the right slot bits (ISA.md §4.1) and K (§9 slot index 12),
word 3 keeps only its 5 bits, a write is visible from the clock after it, and other words are untouched.
Runs on the latch array (default) and the flop build (FLOPS=1)."""

import pathlib
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
import tripwire_spec as S  # noqa: E402

SB = S.SLOT_BITS


def expect(words):
    """(slots, k) as the outputs should show them, from the 52 host words last written."""
    slots = 0
    for s in range(12):
        w = words[4 * s:4 * s + 4]
        bits = w[0] | w[1] << 16 | w[2] << 32 | (w[3] & 0x1F) << 48
        slots |= bits << (SB * s)
    k = sum(words[48 + i] << (16 * i) for i in range(4))
    return slots, k


async def write(dut, addr, data):
    await FallingEdge(dut.clk)
    dut.we.value, dut.waddr.value, dut.wdata.value = 1, addr, data
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.we.value = 0
    dut.wdata.value = random.randrange(1 << 16)        # the data bus moves on; the latches must not follow


async def start(dut):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    dut.we.value, dut.waddr.value, dut.wdata.value = 0, 0, 0
    dut.rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1


@cocotb.test()
async def test_every_word_maps_to_its_bits(dut):
    rng = random.Random(2)
    random.seed(9)
    await start(dut)
    words = [rng.randrange(1 << 16) for _ in range(52)]
    for a, v in enumerate(words):
        await write(dut, a, v)
    for a in range(52, 64):                            # ignored addresses
        await write(dut, a, rng.randrange(1 << 16))
    await ReadOnly()
    assert (int(dut.slots.value), int(dut.k.value)) == expect(words)


@cocotb.test()
async def test_random_rewrites_and_timing(dut):
    """Each write shows from the clock after it (mid-clock) and changes only its own word."""
    rng = random.Random(4)
    await start(dut)
    words = [0] * 52
    for a in range(52):
        await write(dut, a, 0)
    for _ in range(600):
        a, v = rng.randrange(52), rng.randrange(1 << 16)
        await FallingEdge(dut.clk)
        dut.we.value, dut.waddr.value, dut.wdata.value = 1, a, v
        await ReadOnly()
        assert (int(dut.slots.value), int(dut.k.value)) == expect(words), "changed before the write edge"
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
        dut.we.value = 0
        dut.wdata.value = rng.randrange(1 << 16)
        words[a] = v
        await ReadOnly()
        assert (int(dut.slots.value), int(dut.k.value)) == expect(words), f"word {a} not visible in clock n+1"
