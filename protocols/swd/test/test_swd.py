"""RTL tests for protocols/swd (SWD host bit engine) driven by the host library tools/board/swd.py,
against the independent reference target tools/refmodels/swd.py (written from ADIv5)."""

import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, ReadOnly, NextTimeStep

from refmodels import swd as ref

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "board"))
import swd as host  # noqa: E402

try:
    from cocotb import bridge, resume
except ImportError:
    from cocotb._bridge import bridge, resume

CLK_NS = 20


async def setup(dut, tgt):
    cocotb.start_soon(Clock(dut.clk, CLK_NS, unit="ns").start())
    dut.rst_n.value = 0
    dut.swdio_i.value = 1
    dut.h_wdata.value = 0
    dut.h_wvalid.value = 0
    dut.h_rready.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    conflicts = []

    async def bench():
        tdrive = None
        while True:
            await RisingEdge(dut.clk)
            await ReadOnly()
            clk_ = int(dut.swclk_o.value)
            hdrive = int(dut.swdio_o.value) if int(dut.swdio_oe.value) else None
            tdrive = tgt.step(clk_, hdrive)
            line = hdrive if hdrive is not None else (tdrive if tdrive is not None else 1)
            await NextTimeStep()
            dut.swdio_i.value = line

    cocotb.start_soon(bench())

    @resume
    async def send(b):
        dut.h_wdata.value = b
        dut.h_wvalid.value = 1
        while True:
            await RisingEdge(dut.clk)
            if int(dut.h_wready.value):
                break
        dut.h_wvalid.value = 0

    @resume
    async def reply():
        for _ in range(100000):
            await RisingEdge(dut.clk)
            if int(dut.h_rvalid.value):
                v = int(dut.h_rdata.value)
                dut.h_rready.value = 1
                await RisingEdge(dut.clk)
                dut.h_rready.value = 0
                return v
        raise AssertionError("no reply")

    class Link:
        def send(self, *bytes_):
            for b in bytes_:
                send(b)

        def reply(self):
            return reply()

    return host.Swd(Link())


@cocotb.test()
async def test_connect_dpidr(dut):
    tgt = ref.Target(dpidr=0x0BC11477)
    s = await setup(dut, tgt)

    @bridge
    def session():
        s.connect()
        return s.dp_read(0x0)

    assert await session() == 0x0BC11477
    assert ("swd_mode",) in tgt.log and tgt.errors == [], tgt.errors


@cocotb.test()
async def test_ap_write_read(dut):
    tgt = ref.Target()
    s = await setup(dut, tgt)

    @bridge
    def session():
        s.connect()
        s.ap_write(0, 0x04, 0x2000_0010)
        return s.ap_read(0, 0x04)

    assert await session() == 0x2000_0010
    assert ("ap_write", (0, 0x04), 0x2000_0010) in tgt.log
    assert tgt.errors == [], tgt.errors


@cocotb.test()
async def test_wait_is_retried(dut):
    tgt = ref.Target()
    s = await setup(dut, tgt)

    @bridge
    def session():
        s.connect()
        tgt.wait_next = 3
        s.ap_write(0, 0x0C, 0xCAFE_F00D)
        return s.ap_read(0, 0x0C)

    assert await session() == 0xCAFE_F00D
    assert tgt.wait_next == 0 and tgt.errors == [], tgt.errors


@cocotb.test()
async def test_fault_is_reported_and_cleared(dut):
    tgt = ref.Target()
    s = await setup(dut, tgt)

    @bridge
    def session():
        s.connect()
        tgt.fault_next = 1
        try:
            s.ap_read(0, 0x00)
            return "no fault"
        except host.SwdError as e:
            return str(e), s.dp_read(0x0)            # the DP still answers after ABORT

    result = await session()
    assert result[0] == "FAULT" and result[1] == tgt.dpidr, result
    assert not tgt.sticky_fault
