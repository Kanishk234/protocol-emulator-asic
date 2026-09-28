"""L1-EVAL, L1-PIPE and the routine controller of trw_lane, against ISA.md §4-§5 and ARCHITECTURE.md §14
(L1-L12, R1-R6, H1-H2). Expected values are written from those rules, not from any implementation.

Clock numbering as §14: record i is clock i (from reset release); a value written at edge n shows in the
record of clock n+1. The harness drives each clock's inputs at the falling edge and records the design's
outputs (ReadOnly) in the same clock.
"""

import pathlib
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
import tripwire_spec as S  # noqa: E402

OP, DST, ASRC, BSEL = S.OPS, S.DST, S.ASRC, S.BSEL
DATA, CTRL, EVENT, ERR = (S.TAGS[t] for t in ("DATA", "CTRL", "EVENT", "ERR"))
SYS, BR = S.SYS, S.BR_COND
NONE7 = 7                                             # reserved DST code: none (L12)


# ----------------------------------------------------------------------------- encodings
def slot(**f):
    """A reflex slot word from field values (ISA.md §4.1). V defaults to 1."""
    f.setdefault("V", 1)
    w = 0
    for name, v in f.items():
        lsb, width = S.SLOT_FIELDS[name]
        assert 0 <= v < 1 << width, (name, v)
        w |= v << lsb
    return w


def _put(fields, **vals):
    w = 0
    for name, v in vals.items():
        msb, lsb = fields[name]
        v &= (1 << (msb - lsb + 1)) - 1
        w |= v << lsb
    return w


def alu(op, rd, ra, b, bs=1):
    return _put(S.ROUTINE_ALU_FIELDS, op=op, rd=rd, ra=ra, bs=bs, b=b)


def ctrl(name, **vals):
    code, fields = S.ROUTINE_CTRL[name]
    return 1 << 15 | code << S.ROUTINE_CTRL_SUB[1] | _put(fields, **vals)


# ----------------------------------------------------------------------------- harness
REC = ("tnow", "dbg_regs", "dbg_state", "dbg_flags", "dbg_pend", "dbg_rpc", "dbg_rir_valid", "dbg_rz",
       "in_take", "out_load", "out_valid", "out_seq", "out_tok", "mem_en", "mem_we", "mem_addr")


class Lane:
    def __init__(self, dut):
        self.d = dut
        self.recs = []
        self.slots = [0] * 12
        self.drv = dict(run=0, in_avail=0, in_head=0, out_all_taken=3)
        self.sub_last = 0          # a blocking subscriber on O0 (when self.sub is on)
        self.sub = None            # None: all_taken driven as given; else a take policy f(clock) -> bool

    @classmethod
    async def start(cls, dut):
        h = cls(dut)
        cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
        for s in ("run", "step", "slots", "k", "in_avail", "in_head", "out_all_taken", "host_we", "host_sel",
                  "host_wdata", "mem_hwe", "mem_haddr", "mem_hwd"):
            getattr(dut, s).value = 0
        dut.rst_n.value = 0
        for _ in range(2):
            await RisingEdge(dut.clk)
        dut.rst_n.value = 1
        return h

    def set_slots(self, words):
        self.slots = list(words) + [0] * (12 - len(words))
        self.d.slots.value = sum(w << (S.SLOT_BITS * i) for i, w in enumerate(self.slots))

    def set_k(self, ks):
        self.d.k.value = sum(v << (16 * i) for i, v in enumerate(ks))

    async def tick(self, step=0, host=None, **drv):
        """One clock: drive, record, advance. host = (sel, value) for an E2 write this clock."""
        d = self.d
        self.drv.update(drv)
        await FallingEdge(d.clk)
        if self.sub is not None:                     # §4.4 release from the subscriber's registered state
            seq = int(d.out_seq.value) & 1
            valid = int(d.out_valid.value) & 1
            self.drv["out_all_taken"] = (self.drv["out_all_taken"] & 2) | int(self.sub_last == seq)
            take = valid and self.sub_last != seq and self.sub(len(self.recs))
        for k_, v in self.drv.items():
            getattr(d, k_).value = v
        d.step.value = step
        d.host_we.value = int(host is not None)
        if host is not None:
            d.host_sel.value, d.host_wdata.value = host
        await ReadOnly()
        r = {k_: int(getattr(d, k_).value) for k_ in REC}
        r["regs"] = [(r["dbg_regs"] >> (16 * i)) & 0xFFFF for i in range(4)]
        self.recs.append(r)
        if self.sub is not None and take:
            self.sub_last = seq
        await RisingEdge(d.clk)
        return r

    async def ticks(self, n, **drv):
        for _ in range(n):
            await self.tick(**drv)
        return self.recs[-1]

    async def mem_write(self, addr, words):
        d = self.d
        for i, w in enumerate(words):
            await FallingEdge(d.clk)
            d.mem_hwe.value, d.mem_haddr.value, d.mem_hwd.value = 1, addr + i, w
            await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        d.mem_hwe.value = 0

    async def mem_read(self, addr):
        d = self.d
        await FallingEdge(d.clk)
        d.mem_haddr.value = addr
        await ReadOnly()
        v = int(d.mem_hrd.value)
        await RisingEdge(d.clk)
        return v

    def regs(self):
        return self.recs[-1]["regs"]


