"""Encodings and the operation table (ISA.md §3, §4.1, §5.1)."""

from hypothesis import given, strategies as st

from tripsim import isa
from tripsim.asm import Routine, cmpm_field, reflex

u16 = st.integers(0, 0xFFFF)


@given(st.integers(0, (1 << isa.SLOT_BITS) - 1))
def test_slot_roundtrip(word):
    assert isa.encode_slot(isa.decode_slot(word)) == word


def test_slot_fields_tile_52_bits():
    covered = 0
    for lsb, width in isa.SLOT_FIELDS.values():
        mask = ((1 << width) - 1) << lsb
        assert covered & mask == 0, "overlapping slot fields"
        covered |= mask
    assert covered == (1 << 52) - 1


@given(u16, u16)
def test_alu_arith_logic(a, b):
    regs = kregs = [0] * 4
    ref = {"MOV": a, "ADD": (a + b) & 0xFFFF, "SUB": (a - b) & 0xFFFF, "AND": a & b,
           "OR": a | b, "XOR": a ^ b, "SHL": (a << (b & 15)) & 0xFFFF, "SHR": a >> (b & 15),
           "MOVB": b}
    for name, d in ref.items():
        r = isa.alu(isa.OP[name], a, b, 0, regs, kregs)
        assert r.d == d and r.r == int(d == 0), name


@given(u16, u16)
def test_compare_ops_pass_a_through(a, b):
    regs, kregs = [0x00FE, 0x00A0, 0, 0], [0x0F0F, 0x0505, 0, 0]
    r = isa.alu(isa.OP["LTU"], a, b, 0, regs, kregs)
    assert (r.d, r.r) == (a, int(a < b))
    r = isa.alu(isa.OP["PAR"], a, b, 0, regs, kregs)
    assert (r.d, r.r) == (a, bin(a).count("1") & 1)
    r = isa.alu(isa.OP["CMPM"], a, 0, cmpm_field("r0", "r1"), regs, kregs)
    assert (r.d, r.r) == (a, int((a & 0x00FE) == 0x00A0))
    r = isa.alu(isa.OP["CMPM"], a, 0, cmpm_field("K0", "K1"), regs, kregs)
    assert r.r == int((a & 0x0F0F) == 0x0505)


def test_field_ops():
    regs = [0, 0x0200, 0, 0]
    # SHOR: UART frame = stop bit (r1 = 0x200) | byte << 1 | start bit 0
    assert isa.alu(isa.OP["SHOR"], 0x55, 0, (1 << 4) | 1, regs, regs).d == 0x2AA
    # EXT: 8 data bits out of a 10-bit frame
    assert isa.alu(isa.OP["EXT"], 0x2AA, 0, (7 << 4) | 1, regs, regs).d == 0x55
    # MKCTL passes A[11:0], including bit 11 (Q3)
    r = isa.alu(isa.OP["MKCTL"], 0x0805, 0, 1 << 4, regs, regs)
    assert r.d == 0x1805 and r.ctrl


def test_reflex_builder_fields():
    s = isa.decode_slot(reflex(op="CMPM", a="I0", f=cmpm_field("K0", "K1"), deq=True,
                               urgent=True, state=3, flags={0: 1, 3: 0}, tag="DATA",
                               head15=0, ns=4, flag=0))
    assert (s.V, s.U, s.SE, s.SV, s.FM, s.FV) == (1, 1, 1, 3, 0b1001, 0b0001)
    assert (s.TE, s.TAG, s.HE, s.HV, s.DQ, s.NSE, s.NS, s.DFE, s.DF) == (1, 0, 1, 0, 1, 1, 4, 1, 0)
    assert s.OP == isa.OP["CMPM"] and s.IMM == 0x14


def test_routine_branch_offsets():
    r = Routine().label("top").alu("ADD", "r1", "r1", 1).djnz("r0", "top").br("top").ret()
    words = r.assemble()
    assert isa.decode_routine(words[1]) == {"kind": "DJNZ", "rd": 0, "off": -2}
    assert isa.decode_routine(words[2]) == {"kind": "BR", "cond": 0, "off": -3}
    assert isa.decode_routine(words[3])["kind"] == "SYS"
