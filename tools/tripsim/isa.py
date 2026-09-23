"""TRIPWIRE lane encodings and operation semantics.

Every bit position and code comes from the generated `tripwire_spec` module (from
spec/tripwire.yaml via tools/gen/gen.py). Only the *meaning* of each operation (alu())
is written here, from docs/design/ISA.md §3.
"""

from dataclasses import make_dataclass

import tripwire_spec as S

MASK16 = (1 << S.DATA_BITS) - 1

# Token tags
TAGS = dict(S.TAGS)
TAG_DATA, TAG_CTRL, TAG_EVENT, TAG_ERR = (TAGS[n] for n in ("DATA", "CTRL", "EVENT", "ERR"))

# Operation table (shared by reflexes and routines)
OP = dict(S.OPS)
OPS = [None] * len(OP)
for _name, _code in OP.items():
    OPS[_code] = _name

# Slot enums
DST_O0, DST_O1, DST_NONE = S.DST["O0"], S.DST["O1"], S.DST["none"]
A_I0, A_I1, A_ZERO, A_TIME = S.ASRC["I0"], S.ASRC["I1"], S.ASRC["zero"], S.ASRC["time"]
B_REG, B_IMM, B_K = S.BSEL["reg"], S.BSEL["imm"], S.BSEL["k"]

# Reflex slot: name -> (lsb, width)
SLOT_FIELDS = dict(S.SLOT_FIELDS)
SLOT_BITS = S.SLOT_BITS
_SLOT_DEFAULTS = {"DST": DST_NONE, "ASRC": A_ZERO}
Slot = make_dataclass("Slot", [(n, int, _SLOT_DEFAULTS.get(n, 0)) for n in SLOT_FIELDS], frozen=True)


def encode_slot(slot) -> int:
    word = 0
    for name, (lsb, width) in SLOT_FIELDS.items():
        value = getattr(slot, name)
        if not 0 <= value < (1 << width):
            raise ValueError(f"slot field {name}={value} does not fit {width} bits")
        word |= value << lsb
    return word


def decode_slot(word: int):
    if not 0 <= word < (1 << SLOT_BITS):
        raise ValueError(f"slot word wider than {SLOT_BITS} bits")
    return Slot(**{name: (word >> lsb) & ((1 << width) - 1)
                   for name, (lsb, width) in SLOT_FIELDS.items()})


def slot_to_host_words(word: int) -> list:
    """The 16-bit host words of a slot, w0 = bits [15:0] first."""
    return [(word >> (16 * i)) & 0xFFFF for i in range(S.SLOT_HOST_WORDS)]


# ---------------------------------------------------------------------------
# Operation semantics (ISA.md §3)
# ---------------------------------------------------------------------------

class AluResult:
    __slots__ = ("d", "r", "ctrl")

    def __init__(self, d, r, ctrl=False):
        self.d, self.r, self.ctrl = d, r, ctrl


def alu(op: int, a: int, b: int, f: int, regs, kregs) -> AluResult:
    """Evaluate one operation. a, b: 16-bit operands; f: 8-bit field operand."""
    a &= MASK16
    b &= MASK16
    f &= 0xFF
    name = OPS[op]
    if name == "MOV":
        d = a
    elif name == "ADD":
        d = (a + b) & MASK16
    elif name == "SUB":
        d = (a - b) & MASK16
    elif name == "AND":
        d = a & b
    elif name == "OR":
        d = a | b
    elif name == "XOR":
        d = a ^ b
    elif name == "SHL":
        d = (a << (b & 15)) & MASK16
    elif name == "SHR":
        d = a >> (b & 15)
    elif name == "SHOR":
        d = ((a << (f & 15)) | regs[(f >> 4) & 3]) & MASK16
    elif name == "EXT":
        d = (a >> (f & 15)) & ((1 << (((f >> 4) & 15) + 1)) - 1)
    elif name == "CMPM":
        src = kregs if f & 0x10 else regs
        return AluResult(a, int((a & src[f & 3]) == src[(f >> 2) & 3]))
    elif name == "LTU":
        return AluResult(a, int(a < b))
    elif name == "PAR":
        return AluResult(a, bin(a).count("1") & 1)
    elif name == "MOVB":
        d = b                   # DECISIONS D-009: condition/dequeue on A, result from B
    elif name == "MKCTL":
        d = (((f >> 4) & 15) << 12) | (a & 0x0FFF)
        return AluResult(d, int(d == 0), ctrl=True)
    else:
        raise ValueError(f"alu: op {op} ({name}) has no data semantics")
    return AluResult(d, int(d == 0))