# ----------------------------------------------------------------------------- reference: ready() and selection
def f(w, name):
    lsb, width = S.SLOT_FIELDS[name]
    return (w >> lsb) & ((1 << width) - 1)


def ready(w, state, flags, pend, avail, head, ofree=(1, 1), rb=0):
    """ISA.md §4.2, written out."""
    if not f(w, "V"):
        return False
    if f(w, "SE") and state != f(w, "SV"):
        return False
    if (flags ^ f(w, "FV")) & f(w, "FM"):
        return False
    if pend & f(w, "FM"):
        return False
    a = f(w, "ASRC")
    if a in (ASRC["I0"], ASRC["I1"]):
        p = a - ASRC["I0"]
        tok = (head >> (18 * p)) & 0x3FFFF
        if not (avail >> p) & 1:
            return False
        if f(w, "TE") and (tok >> 16) != f(w, "TAG"):
            return False
        bit = tok & 1 if f(w, "HS") else (tok >> 15) & 1
        if f(w, "HE") and bit != f(w, "HV"):
            return False
    dst = f(w, "DST")
    if f(w, "OP") != OP["CALL"] and dst in (DST["O0"], DST["O1"]) and not ofree[dst - DST["O0"]]:
        return False
    if f(w, "OP") == OP["CALL"] and rb:
        return False
    return True


# ----------------------------------------------------------------------------- tests
@cocotb.test()
async def test_eval_ready_and_priority(dut):
    """L1-EVAL: random conditions on all 12 slots (STATE, flags, tag and head-bit tests on I0/I1, V) and one
    STEP; the lowest-index ready slot fires (§4.3), its input take happens in the EVAL clock, and its
    MOVB lands in r0. Also L12: BSEL 3 reads IMM, DST 7 writes nothing."""
    rng = random.Random(5)
    h = await Lane.start(dut)
    fired_any = none_ready = 0
    for it in range(400):
        state = rng.randrange(16)
        want_f = rng.randrange(8)
        await h.tick(host=(4, state))
        for i in range(3):                            # f[i] := R of MOVB imm (imm 0 -> R = 1)
            h.set_slots([slot(OP=OP["MOVB"], BSEL=BSEL["imm"], IMM=0 if (want_f >> i) & 1 else 1,
                              DST=DST["none"], DFE=1, DF=i)])
            await h.tick(step=1)
            await h.tick()
        await h.tick(host=(0, 0))
        ws = []
        pv = rng.choice((0.05, 0.2, 0.5, 0.8))          # how many slots are valid varies, so "none ready" occurs
        for i in range(12):
            fm = rng.randrange(16) if rng.random() < 0.5 else 0
            ws.append(slot(
                V=int(rng.random() < pv), U=rng.randrange(2), SE=int(rng.random() < 0.3),
                SV=state if rng.random() < 0.6 else rng.randrange(16), FM=fm,
                FV=(want_f & fm) if rng.random() < 0.6 else rng.randrange(16),
                TE=rng.randrange(2), TAG=rng.randrange(4), HE=rng.randrange(2), HV=rng.randrange(2),
                HS=rng.randrange(2), OP=OP["MOVB"], BSEL=rng.choice((BSEL["imm"], BSEL["imm"], 3)),
                IMM=i + 1, DST=DST["r0"] if rng.random() < 0.9 else NONE7,
                ASRC=rng.choice((ASRC["I0"], ASRC["I1"], ASRC["zero"], ASRC["r1"])), DQ=rng.randrange(2)))
        h.set_slots(ws)
        avail, head = rng.randrange(4), rng.randrange(1 << 36)
        exp = next((i for i, w in enumerate(ws) if ready(w, state, want_f, 0, avail, head)), None)
        r = await h.tick(step=1, in_avail=avail, in_head=head)
        take = 0
        if exp is not None and f(ws[exp], "DQ") and f(ws[exp], "ASRC") in (ASRC["I0"], ASRC["I1"]):
            take = 1 << (f(ws[exp], "ASRC") - ASRC["I0"])
        assert r["in_take"] == take, f"iter {it}: take {r['in_take']} != {take} (slot {exp})"
        await h.tick(in_avail=0)
        r = await h.tick()
        want_r0 = 0 if exp is None or f(ws[exp], "DST") == NONE7 else exp + 1
        assert r["regs"][0] == want_r0, f"iter {it}: r0 = {r['regs'][0]}, expected slot {exp}"
        assert r["dbg_state"] == state and (r["dbg_flags"] & 7) == want_f
        fired_any += exp is not None
        none_ready += exp is None
    assert fired_any > 150 and none_ready > 20, (fired_any, none_ready)


