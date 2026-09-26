# SPDX-FileCopyrightText: © 2024 Tiny Tapeout, 2026 Kanishk Sama
# SPDX-License-Identifier: Apache-2.0
#
# Pin-level tests of the phase 1 spike top (DECISIONS D-018): the shell around the fabric macro.
# The fabric itself is a black box here (src/warp_tiny.v); tests only rely on shell behaviour:
# parking, and the bit-bang configuration session (FABulous bitbang protocol: data bits on rising
# edges of CFG_CLK, control bits on falling edges; control 0xFAB1 = word/session on, 0xFAB0 = off).
# Loading real bitstreams into the fabric comes with the phase 2 shell and gl_test.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

RUN, CFG_CLK, CFG_DATA = 0, 1, 2
HALF = 6  # clk cycles per CFG_CLK phase (bitbang synchronizes its inputs over 4 stages)


def ui(dut, run=0, cfg_clk=0, cfg_data=0):
    dut.ui_in.value = (run << RUN) | (cfg_clk << CFG_CLK) | (cfg_data << CFG_DATA)


async def reset(dut):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    dut.ena.value = 1
    ui(dut)
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)


async def bitbang_word(dut, data, control, run=0):
    """Shift one 32-bit data word; the last 16 control bits are `control` (MSB first)."""
    for i in range(32):
        d = (data >> (31 - i)) & 1
        c = (control >> (31 - i)) & 1 if i >= 16 else 0
        ui(dut, run, 0, d)
        await ClockCycles(dut.clk, HALF)
        ui(dut, run, 1, d)                  # rising edge: data bit
        await ClockCycles(dut.clk, HALF)
        ui(dut, run, 1, c)
        await ClockCycles(dut.clk, HALF)
        ui(dut, run, 0, c)                  # falling edge: control bit
        await ClockCycles(dut.clk, HALF)
    ui(dut, run)
    await ClockCycles(dut.clk, 8)


def parked(dut):
    uo = int(dut.uo_out.value)
    return (uo & 0b111100) == 0 and int(dut.uio_oe.value) == 0 and int(dut.uio_out.value) == 0


@cocotb.test()
async def test_outputs_parked_after_reset(dut):
    await reset(dut)
    assert parked(dut), "fabric outputs must be parked while RUN is low"
    assert int(dut.uo_out.value) & 1 == 0, "no configuration session after reset"
    assert int(dut.uo_out.value) & 0b11000010 == 0, "unused outputs must be 0"


@cocotb.test()
async def test_config_session_starts_and_ends(dut):
    await reset(dut)
    await bitbang_word(dut, 0xFAB0FAB1, 0xFAB1)          # sync word, session on
    assert int(dut.uo_out.value) & 1 == 1, "CFG_ACTIVE not set by control pattern 0xFAB1"
    await bitbang_word(dut, 0x00000000, 0xFAB0)          # session off
    assert int(dut.uo_out.value) & 1 == 0, "CFG_ACTIVE not cleared by control pattern 0xFAB0"


@cocotb.test()
async def test_outputs_parked_during_config_even_with_run(dut):
    await reset(dut)
    await bitbang_word(dut, 0xFAB0FAB1, 0xFAB1, run=1)
    ui(dut, run=1)
    await ClockCycles(dut.clk, 5)
    assert int(dut.uo_out.value) & 1 == 1
    assert parked(dut), "outputs must stay parked while a configuration session runs"
    await bitbang_word(dut, 0x00000000, 0xFAB0, run=0)


@cocotb.test()
async def test_wrong_control_pattern_is_ignored(dut):
    await reset(dut)
    await bitbang_word(dut, 0x12345678, 0xFAB2)
    assert int(dut.uo_out.value) & 1 == 0, "only 0xFAB1 may start a session"
    assert parked(dut)
