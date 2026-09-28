"""RTL tests for protocols/onewire (1-Wire controller) against the independent reference device
(tools/refmodels/onewire.py, written from the 1-Wire timing specification)."""

import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

from refmodels import onewire

CLK_NS = 20
RESET, WRITE, READ = 0x00, 0x40, 0x80


class Bench:
    """The open-drain line: wired-AND of the controller (dq_oe pulls low) and the devices."""

    def __init__(self, dut, devices):
        self.dut, self.devices = dut, devices
        self.drives = [1] * len(devices)
        self.low_runs = []                 # lengths of controller-driven low pulses (clocks)
        self._low = 0

    async def run(self):
        dut = self.dut
        while True:
            await RisingEdge(dut.clk)
            oe = int(dut.dq_oe.value)
            line = min([1 - oe] + self.drives)
            self.drives = [d.step(line) for d in self.devices]
            dut.dq_i.value = min([1 - oe] + self.drives)


async def reset(dut, devices):
    cocotb.start_soon(Clock(dut.clk, CLK_NS, unit="ns").start())
    dut.rst_n.value = 0
    dut.dq_i.value = 1
    dut.h_wdata.value = 0
    dut.h_wvalid.value = 0
    dut.h_rready.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    bench = Bench(dut, devices)
    cocotb.start_soon(bench.run())
    await ClockCycles(dut.clk, 2)
    return bench


async def send(dut, b):
    dut.h_wdata.value = b
    dut.h_wvalid.value = 1
    while True:
        await RisingEdge(dut.clk)
        if int(dut.h_wready.value):
            break
    dut.h_wvalid.value = 0


async def reply(dut, limit_us=2000):
    for _ in range(limit_us * 1000 // CLK_NS):
        await RisingEdge(dut.clk)
        if int(dut.h_rvalid.value):
            v = int(dut.h_rdata.value)
            dut.h_rready.value = 1
            await RisingEdge(dut.clk)
            dut.h_rready.value = 0
            return v
    raise AssertionError("no reply")


async def idle(dut, limit_us=3000):
    """Wait until the controller is not busy (h_status[0])."""
    for _ in range(limit_us * 1000 // CLK_NS):
        await RisingEdge(dut.clk)
        if not int(dut.h_status.value) & 1:
            return
    raise AssertionError("still busy")


async def line_reset(dut):
    """RESET; returns presence (h_status[3])."""
    await send(dut, RESET)
    await ClockCycles(dut.clk, 2)
    await idle(dut)
    return bool(int(dut.h_status.value) & 0x08)


async def write(dut, v):
    await send(dut, WRITE)
    await send(dut, v)
    await ClockCycles(dut.clk, 2)
    await idle(dut)


ROM = onewire.rom_code(0x28, 0x0000_1234_ABCD)


@cocotb.test()
async def test_presence(dut):
    dev = onewire.Device(ROM, CLK_NS)
    await reset(dut, [dev])
    assert await line_reset(dut), "presence expected"
    assert ("reset",) in dev.log


@cocotb.test()
async def test_no_device(dut):
    await reset(dut, [])
    assert not await line_reset(dut), "no presence expected"


@cocotb.test()
async def test_read_rom(dut):
    """RESET, WRITE 0x33 (READ ROM), 8 x READ: the device's ROM code, CRC-8 valid."""
    dev = onewire.Device(ROM, CLK_NS)
    await reset(dut, [dev])
    assert await line_reset(dut)
    await write(dut, 0x33)
    got = []
    for _ in range(8):
        await send(dut, READ)
        got.append(await reply(dut))
    assert ("byte", 0x33) in dev.log
    assert got == ROM, [hex(b) for b in got]
    assert onewire.crc8(got) == 0


@cocotb.test()
async def test_write_bytes(dut):
    dev = onewire.Device(ROM, CLK_NS)
    await reset(dut, [dev])
    assert await line_reset(dut)
    for v in (0x00, 0xFF, 0xA5):
        await write(dut, v)
    # after a non-ROM command the model stops decoding: check the first byte it saw
    assert ("byte", 0x00) in dev.log


@cocotb.test()
async def test_bad_command(dut):
    await reset(dut, [])
    await send(dut, 0xC0)
    await ClockCycles(dut.clk, 3)
    assert int(dut.h_status.value) & 0x04, "err flag"