@cocotb.test()
async def test_pipeline_state_flag_pending(dut):
    """L1-PIPE (§14 L3-L5, ISA §4.4): STATE := NS is visible to the next EVAL; a flag written at EXEC is
    visible one clock later, and a slot whose FM covers the pending flag waits exactly one extra clock."""
    h = await Lane.start(dut)
    h.set_slots([
        # s0 writes f0 := 0 (MOVB 1 gives R = 0): f0 already matches s1's FV, so only PEND holds s1 back
        slot(SE=1, SV=0, OP=OP["MOVB"], BSEL=BSEL["imm"], IMM=1, DST=DST["none"], DFE=1, DF=0, NSE=1, NS=1),
        slot(SE=1, SV=1, FM=1, FV=0, OP=OP["MOVB"], BSEL=BSEL["imm"], IMM=0x11, DST=DST["r1"], NSE=1, NS=2),
        slot(SE=1, SV=1, OP=OP["MOVB"], BSEL=BSEL["imm"], IMM=0x22, DST=DST["r2"]),
    ])
    await h.tick()
    c0 = len(h.recs)
    for _ in range(6):
        await h.tick(run=1)
    await h.tick(run=0)
    R = h.recs[c0:]
    # c0: s0 fires; c1: STATE 1, PEND[0] set, s1 blocked by the pending rule, s2 fires; f0 lands at edge c1
    assert [r["dbg_state"] for r in R[:4]] == [0, 1, 1, 2]
    assert R[1]["dbg_pend"] & 1 and not R[2]["dbg_pend"] & 1 and not R[2]["dbg_flags"] & 1
    assert R[2]["regs"][2] != 0x22 and R[3]["regs"][2] == 0x22          # s2: EVAL c1, EXEC c2
    assert R[3]["regs"][1] != 0x11 and R[4]["regs"][1] == 0x11          # s1: EVAL c2 (one clock late), EXEC c3


@cocotb.test()
async def test_output_reservation_and_release(dut):
    """L1-PIPE: a slot that always wants O0 never loads over an untaken token, and with a subscriber that
    takes at once it loads exactly every 3 clocks (§4.4: registered release plus the reservation)."""
    h = await Lane.start(dut)
    h.set_slots([slot(OP=OP["MOVB"], BSEL=BSEL["imm"], IMM=7, DST=DST["O0"], OT=EVENT)])
    h.sub = lambda n: True
    for _ in range(30):
        await h.tick(run=1)
    loads = [i for i, r in enumerate(h.recs) if r["out_load"] & 1]
    assert len(loads) >= 8 and all(b - a == 3 for a, b in zip(loads, loads[1:])), loads
    assert (h.recs[-1]["out_tok"] & 0x3FFFF) == (EVENT << 16 | 7)
    h.sub = lambda n: n % 10 == 0                      # a slow subscriber: never a load over a live token
    start = len(h.recs)
    for _ in range(60):
        await h.tick(run=1)
    for a, b in zip(h.recs[start:], h.recs[start + 1:]):
        if b["out_load"] & 1:
            assert not (a["out_load"] & 1)


