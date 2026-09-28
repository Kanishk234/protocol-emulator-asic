"""L1-ROT (VERIFICATION.md §6): the SRAM rotation on the whole chip. Every lane runs a routine that stores and
loads through the SRAM while the host reads the SRAM through its own slot. Every clock, white-box: only the
slot's owner (time mod 4: lanes 0..2, host on 3; ARCHITECTURE.md §14 R1) drives the SRAM, and at most one
requester is active. At the end every store is in place and every load returned the stored value."""

import cocotb
from cocotb.triggers import ReadOnly, RisingEdge

from chiplib import S, start
from host import HM, slot_words

OP, DST = S.OPS, S.DST
NL = S.HOST_MAP["lanes"][1] // S.HOST_LANE_STRIDE


def slot(**f):
    f.setdefault("V", 1)
    w = 0
    for name, v in f.items():
        lsb, width = S.SLOT_FIELDS[name]
        w |= v << lsb
    return w


def ctrl(name, **v):
    code, fields = S.ROUTINE_CTRL[name]
    w = 1 << 15 | code << 12
    for k, x in v.items():
        msb, lsb = fields[k]
        w |= (x & ((1 << (msb - lsb + 1)) - 1)) << lsb
    return w


def alu(op, rd, ra, b):
    f = S.ROUTINE_ALU_FIELDS
    w = 0
    for k, x in dict(op=op, rd=rd, ra=ra, bs=1, b=b).items():
        msb, lsb = f[k]
        w |= x << lsb
    return w


def routine(base, n):
    """r0 = base; r1 = n; loop { r0 += 1; SRAM[r0] = r1; r1 -= 1 } ; r2 = SRAM[r0]; STATE 9; RET."""
    return [ctrl("LDI", rd=0, imm=base), ctrl("LDI", rd=1, imm=n),
            alu(OP["ADD"], 0, 0, 1), ctrl("ST", rd=1, ra=0, off=0), ctrl("DJNZ", rd=1, off=-3),
            ctrl("LD", rd=2, ra=0, off=0), ctrl("SYS", fn=S.SYS["SETST"], arg=9), ctrl("SYS", fn=S.SYS["RET"], arg=0)]


@cocotb.test()
async def test_rotation_every_requester_its_slot(dut):
    p = await start(dut)
    c = dut.u_chip
    bad = []

    async def watch():
        while True:
            await RisingEdge(dut.clk)
            await ReadOnly()
            s = int(c.slot.value)
            owners = [k for k in range(NL) if int(c.l_en.value) >> k & 1] + (["host"] if int(c.h_en.value) else [])
            want = s if s < NL else "host"
            if len(owners) > 1 or any(o != want for o in owners):
                bad.append((int(c.tnow.value), s, owners))
    cocotb.start_soon(watch())

    n, bases = 8, [0x100 + 0x20 * k for k in range(NL)]
    await p.write(HM["sram"], [0x40 + 0x10 * k for k in range(NL)])            # entry table: routine k
    for k in range(NL):
        await p.write(HM["sram"] + 0x40 + 0x10 * k, routine(bases[k], n))
        call = slot(SE=1, SV=0, OP=OP["CALL"], IMM=k, NSE=1, NS=1, DST=DST["none"])
        for s in range(12):
            await p.write(HM["slots"] | k << 8 | s << 4, slot_words(call if s == 0 else 0))
        await p.write(HM["slots"] | k << 8 | 12 << 4, [0, 0, 0, 0])
    await p.write(HM["run"], [(1 << NL) - 1])
    reads = 0
    for _ in range(12):                                                        # host traffic on slot 3 meanwhile
        await p.read(HM["sram"] + 0x40, 4)
        reads += 1
    await p.write(HM["run"], [0])
    for k in range(NL):
        lane = dict(zip(S.HOST_LANE_WORDS, await p.read(HM["lanes"] + S.HOST_LANE_STRIDE * k, 9)))
        assert lane["state"] == 9 and not lane["flags"] >> 3 & 1, (k, lane)
        assert lane["r2"] == 1, (k, lane)                                      # the last store, loaded back
        assert await p.read(HM["sram"] + bases[k] + 1, n) == list(range(n, 0, -1)), k
    assert not bad, f"SRAM driven off its owner's slot: {bad[:5]}"
    assert reads == 12