# ---------------------------------------------------------------------------
# Routine words (ISA.md §5.1), positions from the spec
# ---------------------------------------------------------------------------

BR_ALWAYS, BR_RZ, BR_NRZ = S.BR_COND["always"], S.BR_COND["rz"], S.BR_COND["nrz"]
SYS = dict(S.SYS)
SYS_NAMES = {v: k for k, v in SYS.items()}
_CTRL_BY_CODE = {code: name for name, (code, _) in S.ROUTINE_CTRL.items()}
_SELECT_BIT = S.ROUTINE_BITS - 1


def _get(word, msb, lsb):
    return (word >> lsb) & ((1 << (msb - lsb + 1)) - 1)


def _signed(value: int, bits: int) -> int:
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def _put(value, msb, lsb, name, signed=False):
    bits = msb - lsb + 1
    lo, hi = (-(1 << (bits - 1)), (1 << (bits - 1)) - 1) if signed else (0, (1 << bits) - 1)
    if not lo <= value <= hi:
        raise ValueError(f"routine field {name}={value} out of range [{lo}, {hi}]")
    return (value & ((1 << bits) - 1)) << lsb


def enc_alu(op: str, rd: int, ra: int, b: int, bs: int) -> int:
    if op == "CALL":
        raise ValueError("CALL is not allowed in routines")
    vals = {"op": OP[op], "rd": rd, "ra": ra, "bs": bs, "b": b}
    word = S.ROUTINE_ALU_SELECT << _SELECT_BIT
    for name, (msb, lsb) in S.ROUTINE_ALU_FIELDS.items():
        word |= _put(vals[name], msb, lsb, name)
    return word


def enc_ctrl(kind: str, **vals) -> int:
    """Encode a CTRL-class routine word, e.g. enc_ctrl("LD", rd=1, ra=2, off=5)."""
    code, fields = S.ROUTINE_CTRL[kind]
    if set(vals) != set(fields):
        raise ValueError(f"{kind}: expects fields {sorted(fields)}, got {sorted(vals)}")
    smsb, slsb = S.ROUTINE_CTRL_SUB
    word = (S.ROUTINE_CTRL_SELECT << _SELECT_BIT) | _put(code, smsb, slsb, "sub")
    for name, (msb, lsb) in fields.items():
        word |= _put(vals[name], msb, lsb, name, signed=name in S.ROUTINE_SIGNED[kind])
    return word


def decode_routine(word: int) -> dict:
    word &= (1 << S.ROUTINE_BITS) - 1
    if _get(word, _SELECT_BIT, _SELECT_BIT) == S.ROUTINE_ALU_SELECT:
        out = {"kind": "ALU"}
        out.update({n: _get(word, *r) for n, r in S.ROUTINE_ALU_FIELDS.items()})
        return out
    kind = _CTRL_BY_CODE[_get(word, *S.ROUTINE_CTRL_SUB)]
    _, fields = S.ROUTINE_CTRL[kind]
    out = {"kind": kind}
    for name, (msb, lsb) in fields.items():
        v = _get(word, msb, lsb)
        out[name] = _signed(v, msb - lsb + 1) if name in S.ROUTINE_SIGNED[kind] else v
    return out
