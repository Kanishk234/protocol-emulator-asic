"""RTL tests for protocols/uart against the independent model (tools/refmodels/uart.py) and sigrok."""

import os
import random
import shutil
import subprocess
import tempfile

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, NextTimeStep, ReadOnly, RisingEdge

from refmodels.uart import Frame, decode, encode

DIV = int(os.environ.get("DIV", "16"))
RUNTIME_DIV = int(os.environ.get("RUNTIME_DIV", "0"))
CLK_NS = 20  # 50 MHz


async def reset(dut):
    cocotb.start_soon(Clock(dut.clk, CLK_NS, unit="ns").start())
    dut.rst_n.value = 0
    dut.rx_i.value = 1
    dut.h_wdata.value = 0
    dut.h_wvalid.value = 0
    dut.h_rready.value = 0
    dut.cfg_div.value = 0
    dut.cfg_we.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)


async def set_div(dut, div):
    """Runtime-divisor builds only: load a new divisor."""
    dut.cfg_div.value = div
    dut.cfg_we.value = 1
    await RisingEdge(dut.clk)
    dut.cfg_we.value = 0


async def send_bytes(dut, data):
    """Valid/ready handshake: a byte is taken at the rising edge where h_wready was 1."""
    for byte in data:
        dut.h_wdata.value = byte
        dut.h_wvalid.value = 1
        while True:
            await RisingEdge(dut.clk)
            if int(dut.h_wready.value) == 1:  # value just before this edge
                break
    dut.h_wvalid.value = 0


async def record(sig, clk, ncycles, out):
    for _ in range(ncycles):
        await RisingEdge(clk)
        await ReadOnly()
        out.append(int(sig.value))
    await NextTimeStep()  # leave the read-only phase before the caller drives again


async def drive_wave(dut, wave):
    for level in wave:
        dut.rx_i.value = level
        await RisingEdge(dut.clk)
    dut.rx_i.value = 1


async def collect_rx(dut, out, ncycles):
    """Act as a host that always takes received bytes."""
    dut.h_rready.value = 1
    for _ in range(ncycles):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.h_rvalid.value):
            out.append(int(dut.h_rdata.value))
    await NextTimeStep()


def sigrok_decode(wave, div):
    """Independent second decoder: write the TX line as a VCD and run sigrok's uart decoder."""
    if shutil.which("sigrok-cli") is None:
        return None
    baud = int(1e9 / (CLK_NS * div))
    wave = [1] * (2 * div) + list(wave)  # idle line first, so the first start bit is a 1->0 edge
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "tx.vcd")
        with open(path, "w") as f:
            f.write("$timescale 1 ns $end\n$scope module top $end\n$var wire 1 ! tx $end\n$upscope $end\n$enddefinitions $end\n")
            prev = None
            for i, level in enumerate(wave):
                if level != prev:
                    f.write(f"#{i * CLK_NS}\n{level}!\n")
                    prev = level
            f.write(f"#{len(wave) * CLK_NS}\n")
        out = subprocess.run(
            ["sigrok-cli", "-i", path, "-I", f"vcd:samplerate={int(1e9 / CLK_NS)}",
             "-P", f"uart:rx=tx:baudrate={baud}:format=hex", "-A", "uart=rx-data"],
            capture_output=True, text=True, check=True).stdout
    return [int(tok.split()[-1], 16) for tok in out.splitlines() if tok.strip()]


@cocotb.test()
async def test_tx_back_to_back(dut):
    await reset(dut)
    data = [0x00, 0xFF, 0x55, 0xA5, 0x3C, 0x81]
    wave = []
    frame_clks = 10 * DIV
    rec = cocotb.start_soon(record(dut.tx_o, dut.clk, frame_clks * len(data) + 4 * DIV, wave))
    await send_bytes(dut, data)
    await rec
    assert decode(wave, DIV) == [Frame(b, True) for b in data]
    # back to back: the last stop bit ends within one frame time of len(data) frames
    first_low = wave.index(0)
    assert wave[first_low + frame_clks * len(data):] == [1] * (len(wave) - first_low - frame_clks * len(data))
    sr = sigrok_decode(wave, DIV)
    if sr is not None:
        assert sr == data, f"sigrok decoded {sr}"


