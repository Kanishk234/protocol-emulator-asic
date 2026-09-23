"""Minimal assembler: Python builders for reflex slots and routines.

This is the phase 1 exploration assembler (DECISIONS D-008), not the .trw language:
it produces exactly the encoded words the host would write (ISA.md §4.1, §5.1).
"""

from . import isa

_DST = {"r0": 0, "r1": 1, "r2": 2, "r3": 3, "O0": isa.DST_O0, "O1": isa.DST_O1,
        "none": isa.DST_NONE}
_ASRC = {"r0": 0, "r1": 1, "r2": 2, "r3": 3, "I0": isa.A_I0, "I1": isa.A_I1,
         "zero": isa.A_ZERO, "time": isa.A_TIME}
_FIELD_OPS = {"SHOR", "EXT", "CMPM", "MKCTL", "CALL"}


def _b_operand(b):
    """B operand -> (BSEL, IMM). 'rN' register, 'KN' constant, int immediate."""
    if b is None:
        return isa.B_IMM, 0
    if isinstance(b, int):
        if not 0 <= b <= 0xFF:
            raise ValueError(f"immediate {b} does not fit 8 bits")
        return isa.B_IMM, b
    if b[0] == "r":
        return isa.B_REG, int(b[1])
    if b[0] == "K":
        return isa.B_K, int(b[1])
    raise ValueError(f"bad B operand {b!r}")


def cmpm_field(mask: str, val: str) -> int:
    """F operand for CMPM: mask and value both registers ('rN') or both constants ('KN')."""
    if mask[0] != val[0] or mask[0] not in "rK":
        raise ValueError("CMPM mask and value must both be registers or both constants")
    return (0x10 if mask[0] == "K" else 0) | (int(val[1]) << 2) | int(mask[1])


def reflex(*, op="MOV", dst="none", a="zero", b=None, f=None,
           urgent=False, state=None, flags=None, tag=None, head15=None,
           deq=False, ns=None, flag=None, ot="DATA", keep_tag=False) -> int:
    """Encode one reflex slot.

    flags: {index: value} over f0..f3 (f3 = RB). flag: flag index that receives
    the op's flag result. f: field operand (IMM) for SHOR/EXT/CMPM/MKCTL/CALL.
    """
    fm = fv = 0
    for idx, val in (flags or {}).items():
        fm |= 1 << idx
        fv |= (val & 1) << idx
    if op in _FIELD_OPS:
        if b is not None and op != "CMPM":
            raise ValueError(f"{op} takes its field operand in f, not b")
        bsel, imm = isa.B_IMM, (f or 0)
    else:
        if f is not None:
            raise ValueError(f"{op} has no field operand")
        bsel, imm = _b_operand(b)
    slot = isa.Slot(
        V=1, U=int(urgent),
        SE=int(state is not None), SV=state or 0,
        FM=fm, FV=fv,
        TE=int(tag is not None), TAG=isa.TAGS[tag] if tag else 0,
        HE=int(head15 is not None), HV=head15 or 0,
        OP=isa.OP[op], DST=_DST[dst], ASRC=_ASRC[a], DQ=int(deq),
        BSEL=bsel, IMM=imm,
        NSE=int(ns is not None), NS=ns or 0,
        DFE=int(flag is not None), DF=flag or 0,
        OT=isa.TAGS[ot], KT=int(keep_tag),
    )
    return isa.encode_slot(slot)


class Routine:
    """Builder for one routine. Branch targets are labels resolved at assembly."""

    def __init__(self):
        self._items = []   # (kind, args)
        self._labels = {}

    def label(self, name):
        self._labels[name] = len(self._items)
        return self

    def _emit(self, kind, **args):
        self._items.append((kind, args))
        return self

    # ALU ops: b is 'rN' or an int immediate (0..63)
    def alu(self, op, rd, ra, b=0):
        rd, ra = int(rd[1]), int(ra[1])
        if isinstance(b, str):
            return self._emit("word", word=isa.enc_alu(op, rd, ra, int(b[1]), 0))
        return self._emit("word", word=isa.enc_alu(op, rd, ra, b, 1))

    def ldi(self, rd, imm):
        return self._emit("word", word=isa.enc_ctrl(isa.SUB_LDI, (int(rd[1]) << 10) | isa._field(imm, 10, "imm")))

    def ldih(self, rd, imm6):
        return self._emit("word", word=isa.enc_ctrl(isa.SUB_LDIH, (int(rd[1]) << 10) | isa._field(imm6, 6, "imm6")))

    def load16(self, rd, value):
        """Pseudo-op: full 16-bit constant as LDI + LDIH."""
        self.ldi(rd, value & 0x3FF)
        if value >> 10:
            self.ldih(rd, value >> 10)
        return self

    def br(self, target, cond="always"):
        code = {"always": isa.BR_ALWAYS, "rz": isa.BR_RZ, "nrz": isa.BR_NRZ}[cond]
        return self._emit("br", target=target, cond=code)

    def djnz(self, rd, target):
        return self._emit("djnz", target=target, rd=int(rd[1]))

    def ld(self, rd, ra, off=0):
        return self._emit("word", word=isa.enc_ctrl(isa.SUB_LD, (int(rd[1]) << 10) | (int(ra[1]) << 8) | isa._field(off, 8, "off")))

    def st(self, rd, ra, off=0):
        return self._emit("word", word=isa.enc_ctrl(isa.SUB_ST, (int(rd[1]) << 10) | (int(ra[1]) << 8) | isa._field(off, 8, "off")))

    def out(self, port, ra, tag="DATA"):
        return self._emit("word", word=isa.enc_ctrl(isa.SUB_OUT, (int(port[1]) << 11) | (isa.TAGS[tag] << 9) | (int(ra[1]) << 7)))

    def sys(self, kind, arg=0):
        return self._emit("word", word=isa.enc_ctrl(isa.SUB_SYS, (isa.SYS[kind] << 8) | (arg & 0xFF)))

    def ret(self):
        return self.sys("RET")

    def setst(self, v):
        return self.sys("SETST", v)

    def setf(self, f):
        return self.sys("SETF", f)

    def clrf(self, f):
        return self.sys("CLRF", f)

    def tstf(self, f):
        return self.sys("TSTF", f)

    def cpyf(self, f):
        return self.sys("CPYF", f)

    def gett(self, rd):
        return self.sys("GETT", int(rd[1]))

    def getk(self, rd, k):
        return self.sys("GETK", (int(k[1]) << 2) | int(rd[1]))

    def assemble(self) -> list:
        words = []
        for pc, (kind, args) in enumerate(self._items):
            if kind == "word":
                words.append(args["word"])
                continue
            off = self._labels[args["target"]] - (pc + 1)   # relative to next instruction
            if kind == "br":
                words.append(isa.enc_ctrl(isa.SUB_BR, (args["cond"] << 9) | isa._field(off, 9, "off", True)))
            else:
                words.append(isa.enc_ctrl(isa.SUB_DJNZ, (args["rd"] << 10) | isa._field(off, 10, "off", True)))
        return words


def link_routines(routines: list, base: int = 32) -> list:
    """SRAM image: entry table in words 0..31 (ISA.md §5.2), routines from `base`.

    routines: list of Routine; CALL n calls routines[n].
    """
    if len(routines) > 32:
        raise ValueError("at most 32 routines (entry table is 32 words)")
    image = [0] * base
    for n, routine in enumerate(routines):
        image[n] = len(image)
        image.extend(routine.assemble())
    return image
