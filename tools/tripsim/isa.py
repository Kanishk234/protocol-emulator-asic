"""TRIPWIRE lane encodings and operation semantics.

Transcribed from docs/design/ISA.md (draft, DECISIONS D-007). Hand-written until
tools/gen generates it from spec/tripwire.yaml at the phase 1 spec freeze; after
that this file is replaced by the generated decoder.
"""

from dataclasses import dataclass

MASK16 = 0xFFFF

# Token tags (ARCHITECTURE.md §4.1)
TAG_DATA, TAG_CTRL, TAG_EVENT, TAG_ERR = 0, 1, 2, 3
TAGS = {"DATA": TAG_DATA, "CTRL": TAG_CTRL, "EVENT": TAG_EVENT, "ERR": TAG_ERR}

# Operation table (ISA.md §3), shared by reflexes and routines
OPS = ["MOV", "ADD", "SUB", "AND", "OR", "XOR", "SHL", "SHR",
       "SHOR", "EXT", "CMPM", "LTU", "PAR", "MKCTL", "CALL", "MOVB"]
OP = {name: code for code, name in enumerate(OPS) if name}

# DST (ISA.md §4.1)
DST_O0, DST_O1, DST_NONE = 4, 5, 6
# ASRC
A_I0, A_I1, A_ZERO, A_TIME = 4, 5, 6, 7
# BSEL
B_REG, B_IMM, B_K = 0, 1, 2

# Reflex slot fields: name -> (lsb, width). ISA.md §4.1, 52 bits.
SLOT_FIELDS = {
    "V": (0, 1), "U": (1, 1), "SE": (2, 1), "SV": (3, 4),
    "FM": (7, 4), "FV": (11, 4), "TE": (15, 1), "TAG": (16, 2),
    "HE": (18, 1), "HV": (19, 1),
    "OP": (20, 4), "DST": (24, 3), "ASRC": (27, 3), "DQ": (30, 1),
    "BSEL": (31, 2), "IMM": (33, 8), "NSE": (41, 1), "NS": (42, 4),
    "DFE": (46, 1), "DF": (47, 2), "OT": (49, 2), "KT": (51, 1),
}
SLOT_BITS = 52


@dataclass(frozen=True)
class Slot:
    V: int = 0
    U: int = 0
    SE: int = 0
    SV: int = 0
    FM: int = 0
    FV: int = 0
    TE: int = 0
    TAG: int = 0
    HE: int = 0
    HV: int = 0
    OP: int = 0
    DST: int = DST_NONE
    ASRC: int = A_ZERO
    DQ: int = 0
    BSEL: int = 0
    IMM: int = 0
    NSE: int = 0
    NS: int = 0
    DFE: int = 0
    DF: int = 0
    OT: int = 0
    KT: int = 0


def encode_slot(slot: Slot) -> int:
    word = 0
    for name, (lsb, width) in SLOT_FIELDS.items():
        value = getattr(slot, name)
        if not 0 <= value < (1 << width):
            raise ValueError(f"slot field {name}={value} does not fit {width} bits")
        word |= value << lsb
    return word


def decode_slot(word: int) -> Slot:
    if not 0 <= word < (1 << SLOT_BITS):
        raise ValueError("slot word wider than 52 bits")
    return Slot(**{name: (word >> lsb) & ((1 << width) - 1)
                   for name, (lsb, width) in SLOT_FIELDS.items()})


def slot_to_host_words(word: int) -> list:
    """The four 16-bit host words of a slot (ISA.md §4.1)."""
    return [(word >> (16 * i)) & MASK16 for i in range(4)]


# ---------------------------------------------------------------------------
# Operation semantics (ISA.md §3)
# ---------------------------------------------------------------------------

@dataclass
class AluResult:
    d: int          # data result
    r: int          # 1-bit flag result
    ctrl: bool = False  # result is a CTRL token (MKCTL)


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
# Routine words (ISA.md §5.1)
# ---------------------------------------------------------------------------

SUB_LDI, SUB_LDIH, SUB_BR, SUB_DJNZ, SUB_LD, SUB_ST, SUB_OUT, SUB_SYS = range(8)
BR_ALWAYS, BR_RZ, BR_NRZ = 0, 1, 2
SYS = {"NOP": 0, "RET": 1, "SETST": 2, "SETF": 3, "CLRF": 4, "TSTF": 5,
       "CPYF": 6, "GETT": 7, "GETK": 8}
SYS_NAMES = {v: k for k, v in SYS.items()}


def _signed(value: int, bits: int) -> int:
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def _field(value: int, bits: int, name: str, signed: bool = False) -> int:
    lo, hi = (-(1 << (bits - 1)), (1 << (bits - 1)) - 1) if signed else (0, (1 << bits) - 1)
    if not lo <= value <= hi:
        raise ValueError(f"routine field {name}={value} out of range [{lo}, {hi}]")
    return value & ((1 << bits) - 1)


def enc_alu(op: str, rd: int, ra: int, b: int, bs: int) -> int:
    code = OP[op]
    if op == "CALL":
        raise ValueError("CALL is not allowed in routines")
    return (_field(code, 4, "op") << 11) | (_field(rd, 2, "rd") << 9) | \
           (_field(ra, 2, "ra") << 7) | (_field(bs, 1, "bs") << 6) | _field(b, 6, "b")


def enc_ctrl(sub: int, payload: int) -> int:
    return 0x8000 | (sub << 12) | (payload & 0x0FFF)


def decode_routine(word: int) -> dict:
    word &= MASK16
    if not word & 0x8000:
        return {"kind": "ALU", "op": (word >> 11) & 15, "rd": (word >> 9) & 3,
                "ra": (word >> 7) & 3, "bs": (word >> 6) & 1, "b": word & 0x3F}
    sub = (word >> 12) & 7
    if sub in (SUB_LDI, SUB_LDIH):
        return {"kind": "LDI" if sub == SUB_LDI else "LDIH", "rd": (word >> 10) & 3,
                "imm": word & 0x3FF}
    if sub == SUB_BR:
        return {"kind": "BR", "cond": (word >> 9) & 7, "off": _signed(word, 9)}
    if sub == SUB_DJNZ:
        return {"kind": "DJNZ", "rd": (word >> 10) & 3, "off": _signed(word, 10)}
    if sub in (SUB_LD, SUB_ST):
        return {"kind": "LD" if sub == SUB_LD else "ST", "rd": (word >> 10) & 3,
                "ra": (word >> 8) & 3, "off": word & 0xFF}
    if sub == SUB_OUT:
        return {"kind": "OUT", "port": (word >> 11) & 1, "tag": (word >> 9) & 3,
                "ra": (word >> 7) & 3}
    return {"kind": "SYS", "sys": (word >> 8) & 15, "arg": word & 0xFF}