@cocotb.test()
async def test_tx_random(dut):
    await reset(dut)
    rng = random.Random(1)
    data = [rng.randrange(256) for _ in range(12)]
    wave = []
    rec = cocotb.start_soon(record(dut.tx_o, dut.clk, 10 * DIV * len(data) + 4 * DIV, wave))
    await send_bytes(dut, data)
    await rec
    assert [f.data for f in decode(wave, DIV)] == data


@cocotb.test()
async def test_rx_bytes_with_gaps(dut):
    await reset(dut)
    data = [0x00, 0xFF, 0x5A, 0x01, 0x80, 0xC3]
    wave = encode(data, DIV, idle_before=7, gap=3)
    got = []
    col = cocotb.start_soon(collect_rx(dut, got, len(wave) + 4 * DIV))
    await drive_wave(dut, wave)
    await col
    assert got == data
    assert int(dut.h_status.value) & 0b110 == 0


@cocotb.test()
async def test_rx_tolerates_baud_error(dut):
    """Sender 3 % slow and 3 % fast (rounded to whole clocks)."""
    await reset(dut)
    for cpb in (round(DIV * 1.03), round(DIV * 0.97)):
        data = [0x96, 0x69, 0xF0]
        wave = encode(data, cpb, idle_before=5)
        got = []
        col = cocotb.start_soon(collect_rx(dut, got, len(wave) + 4 * DIV))
        await drive_wave(dut, wave)
        await col
        assert got == data, f"cpb={cpb}"


@cocotb.test()
async def test_rx_framing_error(dut):
    await reset(dut)
    wave = encode([0xA5], DIV)
    wave[-DIV:] = [0] * DIV  # stop bit low
    wave += [1] * (2 * DIV)
    got = []
    col = cocotb.start_soon(collect_rx(dut, got, len(wave) + 2 * DIV))
    await drive_wave(dut, wave)
    await col
    assert int(dut.h_status.value) & 0b010, "ferr not set"


@cocotb.test()
async def test_rx_glitch_ignored(dut):
    await reset(dut)
    wave = [1] * 4 + [0] * max(1, DIV // 2 - 3) + [1] * (12 * DIV)
    got = []
    col = cocotb.start_soon(collect_rx(dut, got, len(wave)))
    await drive_wave(dut, wave)
    await col
    assert got == []


@cocotb.test()
async def test_rx_overrun_keeps_first_byte(dut):
    await reset(dut)
    dut.h_rready.value = 0
    await drive_wave(dut, encode([0x11, 0x22], DIV) + [1] * (2 * DIV))
    await ReadOnly()
    # (last statement; nothing is driven after this read)
    assert int(dut.h_rvalid.value) == 1 and int(dut.h_rdata.value) == 0x11
    assert int(dut.h_status.value) & 0b100, "overrun not set"


@cocotb.test(skip=not RUNTIME_DIV)
async def test_runtime_divisor(dut):
    await reset(dut)
    new = DIV + 7
    await set_div(dut, new)
    data = [0x3A, 0xC5]
    wave = []
    rec = cocotb.start_soon(record(dut.tx_o, dut.clk, 10 * new * len(data) + 4 * new, wave))
    await send_bytes(dut, data)
    await rec
    assert [f.data for f in decode(wave, new)] == data
    got = []
    rxw = encode([0x7E], new, idle_before=3)
    col = cocotb.start_soon(collect_rx(dut, got, len(rxw) + 4 * new))
    await drive_wave(dut, rxw)
    await col
    assert got == [0x7E]