def program():
    """The routine of test_routine_steps, at 0x40 (entry 3). Addresses in comments."""
    return [
        ctrl("LDI", rd=1, imm=5),                               # 40 r1 = 5
        alu(OP["ADD"], rd=2, ra=2, b=1),                        # 41 r2 += 1
        ctrl("DJNZ", rd=1, off=-2),                             # 42 back to 41 while r1 != 0
        ctrl("LDI", rd=0, imm=0x100),                           # 43
        ctrl("ST", rd=2, ra=0, off=4),                          # 44 SRAM[0x104] = r2
        ctrl("LD", rd=3, ra=0, off=4),                          # 45 r3 = SRAM[0x104]
        ctrl("OUT", port=0, tag=DATA, ra=3),                    # 46
        ctrl("SYS", fn=SYS["GETT"], arg=0),                     # 47 r0 = time at this step's EVAL
        ctrl("SYS", fn=SYS["SETST"], arg=5),                    # 48
        ctrl("BR", cond=4, off=100),                            # 49 reserved condition: never taken (L12)
        alu(OP["CALL"], rd=3, ra=2, b=0),                       # 4A reserved in routines: NOP (L12)
        ctrl("SYS", fn=12, arg=0),                              # 4B reserved SYS kind: NOP (L12)
        ctrl("BR", cond=BR["always"], off=1),                   # 4C skip 4D
        ctrl("LDI", rd=3, imm=0x3FF),                           # 4D (skipped)
        ctrl("SYS", fn=SYS["SETF"], arg=2),                     # 4E f2 = 1
        ctrl("SYS", fn=SYS["TSTF"], arg=2),                     # 4F RZ = f2
        ctrl("SYS", fn=SYS["CPYF"], arg=1),                     # 50 f1 = RZ
        ctrl("SYS", fn=SYS["CLRF"], arg=2),                     # 51 f2 = 0
        ctrl("SYS", fn=SYS["SETF"], arg=3),                     # 52 f3 = RB: no effect (L10)
        ctrl("SYS", fn=SYS["RET"], arg=0),                      # 53
    ]


@cocotb.test()
async def test_routine_steps(dut):
    """Routine controller (§14 L6, R1-R6, ISA §5): CALL -> entry read on the next rotation slot -> first
    fetch on the slot after; a fetched word competes in the next clock; LDI, ALU, DJNZ loop, ST, LD (a
    second step), OUT, GETT (time at EVAL), SETST, reserved codes, BR, RET. SRAM is touched only on the
    lane's slot."""
    h = await Lane.start(dut)
    await h.mem_write(3, [0x40])
    await h.mem_write(0x40, program())
    h.set_slots([slot(SE=1, SV=0, OP=OP["CALL"], IMM=3, DST=DST["none"], NSE=1, NS=1),
                 slot(SE=1, SV=1, OP=OP["CALL"], IMM=3, DST=DST["none"], NSE=1, NS=6)])   # RB = 1: never ready
    h.sub = lambda n: True
    await h.tick()
    c0 = len(h.recs)
    for _ in range(400):
        r = await h.tick(run=1)
        if len(h.recs) > c0 + 10 and not (r["dbg_flags"] >> 3) & 1:
            break
    R = h.recs
    assert not (R[-1]["dbg_flags"] >> 3) & 1, "routine did not return"
    assert all(r["tnow"] % 4 == 0 for r in R if r["mem_en"]), "SRAM access off the lane's slot"
    call = next(i for i in range(c0, len(R)) if R[i + 1]["dbg_state"] == 1)       # CALL's EVAL clock
    acc = [i for i in range(call, len(R)) if R[i]["mem_en"]]
    assert R[acc[0]]["mem_addr"] == 3 and acc[0] == next(i for i in range(call + 1, len(R)) if R[i]["tnow"] % 4 == 0)
    assert R[acc[1]]["mem_addr"] == 0x40 and acc[1] == acc[0] + 4
    k = acc[1]                                                                    # first fetch
    assert R[k + 2]["regs"][1] != 5 and R[k + 3]["regs"][1] == 5, "fetched step must compete in clock k+1"
    regs = R[-1]["regs"]
    assert regs[1] == 0 and regs[2] == 5 and regs[3] == 5, regs
    assert R[-1]["dbg_state"] == 5 and all(r["dbg_state"] != 6 for r in R), "CALL fired while RB = 1"
    assert (R[-1]["dbg_flags"] & 7) == 0b010, "SETF/TSTF/CPYF/CLRF"
    assert await h.mem_read(0x104) == 5
    loads = [r for r in R if r["out_load"] & 1]
    assert len(loads) == 1
    tok_rec = next(i for i, r in enumerate(R) if r["out_valid"] & 1)
    assert (R[tok_rec]["out_tok"] & 0x3FFFF) == (DATA << 16 | 5)
    v = next(i for i in range(len(R)) if i > call and R[i]["regs"][0] not in (0, 0x100))
    assert R[v]["regs"][0] == R[v - 2]["tnow"], "GETT must return the time at its EVAL (R3)"
    assert [r["mem_we"] for r in R if r["mem_en"]].count(1) == 1


