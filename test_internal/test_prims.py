# SPDX-FileCopyrightText: © 2026 Kanishk Sama
# SPDX-License-Identifier: Apache-2.0
#
# White-box check of the G1 hard primitives (arch/prims) against the independent Python reference
# models (tools/refmodels/prims.py), cycle by cycle under random stimulus and random
# configurations. Complements the formal proof F4 (formal/f4_prims.sby), whose spec model is
# written separately in SystemVerilog.

import random
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from refmodels.prims import Shift, Timer  # noqa: E402


async def start(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await FallingEdge(dut.clk)


@cocotb.test()
async def test_timer_matches_model(dut):
    await start(dut)
    rng = random.Random(1)
    for trial in range(12):
        reload = rng.choice([0, 1, 2, 3, 7, 25, 434, rng.randrange(1 << 16)])
        oneshot = rng.random() < 0.3
        dut.t_cfg.value = reload | int(oneshot) << 16
        m = Timer(reload, oneshot)
        dut.t_rst.value, dut.t_load.value, dut.t_half.value, dut.t_en.value = 1, 0, 0, 0
        await RisingEdge(dut.clk)
        m.clock(rst=1)
        await FallingEdge(dut.clk)
        for cyc in range(600):
            ins = {"rst": int(rng.random() < 0.01), "load": int(rng.random() < 0.03),
                   "half": rng.getrandbits(1), "en": int(rng.random() < 0.9)}
            dut.t_rst.value, dut.t_load.value = ins["rst"], ins["load"]
            dut.t_half.value, dut.t_en.value = ins["half"], ins["en"]
            await cocotb.triggers.Timer(1, "ns")
            assert int(dut.t_tc.value) == m.outputs(**ins)["tc"], \
                (f"trial {trial} cycle {cyc} RELOAD {reload} oneshot {oneshot} inputs {ins} "
                 f"model count {m.count} armed {m.armed}")
            await RisingEdge(dut.clk)
            m.clock(**ins)
            await FallingEdge(dut.clk)


@cocotb.test()
async def test_shift_matches_model(dut):
    await start(dut)
    rng = random.Random(2)
    for trial in range(12):
        length = rng.randint(1, 15)
        msb = rng.random() < 0.5
        dut.s_cfg.value = length | int(msb) << 4
        m = Shift(length, msb)
        dut.s_rst.value, dut.s_load.value, dut.s_step.value = 1, 0, 0
        await RisingEdge(dut.clk)
        m.clock(rst=1)
        await FallingEdge(dut.clk)
        for _ in range(400):
            ins = {"rst": int(rng.random() < 0.01), "load": int(rng.random() < 0.08),
                   "d": rng.getrandbits(8), "step": int(rng.random() < 0.6), "sin": rng.getrandbits(1)}
            dut.s_rst.value, dut.s_load.value, dut.s_d.value = ins["rst"], ins["load"], ins["d"]
            dut.s_step.value, dut.s_sin.value = ins["step"], ins["sin"]
            await cocotb.triggers.Timer(1, "ns")
            exp = m.outputs()
            assert int(dut.s_q.value) == exp["q"], f"trial {trial}"
            assert int(dut.s_sout.value) == exp["sout"] and int(dut.s_done.value) == exp["done"]
            await RisingEdge(dut.clk)
            m.clock(**ins)
            await FallingEdge(dut.clk)
