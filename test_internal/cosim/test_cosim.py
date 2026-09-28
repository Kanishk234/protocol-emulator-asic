"""Co-simulation: the UART as a bitstream on the chip's fabric (uart16, loaded through the host
pins) against the same design's source RTL (protocols/uart, same parameters), in one simulation.

- TX: the same byte is given to both (the chip over the host channel, the RTL on h_w*); the two
  TX lines must be identical sample for sample from their start bits on (bit timing included).
- RX: the same frames drive both RX pins in the same clock; the bytes and flags each delivers
  must be equal; the chip's shell adds its input synchronizer, so only values are compared.
"""

import random
import sys
from pathlib import Path

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "test"))
from test_bitstream import (bit, ch_recv, ch_send, load_and_run, leave_fabric,  # noqa: E402
                            UART_DIV)
from warp_host import reset  # noqa: E402

N = 10 * UART_DIV


@cocotb.test()
async def test_uart_rtl_vs_fabric(dut):
    host = await reset(dut)
    dut.ref_rst_n.value = 0
    dut.ref_rx.value = 1
    dut.ref_h_wvalid.value = 0
    dut.ref_h_wdata.value = 0
    dut.ref_h_rready.value = 1
    await ClockCycles(dut.clk, 3)
    dut.ref_rst_n.value = 1
    host.set_fab_in(1)
    await load_and_run(host, "uart16")
    rng = random.Random(3)

    # ---- TX: waveform equality from the start bit
    for b in (0x00, 0xFF, 0xA5, rng.randrange(256)):
        chip, ref = [], []
        stop = [False]

        async def rec():
            while not stop[0]:
                await RisingEdge(dut.clk)
                chip.append(bit(dut.uo_out, 2))
                ref.append(int(dut.ref_tx.value))
        r = cocotb.start_soon(rec())
        dut.ref_h_wdata.value = b
        dut.ref_h_wvalid.value = 1
        while True:
            await RisingEdge(dut.clk)
            if int(dut.ref_h_wready.value):
                break
        dut.ref_h_wvalid.value = 0
        await ch_send(host, b)
        await ClockCycles(dut.clk, N + 4 * UART_DIV)
        stop[0] = True
        await r
        c0, r0 = chip.index(0), ref.index(0)
        assert chip[c0:c0 + N] == ref[r0:r0 + N], f"TX waveform differs for {b:#04x}"

    # ---- RX: the same frames into both
    sent = [rng.randrange(256) for _ in range(6)]
    for b in sent:
        ref_got = []
        for level in [0] + [(b >> i) & 1 for i in range(8)] + [1]:
            host.set_fab_in(level)
            dut.ref_rx.value = level
            for _ in range(UART_DIV):
                await RisingEdge(dut.clk)
                if int(dut.ref_h_rvalid.value):
                    ref_got.append(int(dut.ref_h_rdata.value))
        for _ in range(3 * UART_DIV):
            await RisingEdge(dut.clk)
            if int(dut.ref_h_rvalid.value):
                ref_got.append(int(dut.ref_h_rdata.value))
        chip_got = await ch_recv(host)
        assert ref_got == [b] and chip_got == b, (hex(b), ref_got, chip_got)
    await leave_fabric(dut)
