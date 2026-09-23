# SPDX-FileCopyrightText: © 2026 Kanishk, Krithik
# SPDX-License-Identifier: Apache-2.0

# Phase 0 placeholder tests for the 8-bit counter in tt_um_tripwire.
# Pin-level only (ui_in, uo_out, uio_*, clk, rst_n), so they also run in gl_test.
# Counter values are compared relative to each other, never at an absolute
# cycle, so the checks do not depend on where in the clock period we sample.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

CLK_PERIOD_NS = 20  # 50 MHz, matches info.yaml clock_hz


async def reset(dut):
    clock = Clock(dut.clk, CLK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)


def count(dut):
    assert dut.uo_out.value.is_resolvable, f"uo_out has X/Z: {dut.uo_out.value}"
    return int(dut.uo_out.value)


@cocotb.test()
async def test_reset_clears(dut):
    await reset(dut)
    dut.ui_in.value = 1  # enable is ignored while in reset
    await ClockCycles(dut.clk, 5)
    assert count(dut) == 0
    assert int(dut.uio_oe.value) == 0, "uio pins must stay inputs"


@cocotb.test()
async def test_counts_when_enabled(dut):
    await reset(dut)
    dut.rst_n.value = 1
    dut.ui_in.value = 1
    await ClockCycles(dut.clk, 3)
    start = count(dut)
    await ClockCycles(dut.clk, 37)
    assert (count(dut) - start) % 256 == 37


@cocotb.test()
async def test_holds_when_disabled(dut):
    await reset(dut)
    dut.rst_n.value = 1
    dut.ui_in.value = 1
    await ClockCycles(dut.clk, 20)
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 3)
    held = count(dut)
    assert held != 0
    await ClockCycles(dut.clk, 50)
    assert count(dut) == held


@cocotb.test()
async def test_wraps(dut):
    await reset(dut)
    dut.rst_n.value = 1
    dut.ui_in.value = 1
    await ClockCycles(dut.clk, 3)
    start = count(dut)
    await ClockCycles(dut.clk, 300)
    assert (count(dut) - start) % 256 == 300 % 256
