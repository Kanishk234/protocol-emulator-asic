# SPDX-FileCopyrightText: © 2026 Kanishk, Krithik
# SPDX-License-Identifier: Apache-2.0

# R2 latch-array + lane smoke test (branch spike/r2-latch): pin-level only, so it also runs in
# gl_test. Pin map: see src/tt_um_tripwire.v on this branch. Slot field positions come from the
# generated src/trw_defs.vh (spec/tripwire.yaml).

import os
import re
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

CLK_PERIOD_NS = 20
STROBE_CLOCKS = 4
REG_WR, SLOT_WR, PUSH, POP0, POP1 = 0, 4, 5, 6, 7
R_ADDR, R_WLO, R_WHI, R_TLO, R_THI, R_CTRL, R_RSEL = range(7)
NWORDS = 52                                   # 12 slots x 4 host words + K0..K3

DEFS = Path(os.environ.get("TRW_DEFS", Path(__file__).resolve().parent.parent / "src" / "trw_defs.vh"))
_defs = dict(re.findall(r"`define (TRW_\w+) (\S+)", DEFS.read_text()))


def d(name):
    v = _defs["TRW_" + name]
    return int(v.split("'d")[1]) if "'d" in v else int(v)


def slot(**fields):
    """A 53-bit slot image from field values, e.g. slot(V=1, OP=d('OP_MOV'))."""
    word = 0
    for name, value in fields.items():
        width = d(f"SLOT_{name}_W")
        assert 0 <= value < (1 << width), (name, value)
        word |= value << d(f"SLOT_{name}_LSB")
    return word


def word_mask(w):
    return 0x1F if (w < 48 and w % 4 == 3) else 0xFFFF


class Pins:
    def __init__(self, dut):
        self.dut = dut
        self.ui = 0
        self.ctrl = 0

    def _ui(self, value):
        self.ui = value
        self.dut.ui_in.value = value

    async def strobe(self, bit, extra=0):
        self._ui(extra | (1 << bit))
        await ClockCycles(self.dut.clk, STROBE_CLOCKS)
        self._ui(extra)
        await ClockCycles(self.dut.clk, STROBE_CLOCKS)

    async def reg(self, sel, byte):
        self.dut.uio_in.value = byte
        await self.strobe(REG_WR, sel << 1)

    async def out(self, rsel):
        await self.reg(R_RSEL, rsel)
        value = self.dut.uo_out.value
        assert value.is_resolvable, f"uo_out has X/Z (rsel {rsel}): {value}"
        return int(value)

    async def word(self, rsel_lo):
        return await self.out(rsel_lo) | (await self.out(rsel_lo + 1) << 8)

    async def write_slot_word(self, w, value):
        await self.reg(R_ADDR, w)
        await self.reg(R_WLO, value & 0xFF)
        await self.reg(R_WHI, value >> 8)
        await self.strobe(SLOT_WR)

    async def read_slot_word(self, w):
        await self.reg(R_ADDR, w)
        return await self.word(0)

    async def set_ctrl(self, run=None, rir=False, tag=None):
        if run is not None:
            self.ctrl = (self.ctrl & ~1) | int(run)
        if tag is not None:
            self.ctrl = (self.ctrl & ~0xC) | (tag << 2)
        await self.reg(R_CTRL, self.ctrl | (2 if rir else 0))

    async def status(self):
        s = await self.out(6)
        return {"o0": s >> 7, "o0_tag": (s >> 5) & 3, "o1": (s >> 4) & 1, "o1_tag": (s >> 2) & 3,
                "i0_full": (s >> 1) & 1, "run": s & 1}

    async def push(self, data, tag=0):
        await self.set_ctrl(tag=tag)
        await self.reg(R_TLO, data & 0xFF)
        await self.reg(R_THI, data >> 8)
        await self.strobe(PUSH)

    async def rir(self, instr):
        await self.reg(R_WLO, instr & 0xFF)
        await self.reg(R_WHI, instr >> 8)
        await self.set_ctrl(rir=True)


async def reset(dut):
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD_NS, unit="ns").start())
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    return Pins(dut)


@cocotb.test()
async def test_latch_array_holds_two_patterns(dut):
    """Every word of the latch slot store (636 slot bits + 64 K bits), two complementary patterns."""
    pins = await reset(dut)
    assert (await pins.status())["run"] == 0
    for flip in (0x0000, 0xFFFF):
        pat = {w: (((w * 0x1357) ^ 0xA5A5 ^ flip) & word_mask(w)) for w in range(NWORDS)}
        for w, v in pat.items():
            await pins.write_slot_word(w, v)
        for w, v in pat.items():
            got = await pins.read_slot_word(w)
            assert got == v, f"slot store word {w}: {got:#06x}, expected {v:#06x} (flip {flip:#x})"
    assert dut.uio_oe.value == 0


