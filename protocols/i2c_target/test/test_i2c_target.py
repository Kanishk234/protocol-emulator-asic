"""RTL tests for protocols/i2c_target, driven by the independent reference controller
(tools/refmodels/i2c.py: Controller), with a model target at another address on the same bus."""

import os
import re
import shutil
import subprocess
import tempfile

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, NextTimeStep, ReadOnly, RisingEdge

from refmodels.i2c import Controller, Target, decode, wired_and

Q = int(os.environ.get("Q", "4"))
CLK_NS = 20
ADDR = 0x42          # the DUT's default ADDR parameter


def ops_write(addr, ptr, data):
    return [("start",), ("write", addr << 1), ("write", ptr)] + [("write", d) for d in data] + [("stop",)]


def ops_read(addr, ptr, n):
    return ([("start",), ("write", addr << 1), ("write", ptr), ("start",), ("write", (addr << 1) | 1)]
            + [("read", k != n - 1) for k in range(n)] + [("stop",)])


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


async def bus(dut, ops, others=()):
    """Run the reference controller's ops against the DUT (+ model targets) until it is done."""
    c = Controller(Q)
    gen = c.run(ops + [("idle", 8 * Q)])
    drives = next(gen)
    tdrives = [(1, 1)] * len(others)
    sda_t, scl_t = [], []
    nres = sum(1 for op in ops if op[0] in ("write", "read"))
    while True:
        await RisingEdge(dut.clk)
        sda = wired_and(drives[0], 1 - int(dut.sda_oe.value), *[d[0] for d in tdrives])
        scl = wired_and(drives[1], *[d[1] for d in tdrives])
        sda_t.append(sda)
        scl_t.append(scl)
        tdrives = [t.step(sda, scl) for t in others]
        drives = gen.send((sda, scl))
        dut.sda_i.value = sda
        dut.scl_i.value = scl
        if len(c.results) == nres and not c.owned and all(x == 1 for x in sda_t[-8 * Q:]) and len(sda_t) > 16 * Q:
            break
    return c.results, sda_t, scl_t


async def host(dut, cmds):
    """Send host command bytes; return the replies."""
    replies = []
    for byte in cmds:
        dut.h_wdata.value = byte
        dut.h_wvalid.value = 1
        await RisingEdge(dut.clk)          # command taken here (h_wready is always 1)
        dut.h_wvalid.value = 0
        await ReadOnly()                   # a read's reply is valid right after that edge
        if int(dut.h_rvalid.value):
            replies.append(int(dut.h_rdata.value))
        await NextTimeStep()
    return replies


async def read_regs_host(dut, n=4):
    return await host(dut, [0x80 | i for i in range(n)])


def check_bus(sda, scl):
    ev = decode(sda, scl)
    starts_stops = sum(e.kind in ("start", "restart", "stop") for e in ev)
    changes_high = sum(1 for i in range(1, len(sda)) if scl[i] == 1 and scl[i - 1] == 1 and sda[i] != sda[i - 1])
    assert changes_high == starts_stops, "SDA changed while SCL was high outside START/STOP"
    return ev


def sigrok_decode(sda, scl):
    """sigrok's i2c decoder on the recorded bus (independent of our decoder)."""
    if shutil.which("sigrok-cli") is None:
        return None
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "i2c.vcd")
        with open(path, "w") as f:
            f.write("$timescale 1 ns $end\n$scope module top $end\n$var wire 1 ! scl $end\n"
                    "$var wire 1 # sda $end\n$upscope $end\n$enddefinitions $end\n")
            prev = (None, None)
            for t, (c, s_) in enumerate(zip(scl, sda)):
                if (c, s_) != prev:
                    f.write(f"#{t * CLK_NS}\n{c}!\n{s_}#\n")
                    prev = (c, s_)
            f.write(f"#{len(scl) * CLK_NS}\n")
        out = subprocess.run(
            ["sigrok-cli", "-i", path, "-I", f"vcd:samplerate={int(1e9 / CLK_NS)}",
             "-P", "i2c:scl=scl:sda=sda", "-A", "i2c=address-read:address-write:data-read:data-write"],
            capture_output=True, text=True, check=True).stdout
    return [(m.group(1), int(m.group(2), 16)) for m in
            (re.search(r"(Address read|Address write|Data read|Data write): ([0-9A-Fa-f]+)", ln) for ln in out.splitlines()) if m]


@cocotb.test()
async def test_bus_write_then_host_reads(dut):
    await reset(dut)
    res, sda, scl = await bus(dut, ops_write(ADDR, 1, [0x11, 0x22]))
    assert res == [True] * 4
    check_bus(sda, scl)
    assert (int(dut.h_status.value) >> 4) & 0xF == 0b0110, "dirty bits for registers 1 and 2"
    assert await read_regs_host(dut) == [0x00, 0x11, 0x22, 0x00]
    assert (int(dut.h_status.value) >> 4) & 0xF == 0, "host reads clear dirty"


@cocotb.test()
async def test_host_write_then_bus_reads(dut):
    await reset(dut)
    await host(dut, [0x00, 0xA0, 0x01, 0xA1, 0x02, 0xA2, 0x03, 0xA3])
    res, sda, scl = await bus(dut, ops_read(ADDR, 1, 3))
    assert res == [True] * 3 + [0xA1, 0xA2, 0xA3]
    ev = check_bus(sda, scl)
    data = [e for e in ev if e.kind == "byte"][-3:]
    assert [(e.value, e.ack) for e in data] == [(0xA1, True), (0xA2, True), (0xA3, False)]
    sr = sigrok_decode(sda, scl)
    if sr is not None:
        assert sr == [("Address write", ADDR), ("Data write", 1), ("Address read", ADDR),
                      ("Data read", 0xA1), ("Data read", 0xA2), ("Data read", 0xA3)], sr


@cocotb.test()
async def test_auto_increment_wraps(dut):
    await reset(dut)
    res, _, _ = await bus(dut, ops_write(ADDR, 3, [0x33, 0x40, 0x41]) + ops_read(ADDR, 3, 3))
    assert res[-3:] == [0x33, 0x40, 0x41]
    assert await read_regs_host(dut) == [0x40, 0x41, 0x00, 0x33]


@cocotb.test()
async def test_other_address_ignored(dut):
    """A model target at 0x43 on the same bus gets its traffic; the DUT stays silent."""
    await reset(dut)
    other = Target(0x43)
    res, sda, scl = await bus(dut, ops_write(0x43, 0, [0x99]) + ops_write(0x44, 0, [0x77]), others=[other])
    assert res == [True, True, True, False, False, False]
    assert other.regs == {0: 0x99}
    assert await read_regs_host(dut) == [0x00] * 4
    check_bus(sda, scl)


@cocotb.test()
async def test_repeated_start_keeps_pointer(dut):
    await reset(dut)
    await host(dut, [0x00, 0x5A, 0x01, 0x6B])
    ops = [("start",), ("write", ADDR << 1), ("write", 0), ("start",), ("write", (ADDR << 1) | 1),
           ("read", True), ("read", False), ("stop",)]
    res, _, _ = await bus(dut, ops)
    assert res == [True, True, True, 0x5A, 0x6B]


@cocotb.test()
async def test_host_command_errors(dut):
    await reset(dut)
    await host(dut, [0x84, 0x10])         # register 4 does not exist; bad opcode bits
    assert int(dut.h_status.value) & 0b100, "cmd_err not set"
