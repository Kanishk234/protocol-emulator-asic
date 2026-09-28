"""RTL tests for protocols/ws2812 against the independent reference decoder
(tools/refmodels/ws2812.py, written from the WS2812B datasheet)."""

import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, ReadOnly, RisingEdge, NextTimeStep

from refmodels import ws2812

CLK_NS = 20                       # 50 MHz, the parameters' reference rate
TBIT = int(os.environ.get("TBIT", "62"))
RESET_BITS = int(os.environ.get("RESET_BITS", "45"))


async def reset(dut):
    cocotb.start_soon(Clock(dut.clk, CLK_NS, unit="ns").start())
    dut.rst_n.value = 0
    dut.h_wdata.value = 0
    dut.h_wlast.value = 0
    dut.h_wvalid.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)


async def record(dut, wave, stop):
    while not stop[0]:
        await RisingEdge(dut.clk)
        await ReadOnly()
        wave.append(int(dut.dout_o.value))


async def feed(dut, frames, pause_after=None, pause_clocks=0):
    """Stream frames through the host channel (valid/ready), the last byte of each with h_wlast.
    `pause_after` = (frame, byte): stop offering data for `pause_clocks` after that byte."""
    for fi, frame in enumerate(frames):
        for bi, b in enumerate(frame):
            dut.h_wdata.value = b
            dut.h_wlast.value = int(bi == len(frame) - 1)
            dut.h_wvalid.value = 1
            while True:
                await RisingEdge(dut.clk)
                taken = int(dut.h_wready.value)      # the value the design saw at this edge
                if taken:
                    break
            dut.h_wvalid.value = 0
            if pause_after == (fi, bi):
                await ClockCycles(dut.clk, pause_clocks)


async def run(dut, frames, **kw):
    wave, stop = [], [False]
    rec = cocotb.start_soon(record(dut, wave, stop))
    await ClockCycles(dut.clk, 5)                        # idle line first: the decoder needs a rising edge
    await feed(dut, frames, **kw)
    await ClockCycles(dut.clk, (RESET_BITS + 12) * TBIT)
    stop[0] = True
    await rec
    return ws2812.decode(wave, CLK_NS)


@cocotb.test()
async def test_eight_leds(dut):
    """8 LEDs (24 bytes, GRB) as one frame: every bit within the datasheet's windows."""
    await reset(dut)
    rng = random.Random(1)
    data = [rng.randrange(256) for _ in range(24)]
    frames, errors = await run(dut, [data])
    assert errors == [], errors[:5]
    assert frames == [data]
    assert int(dut.h_status.value) & 0x2 == 0, "no underrun"


@cocotb.test()
async def test_two_frames(dut):
    """Two frames, each ended by h_wlast: two latches, the gap long enough to reset the LEDs."""
    await reset(dut)
    a, b = [0x00, 0xFF, 0x0F], [0xA5, 0x5A, 0xC3, 0x3C, 0x81, 0x18]
    frames, errors = await run(dut, [a, b])
    assert errors == [], errors[:5]
    assert frames == [a, b]


@cocotb.test()
async def test_underrun(dut):
    """The host misses a byte's deadline inside a frame: the line stays low (the LEDs latch what
    they have), `underrun` is set, and the rest goes out as a new frame."""
    await reset(dut)
    data = [0x11, 0x22, 0x33, 0x44]
    frames, errors = await run(dut, [data], pause_after=(0, 1), pause_clocks=12 * 8 * TBIT)
    assert errors == [], errors[:5]
    assert frames == [data[:2], data[2:]], frames
    assert int(dut.h_status.value) & 0x2, "underrun flag"
