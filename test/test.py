# SPDX-FileCopyrightText: © 2026 Kanishk, Krithik
# SPDX-License-Identifier: Apache-2.0

# R3 SRAM smoke test (branch spike/r3-sram): pin-level only, so it also runs in gl_test.
# Pin map: see src/tt_um_tripwire.v on this branch.

import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

CLK_PERIOD_NS = 20
STROBE_CLOCKS = 4          # strobes are synchronised (2 flops) and edge-detected
LAST_PASS = 17
BIST_CLOCKS = 18 * (512 + 512) + 16

START, RSEL0, REG_WR, REGSEL0, REGSEL1, MEM_WR, MEM_RD, RSEL1 = range(8)


class Pins:
    def __init__(self, dut):
        self.dut = dut
        self.ui = 0

    def set(self, bit, value):
        self.ui = (self.ui | (1 << bit)) if value else (self.ui & ~(1 << bit))
        self.dut.ui_in.value = self.ui

    async def strobe(self, bit):
        self.set(bit, 1)
        await ClockCycles(self.dut.clk, STROBE_CLOCKS)
        self.set(bit, 0)
        await ClockCycles(self.dut.clk, STROBE_CLOCKS)

    async def reg(self, sel, byte):
        self.set(REGSEL0, sel & 1)
        self.set(REGSEL1, sel >> 1)
        self.dut.uio_in.value = byte
        await self.strobe(REG_WR)

    async def select(self, rsel):
        self.set(RSEL0, rsel & 1)
        self.set(RSEL1, rsel >> 1)
        await ClockCycles(self.dut.clk, 1)
        value = self.dut.uo_out.value
        assert value.is_resolvable, f"uo_out has X/Z: {value}"
        return int(value)

    async def write(self, addr, data):
        await self.reg(0, addr & 0xFF)
        await self.reg(1, addr >> 8)
        await self.reg(2, data & 0xFF)
        await self.reg(3, data >> 8)
        await self.strobe(MEM_WR)

    async def read(self, addr):
        await self.reg(0, addr & 0xFF)
        await self.reg(1, addr >> 8)
        await self.strobe(MEM_RD)
        return await self.select(2) | (await self.select(3) << 8)

    async def status(self):
        s = await self.select(0)
        return {"busy": s >> 7, "done": (s >> 6) & 1, "fail": (s >> 5) & 1, "pass": s & 0x1F}


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


def pattern(p, a):
    if p < 16:
        return 1 << ((a + p) % 16)
    word = ((a & 0x7F) << 9) | a
    return word if p == 16 else word ^ 0xFFFF


@cocotb.test()
async def test_reset_state(dut):
    pins = await reset(dut)
    assert await pins.status() == {"busy": 0, "done": 0, "fail": 0, "pass": 0}
    assert await pins.select(1) == 0, "error count not zero after reset"
    assert dut.uio_oe.value == 0


@cocotb.test()
async def test_direct_address_and_data_lines(dut):
    """Every address line and every data bit, from the pins, with no aliasing."""
    pins = await reset(dut)
    expect = {0: 0xA5A5, 511: 0x5A5A}
    for k in range(9):                              # each address line alone
        expect[1 << k] = 0x0100 * (k + 1) + 0x3C
    for b in range(16):                             # each data bit alone, and its complement
        expect[300 + 2 * b] = 1 << b                # 300..331: clear of the 2^k addresses
        expect[301 + 2 * b] = (1 << b) ^ 0xFFFF
    for addr, data in expect.items():
        await pins.write(addr, data)
    for addr, data in expect.items():
        got = await pins.read(addr)
        assert got == data, f"SRAM[{addr}] = {got:#06x}, expected {data:#06x}"


@cocotb.test()
async def test_bist_walking_ones_and_address_patterns(dut):
    pins = await reset(dut)
    await pins.strobe(START)
    st = await pins.status()
    assert st["busy"] == 1 and st["done"] == 0, f"BIST did not start: {st}"
    waited = 0
    while True:
        await ClockCycles(dut.clk, 512)
        waited += 512
        st = await pins.status()
        if not st["busy"]:
            break
        assert waited < 2 * BIST_CLOCKS, f"BIST still busy after {waited} clocks: {st}"
    assert st["done"] == 1 and st["fail"] == 0 and st["pass"] == LAST_PASS, f"BIST result {st}"
    assert await pins.select(1) == 0, "BIST error count not zero"
    dut._log.info(f"BIST finished within {waited} clocks, no mismatches")

    # Independent check: the last pass is left in the memory; read it back from the pins.
    rng = random.Random(3)
    for addr in [0, 1, 255, 256, 510, 511] + rng.sample(range(512), 10):
        got = await pins.read(addr)
        exp = pattern(LAST_PASS, addr)
        assert got == exp, f"after BIST SRAM[{addr}] = {got:#06x}, expected {exp:#06x}"
