"""RTL tests for protocols/i2c_ctrl against the independent model (tools/refmodels/i2c.py) and sigrok."""

import os
import re
import shutil
import subprocess
import tempfile

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, NextTimeStep, ReadOnly, RisingEdge

from refmodels.i2c import Event, Target, decode, wired_and

Q = int(os.environ.get("Q", "4"))
CLK_NS = 20
START, WRITE, READ_ACK, READ_NACK, STOP = 0x00, 0x40, 0x80, 0x81, 0xC0


class Bench:
    """Open-drain bus: wired-AND of the DUT's drives and the reference targets' drives."""

    def __init__(self, dut, targets):
        self.dut, self.targets = dut, targets
        self.drives = [(1, 1) for _ in targets]
        self.sda, self.scl = [], []
        self.replies = []

    async def run(self):
        dut = self.dut
        while True:
            await RisingEdge(dut.clk)
            sda = wired_and(1 - int(dut.sda_oe.value), *[d[0] for d in self.drives])
            scl = wired_and(1 - int(dut.scl_oe.value), *[d[1] for d in self.drives])
            self.sda.append(sda)
            self.scl.append(scl)
            self.drives = [t.step(sda, scl) for t in self.targets]
            if int(dut.h_rvalid.value) and int(dut.h_rready.value):
                self.replies.append(int(dut.h_rdata.value))
            dut.sda_i.value = sda
            dut.scl_i.value = scl


async def reset(dut):
    cocotb.start_soon(Clock(dut.clk, CLK_NS, unit="ns").start())
    dut.rst_n.value = 0
    dut.sda_i.value = 1
    dut.scl_i.value = 1
    dut.h_wdata.value = 0
    dut.h_wlast.value = 0
    dut.h_wvalid.value = 0
    dut.h_rready.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)


async def host(dut, cmds):
    for byte in cmds:
        dut.h_wdata.value = byte
        dut.h_wvalid.value = 1
        while True:
            await RisingEdge(dut.clk)
            if int(dut.h_wready.value) == 1:
                break
    dut.h_wvalid.value = 0


async def finish(dut, b, clocks=None):
    await ClockCycles(dut.clk, clocks or 60 * Q)
    await ReadOnly()
    await NextTimeStep()


def write_cmds(addr, ptr, data):
    c = [START, WRITE, addr << 1, WRITE, ptr]
    for d in data:
        c += [WRITE, d]
    return c + [STOP]


def read_cmds(addr, ptr, n):
    c = [START, WRITE, addr << 1, WRITE, ptr, START, WRITE, (addr << 1) | 1]
    c += [READ_ACK] * (n - 1) + [READ_NACK, STOP]
    return c


def check_bus(b):
    """Bus-level checks: SDA changes while SCL is high only at START/STOP, and the bus ends idle."""
    ev = decode(b.sda, b.scl)
    starts_stops = sum(e.kind in ("start", "restart", "stop") for e in ev)
    changes_high = sum(1 for i in range(1, len(b.sda))
                       if b.scl[i] == 1 and b.scl[i - 1] == 1 and b.sda[i] != b.sda[i - 1])
    assert changes_high == starts_stops, "SDA changed while SCL was high outside START/STOP"
    assert b.sda[-1] == 1 and b.scl[-1] == 1, "bus not released at the end"
    return ev


def sigrok_decode(b):
    if shutil.which("sigrok-cli") is None:
        return None
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "i2c.vcd")
        with open(path, "w") as f:
            f.write("$timescale 1 ns $end\n$scope module top $end\n$var wire 1 ! scl $end\n$var wire 1 # sda $end\n$upscope $end\n$enddefinitions $end\n")
            prev = (None, None)
            for t, (c, s) in enumerate(zip(b.scl, b.sda)):
                if (c, s) != prev:
                    f.write(f"#{t * CLK_NS}\n{c}!\n{s}#\n")
                    prev = (c, s)
            f.write(f"#{len(b.scl) * CLK_NS}\n")
        out = subprocess.run(
            ["sigrok-cli", "-i", path, "-I", f"vcd:samplerate={int(1e9 / CLK_NS)}",
             "-P", "i2c:scl=scl:sda=sda", "-A", "i2c=address-read:address-write:data-read:data-write"],
            capture_output=True, text=True, check=True).stdout
    res = []
    for line in out.splitlines():
        m = re.search(r"(Address read|Address write|Data read|Data write): ([0-9A-Fa-f]+)", line)
        if m:
            res.append((m.group(1), int(m.group(2), 16)))
    return res