@cocotb.test()
async def test_lane_runs_a_program(dut):
    """ISA.md §7.1 (forward 3 bytes, then an EVENT), a routine step pair, a K constant."""
    pins = await reset(dut)
    INIT, SEND, DEC, IDLE, DONE, END = range(6)
    N = 3
    common = {"V": 1, "SE": 1, "NSE": 1, "DF": 3}
    prog = [
        # 0: when SEND, f0=0 do MOV O0 := I0 ; deq ; STATE:=DEC
        slot(**common, SV=SEND, FM=0b0001, FV=0, OP=d("OP_MOV"), DST=d("DST_O0"),
             ASRC=d("ASRC_I0"), DQ=1, NS=DEC, OT=d("TAG_DATA")),
        # 1: when DEC do SUB r0 := r0, #1 -> f0 ; STATE:=SEND
        slot(**{**common, "DF": 0}, SV=DEC, OP=d("OP_SUB"), DST=d("DST_R0"), ASRC=d("ASRC_R0"),
             BSEL=d("BSEL_IMM"), IMM=1, DFE=1, NS=SEND),
        # 2: when SEND, f0=1 do MOV O1 := zero, tag EVENT ; STATE:=IDLE
        slot(**common, SV=SEND, FM=0b0001, FV=0b0001, OP=d("OP_MOV"), DST=d("DST_O1"),
             ASRC=d("ASRC_ZERO"), OT=d("TAG_EVENT"), NS=IDLE),
        # 3: when INIT do MOVB r0 := #N ; STATE:=SEND
        slot(**common, SV=INIT, OP=d("OP_MOVB"), DST=d("DST_R0"), BSEL=d("BSEL_IMM"), IMM=N, NS=SEND),
        # 4: when IDLE, f1=1 (set by the routine) do MOV O1 := r1 ; STATE:=DONE
        slot(**common, SV=IDLE, FM=0b0010, FV=0b0010, OP=d("OP_MOV"), DST=d("DST_O1"),
             ASRC=d("ASRC_R1"), OT=d("TAG_DATA"), NS=DONE),
        # 5: when DONE do OR O0 := zero | K2, tag CTRL ; STATE:=END
        slot(**common, SV=DONE, OP=d("OP_OR"), DST=d("DST_O0"), ASRC=d("ASRC_ZERO"),
             BSEL=d("BSEL_K"), IMM=2, OT=d("TAG_CTRL"), NS=END),
    ]
    K = [0x0000, 0x0000, 0x6001, 0x0000]
    image = {}
    for s in range(12):
        bits = prog[s] if s < len(prog) else 0
        for h in range(4):
            image[4 * s + h] = (bits >> (16 * h)) & word_mask(4 * s + h)
    for j, kv in enumerate(K):
        image[48 + j] = kv
    for w, v in image.items():
        await pins.write_slot_word(w, v)
    for w, v in image.items():
        assert await pins.read_slot_word(w) == v, f"program word {w} did not load"

    await pins.set_ctrl(run=1, tag=d("TAG_DATA"))
    # Slot writes are ignored while running.
    await pins.write_slot_word(0, image[0] ^ 0x0100)
    assert await pins.read_slot_word(0) == image[0], "slot store changed while RUN"

    for i in range(N):
        await pins.push(0x00A1 + i, tag=d("TAG_DATA"))
        st = await pins.status()
        assert st["o0"] == 1 and st["o0_tag"] == d("TAG_DATA"), f"byte {i}: O0 status {st}"
        got = await pins.word(2)
        assert got == 0x00A1 + i, f"byte {i}: O0 = {got:#06x}"
        await pins.strobe(POP0)
    st = await pins.status()
    assert st["o1"] == 1 and st["o1_tag"] == d("TAG_EVENT") and st["o0"] == 0, f"after {N} bytes: {st}"
    assert await pins.word(4) == 0
    await pins.strobe(POP1)

    # Two routine steps: LDI r1, 0x155 then SYS SETF 1 (encodings: ISA.md §5.1).
    ldi = 0x8000 | (d("RT_SUB_LDI") << 12) | (1 << 10) | 0x155
    setf = 0x8000 | (d("RT_SUB_SYS") << 12) | (d("SYS_SETF") << 8) | 1
    await pins.rir(ldi)
    await pins.rir(setf)
    st = await pins.status()
    assert st["o1"] == 1 and st["o1_tag"] == d("TAG_DATA"), f"routine result: {st}"
    assert await pins.word(4) == 0x155, "r1 written by the routine step (LDI) not seen on O1"
    await pins.strobe(POP1)

    st = await pins.status()
    assert st["o0"] == 1 and st["o0_tag"] == d("TAG_CTRL"), f"K2 token: {st}"
    assert await pins.word(2) == 0x6001, "K2 not seen on O0"
    await pins.strobe(POP0)
    assert (await pins.out(7)) & 0x08 == 0, "RIR still valid"
