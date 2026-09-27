"""L1-ALU: all 16 operations against a Python reference written from the ISA.md §3 table (op codes from
spec/tripwire.yaml through tools/tripwire_spec.py), over edge-case and random operands."""

import itertools
import pathlib
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
import tripwire_spec as S  # noqa: E402

OP = S.OPS
M16 = 0xFFFF
EDGES = (0, 1, 2, 0x7FFF, 0x8000, 0x8001, 0xFFFE, 0xFFFF, 0x00FF, 0xFF00, 0x5555, 0xAAAA, 0x1234)


def ref(op, a, b, f, rf, m, v):
    """(d, R) for one operation, as ISA.md §3 states it."""
    z = lambda d: (d, int(d == 0))
    if op == OP["MOV"]:
        return z(a)
    if op == OP["ADD"]:
        return z((a + b) & M16)
    if op == OP["SUB"]:
        return z((a - b) & M16)
    if op == OP["AND"]:
        return z(a & b)
    if op == OP["OR"]:
        return z(a | b)
    if op == OP["XOR"]:
        return z(a ^ b)
    if op == OP["SHL"]:
        return z((a << (b & 15)) & M16)
    if op == OP["SHR"]:
        return z(a >> (b & 15))
    if op == OP["SHOR"]:
        return z(((a << (f & 15)) & M16) | rf)
    if op == OP["EXT"]:
        return z((a >> (f & 15)) & ((1 << ((f >> 4) + 1)) - 1))
    if op == OP["CMPM"]:
        return a, int((a & m) == v)
    if op == OP["LTU"]:
        return a, int(a < b)
    if op == OP["PAR"]:
        return a, bin(a).count("1") & 1
    if op == OP["MKCTL"]:
        return z((f >> 4) << 12 | (a & 0xFFF))
    if op == OP["CALL"]:
        return 0, 0          # no data or flag result (the lane starts the routine)
    if op == OP["MOVB"]:
        return z(b)
    raise ValueError(op)


async def check(dut, op, a, b, f, rf=0, m=0, v=0):
    dut.op.value, dut.a.value, dut.b.value, dut.f.value = op, a, b, f
    dut.rf.value, dut.m.value, dut.v.value = rf, m, v
    await Timer(1, unit="ns")
    got = (int(dut.d.value), int(dut.r.value))
    want = ref(op, a, b, f, rf, m, v)
    assert got == want, f"op {op} a={a:#06x} b={b:#06x} f={f:#04x} rf={rf:#06x} m={m:#06x} v={v:#06x}: {got} != {want}"


@cocotb.test()
async def test_op_table_is_the_spec(dut):
    """The 16 codes are the spec's (a renumbering in the yaml must reach both the RTL and this test)."""
    assert sorted(OP.values()) == list(range(16))


@cocotb.test()
async def test_edge_operands(dut):
    """Every op over the edge-case operand pairs; shifts, SHOR and EXT over every amount and field width."""
    for op in range(16):
        for a, b in itertools.product(EDGES, EDGES):
            await check(dut, op, a, b, f=b & 0xFF, rf=a ^ b, m=b, v=a & b)
    for a in EDGES:
        for sh in range(16):
            await check(dut, OP["SHL"], a, sh | 0xFFF0, f=0)             # only B[3:0] counts
            await check(dut, OP["SHR"], a, sh | 0x0100, f=0)
            for w in range(16):
                f = w << 4 | sh
                await check(dut, OP["EXT"], a, 0, f)
                await check(dut, OP["MKCTL"], a, 0, f)
                for sel in range(4):
                    await check(dut, OP["SHOR"], a, 0, sel << 4 | sh, rf=(1 << sel) | 0x10 * sel)


@cocotb.test()
async def test_cmpm_matches(dut):
    """CMPM: R = (A & M) == V, true and false cases for many masks; d passes A through."""
    rng = random.Random(3)
    for _ in range(2000):
        a, m = rng.randrange(1 << 16), rng.randrange(1 << 16)
        v = a & m if rng.random() < 0.5 else rng.randrange(1 << 16)
        await check(dut, OP["CMPM"], a, rng.randrange(1 << 16), rng.randrange(256), m=m, v=v)


@cocotb.test()
async def test_random_operands(dut):
    rng = random.Random(11)
    for _ in range(20000):
        await check(dut, rng.randrange(16), rng.randrange(1 << 16), rng.randrange(1 << 16), rng.randrange(256),
                    rf=rng.randrange(1 << 16), m=rng.randrange(1 << 16), v=rng.randrange(1 << 16))