@cocotb.test()
async def test_write_then_read_back(dut):
    await reset(dut)
    tgt = Target(0x42)
    b = Bench(dut, [tgt])
    cocotb.start_soon(b.run())
    await host(dut, write_cmds(0x42, 5, [0xDE, 0xAD, 0x01]))
    await host(dut, read_cmds(0x42, 5, 3))
    await finish(dut, b)
    assert tgt.regs == {5: 0xDE, 6: 0xAD, 7: 0x01}
    # replies: 5 ACKs for the write, 3 ACKs (addr, ptr, addr+R) then 3 data bytes for the read
    assert b.replies == [0] * 5 + [0] * 3 + [0xDE, 0xAD, 0x01]
    ev = check_bus(b)
    assert [e.kind for e in ev if e.kind != "byte"] == ["start", "stop", "start", "restart", "stop"]
    reads = [e for e in ev if e.kind == "byte"][-3:]
    assert [(e.value, e.ack) for e in reads] == [(0xDE, True), (0xAD, True), (0x01, False)]
    sr = sigrok_decode(b)
    if sr is not None:
        assert sr == [("Address write", 0x42), ("Data write", 5), ("Data write", 0xDE), ("Data write", 0xAD),
                      ("Data write", 0x01), ("Address write", 0x42), ("Data write", 5),
                      ("Address read", 0x42), ("Data read", 0xDE), ("Data read", 0xAD), ("Data read", 0x01)], sr


@cocotb.test()
async def test_wrong_address_is_nacked(dut):
    await reset(dut)
    tgt = Target(0x42)
    b = Bench(dut, [tgt])
    cocotb.start_soon(b.run())
    await host(dut, [START, WRITE, 0x43 << 1, STOP])
    await finish(dut, b)
    assert b.replies == [0x01]
    assert int(dut.h_status.value) & 0b010, "last_nack not set"
    assert tgt.regs == {}
    check_bus(b)


@cocotb.test()
async def test_clock_stretching(dut):
    await reset(dut)
    tgt = Target(0x2C, stretch=13 * Q)
    b = Bench(dut, [tgt])
    cocotb.start_soon(b.run())
    await host(dut, write_cmds(0x2C, 0, [0x5A]))
    await host(dut, read_cmds(0x2C, 0, 1))
    await finish(dut, b, 120 * Q)
    assert tgt.regs == {0: 0x5A}
    assert b.replies[-1] == 0x5A
    check_bus(b)
    # the target held SCL low while the DUT had released it
    held = sum(1 for i, c in enumerate(b.scl) if c == 0)
    assert held > 0


@cocotb.test()
async def test_data_byte_nack(dut):
    await reset(dut)
    tgt = Target(0x11, nack_after=2)
    b = Bench(dut, [tgt])
    cocotb.start_soon(b.run())
    await host(dut, write_cmds(0x11, 0, [0x01, 0x02]))
    await finish(dut, b)
    assert b.replies == [0, 0, 1, 1]
    check_bus(b)


@cocotb.test()
async def test_two_targets_on_one_bus(dut):
    await reset(dut)
    a, c = Target(0x20), Target(0x21)
    b = Bench(dut, [a, c])
    cocotb.start_soon(b.run())
    await host(dut, write_cmds(0x20, 1, [0xAA]))
    await host(dut, write_cmds(0x21, 1, [0xBB]))
    await finish(dut, b)
    assert a.regs == {1: 0xAA} and c.regs == {1: 0xBB}
    check_bus(b)


@cocotb.test()
async def test_commands_without_start_set_err(dut):
    await reset(dut)
    b = Bench(dut, [Target(0x42)])
    cocotb.start_soon(b.run())
    await host(dut, [WRITE, STOP])
    await finish(dut, b, 10)
    assert int(dut.h_status.value) & 0b1000, "err not set"
    assert b.replies == []