@cocotb.test()
async def test_urgent_beats_routine(dut):
    """§4.3 / ISA §5.3: a waiting routine step beats a non-urgent ready slot (which loses exactly one clock
    per step) but loses to an urgent one."""
    for urgent in (0, 1):
        h = await Lane.start(dut) if urgent == 0 else h
        if urgent:
            await h.tick(run=0, in_avail=0)
            await h.tick(host=(4, 0))
            for i in range(4):
                await h.tick(host=(i, 0))
        await h.mem_write(3, [0x40])
        await h.mem_write(0x40, [ctrl("LDI", rd=1, imm=20), ctrl("DJNZ", rd=1, off=-1),
                                 ctrl("SYS", fn=SYS["RET"], arg=0)])
        h.set_slots([
            slot(SE=1, SV=0, OP=OP["CALL"], IMM=3, DST=DST["none"], NSE=1, NS=1),
            slot(U=urgent, SE=1, SV=1, ASRC=ASRC["I0"], DQ=1, OP=OP["MOV"], DST=DST["none"]),
        ])
        c0 = len(h.recs)
        for _ in range(250):
            await h.tick(run=1, in_avail=1)
        R = h.recs[c0:]
        busy = [r for r in R if r["dbg_state"] == 1]
        if urgent:
            assert all((r["dbg_flags"] >> 3) & 1 for r in busy[2:]), "an urgent slot must starve the routine"
            assert R[-1]["regs"][1] == 0, "the routine must not have made a step"
        else:
            done = next(i for i, r in enumerate(R) if i > 5 and not (r["dbg_flags"] >> 3) & 1)
            lost = sum(1 for r in R[2:done] if not r["in_take"] & 1)
            assert lost == 22, f"non-urgent slot lost {lost} clocks, expected one per step (22)"
            await h.tick(run=0, in_avail=0)


@cocotb.test()
async def test_halt_step_and_host_writes(dut):
    """§14 H2 and D-035 E2: an action selected before RUN drops still executes; STEP runs exactly one EVAL
    and its EXEC; host writes to r0-r3 and STATE apply only while halted."""
    h = await Lane.start(dut)
    h.set_slots([slot(OP=OP["ADD"], ASRC=ASRC["r3"], BSEL=BSEL["imm"], IMM=1, DST=DST["r3"])])
    for _ in range(5):
        await h.tick(run=1)
    await h.tick(run=1, host=(2, 0x55))                     # ignored: running
    r = await h.ticks(4, run=0)
    assert r["regs"][3] == 6 and r["regs"][2] == 0, r["regs"]   # 6 EVALs while running, the last executed
    await h.tick(step=1)
    r = await h.ticks(3)
    assert r["regs"][3] == 7
    await h.tick(step=1)
    await h.tick(step=1)
    r = await h.ticks(3)
    assert r["regs"][3] == 9
    await h.tick(host=(3, 0x1234))
    await h.tick(host=(4, 0xA))
    r = await h.tick()
    assert r["regs"][3] == 0x1234 and r["dbg_state"] == 0xA
