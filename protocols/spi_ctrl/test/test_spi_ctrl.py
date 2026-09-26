"""RTL tests for protocols/spi_ctrl against the independent model (tools/refmodels/spi.py) and sigrok."""

import os
import random
import shutil
import subprocess
import tempfile

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, NextTimeStep, ReadOnly, RisingEdge

from refmodels.spi import Target, decode, idle_ok

CPOL = int(os.environ.get("CPOL", "0"))
CPHA = int(os.environ.get("CPHA", "0"))
HALF = int(os.environ.get("HALF", "4"))
CLK_NS = 20


class Bench:
    """Connects the DUT's pins to a reference SPI target, one system clock at a time, and records the lines."""

    def __init__(self, dut, responses):
        self.dut = dut
        self.tgt = Target(CPOL, CPHA, responses=responses)
        self.cs, self.sck, self.mosi, self.miso = [], [], [], []
        self.host_rx = []
        self.take_rx = True

    async def run(self):
        dut = self.dut
        while True:
            await RisingEdge(dut.clk)
            # values of the clock period that just ended
            c, s, o = int(dut.cs_n_o.value), int(dut.sck_o.value), int(dut.mosi_o.value)
            i = self.tgt.step(c, s, o)
            self.cs.append(c); self.sck.append(s); self.mosi.append(o); self.miso.append(i)
            if self.take_rx and int(dut.h_rvalid.value) and int(dut.h_rready.value):
                self.host_rx.append(int(dut.h_rdata.value))
            dut.miso_i.value = i
            dut.h_rready.value = 1 if self.take_rx else 0


async def reset(dut):
    cocotb.start_soon(Clock(dut.clk, CLK_NS, unit="ns").start())
    dut.rst_n.value = 0
    dut.miso_i.value = 1
    dut.h_wdata.value = 0
    dut.h_wlast.value = 0
    dut.h_wvalid.value = 0
    dut.h_rready.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)


async def send(dut, data, stall=0):
    """Send one transaction; `stall` idle clocks between bytes (CS must stay low)."""
    for k, byte in enumerate(data):
        dut.h_wdata.value = byte
        dut.h_wlast.value = 1 if k == len(data) - 1 else 0
        dut.h_wvalid.value = 1
        while True:
            await RisingEdge(dut.clk)
            if int(dut.h_wready.value) == 1:
                break
        dut.h_wvalid.value = 0
        if stall:
            await ClockCycles(dut.clk, stall)


async def settle(dut, clocks):
    await ClockCycles(dut.clk, clocks)
    await ReadOnly()
    await NextTimeStep()


def sigrok_decode(b):
    if shutil.which("sigrok-cli") is None:
        return None
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "spi.vcd")
        sigs = {"cs": b.cs, "sck": b.sck, "mosi": b.mosi, "miso": b.miso}
        ids = dict(zip(sigs, "!#$%"))
        with open(path, "w") as f:
            f.write("$timescale 1 ns $end\n$scope module top $end\n")
            for name, i in ids.items():
                f.write(f"$var wire 1 {i} {name} $end\n")
            f.write("$upscope $end\n$enddefinitions $end\n")
            prev = {}
            for t in range(len(b.cs)):
                changes = [(ids[n], v[t]) for n, v in sigs.items() if prev.get(n) != v[t]]
                if changes:
                    f.write(f"#{t * CLK_NS}\n" + "".join(f"{v}{i}\n" for i, v in changes))
                    prev.update({n: v[t] for n, v in sigs.items()})
            f.write(f"#{len(b.cs) * CLK_NS}\n")
        res = {}
        for ann in ("mosi-data", "miso-data"):
            out = subprocess.run(
                ["sigrok-cli", "-i", path, "-I", f"vcd:samplerate={int(1e9 / CLK_NS)}",
                 "-P", f"spi:clk=sck:mosi=mosi:miso=miso:cs=cs:cpol={CPOL}:cpha={CPHA}",
                 "-A", f"spi={ann}"], capture_output=True, text=True, check=True).stdout
            res[ann] = [int(line.split()[-1], 16) for line in out.splitlines() if line.strip()]
    return res


def check_waveform(b, transactions, responses):
    assert idle_ok(b.cs, b.sck, CPOL), "SCK not at its idle level while CS is high"
    dec = decode(b.cs, b.sck, b.mosi, b.miso, CPOL, CPHA)
    assert [[m for m, _ in t] for t in dec] == transactions
    flat_resp = [responses[i % len(responses)] for i in range(sum(map(len, transactions)))]
    assert [x for t in dec for _, x in t] == flat_resp
    sr = sigrok_decode(b)
    if sr is not None:
        assert sr["mosi-data"] == [x for t in transactions for x in t], f"sigrok mosi {sr}"
        assert sr["miso-data"] == flat_resp, f"sigrok miso {sr}"


@cocotb.test()
async def test_two_transactions(dut):
    await reset(dut)
    resp = [0x5A, 0xC3, 0x0F]
    b = Bench(dut, resp)
    cocotb.start_soon(b.run())
    tx = [[0xA5, 0x00, 0xFF], [0x3C]]
    for t in tx:
        await send(dut, t)
    await settle(dut, 40 * HALF)
    assert b.tgt.transactions == tx
    assert b.host_rx == [resp[i % 3] for i in range(4)]
    check_waveform(b, tx, resp)


@cocotb.test()
async def test_host_stalls_between_bytes(dut):
    await reset(dut)
    resp = [0x81, 0x7E]
    b = Bench(dut, resp)
    cocotb.start_soon(b.run())
    tx = [[0x12, 0x34, 0x56]]
    await send(dut, tx[0], stall=7 * HALF)
    await settle(dut, 40 * HALF)
    assert b.tgt.transactions == tx, "CS must stay low while the host stalls"
    assert b.host_rx == [0x81, 0x7E, 0x81]
    check_waveform(b, tx, resp)


@cocotb.test()
async def test_random_bytes(dut):
    await reset(dut)
    rng = random.Random(CPOL * 2 + CPHA)
    resp = [rng.randrange(256) for _ in range(5)]
    b = Bench(dut, resp)
    cocotb.start_soon(b.run())
    tx = [[rng.randrange(256) for _ in range(rng.randrange(1, 5))] for _ in range(3)]
    for t in tx:
        await send(dut, t)
    await settle(dut, 40 * HALF)
    assert b.tgt.transactions == tx
    check_waveform(b, tx, resp)


@cocotb.test()
async def test_overrun_keeps_first_byte(dut):
    await reset(dut)
    b = Bench(dut, [0x11, 0x22])
    b.take_rx = False
    cocotb.start_soon(b.run())
    await send(dut, [0xAA, 0xBB])
    await settle(dut, 40 * HALF)
    assert int(dut.h_rvalid.value) == 1 and int(dut.h_rdata.value) == 0x11
    assert int(dut.h_status.value) & 0b10, "overrun not set"
