"""Real loaded UART plus bounded event capture, checked through top ports."""
import os
from pathlib import Path

import cocotb
from cocotb.triggers import ClockCycles

import test_bitstream as bs
from warp_host import bit, reset
from host.protocol import Op, parse_byte, tx_ch_read, tx_ch_write, tx_simple, tx_user_status


@cocotb.test()
async def test_loaded_uart_capture(dut):
    image = Path(os.environ["WARP_UART_CAPTURE_BITFILE"]).resolve()
    tick = 1 << int(os.environ.get("WARP_UART_CAPTURE_STAMP_SHIFT", "0"))
    assert tick in (1, 4), "loaded test covers the unscaled and divide-by-four images"
    bs.BITS = image.parent
    host = await reset(dut)
    host.set_fab_in(1)
    await bs.load_and_run(host, image.stem)
    wave = []
    done = [False]

    async def observe():
        while not done[0]:
            await ClockCycles(dut.clk, 1)
            wave.append(bit(dut.uo_out, 2))

    async def pulse(base=1, low=24):
        host.set_fab_in(base | 2)
        await ClockCycles(dut.clk, 8)
        host.set_fab_in(base)
        await ClockCycles(dut.clk, low)

    async def during_tx():
        for _ in range(4000):
            if not bit(dut.uo_out, 2):
                break
            await ClockCycles(dut.clk, 1)
        else:
            raise AssertionError("UART never started")
        for _ in range(3):
            await pulse()

    recorder = cocotb.start_soon(observe())
    producer = cocotb.start_soon(during_tx())
    await host.xfer(tx_ch_write(0x55))
    await producer
    await ClockCycles(dut.clk, 200)
    done[0] = True
    await recorder
    start = wave.index(0)
    mid = start + 8
    assert sum(wave[mid + (k + 1) * 16] << k for k in range(8)) == 0x55
    assert wave[mid + 9 * 16] == 1
    assert parse_byte(await host.xfer(tx_user_status())) == 0xE0

    # Selecting capture drains it automatically into the shell RX FIFO.
    host.set_fab_in(5)
    await ClockCycles(dut.clk, 16)
    assert parse_byte(await host.xfer(tx_user_status())) == 0x80
    assert (await host.status()).rx_valid
    first = parse_byte(await host.xfer(tx_ch_read()))
    second = parse_byte(await host.xfer(tx_ch_read()))
    assert first < 64 and second < 64
    assert (second - first) % 64 == 32 // tick
    assert not (await host.status()).rx_valid, "overflow event was queued instead of dropped"

    # Refill and wrap both queue pointers and the timestamp counter.
    # Separation68 timestamp ticks gives a modular difference of4.
    host.set_fab_in(1)
    await ClockCycles(dut.clk, 16)
    await pulse(low=68 * tick - 8)
    await pulse()
    assert parse_byte(await host.xfer(tx_user_status())) == 0xE0
    host.set_fab_in(5)
    await ClockCycles(dut.clk, 16)
    first = parse_byte(await host.xfer(tx_ch_read()))
    second = parse_byte(await host.xfer(tx_ch_read()))
    assert (second - first) % 64 == 4
    assert not (await host.status()).rx_valid
    await host.xfer(tx_simple(Op.USER_RESET))
    await ClockCycles(dut.clk, 12)
    assert parse_byte(await host.xfer(tx_user_status())) == 0

    # A13-clock interval straddles a fractional prescaled tick. Either adjacent
    # quantized difference is valid; this catches accidental event decimation.
    host.set_fab_in(1)
    await ClockCycles(dut.clk, 16)
    await pulse(low=5)
    await pulse()
    host.set_fab_in(5)
    await ClockCycles(dut.clk, 16)
    first = parse_byte(await host.xfer(tx_ch_read()))
    second = parse_byte(await host.xfer(tx_ch_read()))
    assert (second - first) % 64 in {13 // tick, (13 + tick - 1) // tick}
    assert not (await host.status()).rx_valid
    await host.xfer(tx_simple(Op.USER_RESET))
    await ClockCycles(dut.clk, 12)

    # Keep capture selected and withhold host reads: the shell's specified
    # two-entry RX FIFO fills, then the two soft entries absorb two more.
    # Unequal intervals distinguish preserved order from a drop-oldest policy.
    for low in (8, 16, 24, 32, 8):
        await pulse(base=5, low=low)
    assert parse_byte(await host.xfer(tx_user_status())) == 0xE0
    buffered = [parse_byte(await host.xfer(tx_ch_read())) for _ in range(4)]
    assert [(b-a) % 64 for a, b in zip(buffered, buffered[1:])] == [n // tick for n in (16, 24, 32)]
    assert not (await host.status()).rx_valid
    assert parse_byte(await host.xfer(tx_user_status())) == 0x80
    await host.xfer(tx_simple(Op.USER_RESET))
    await ClockCycles(dut.clk, 12)
    assert parse_byte(await host.xfer(tx_user_status())) == 0

    # Normal UART RX remains usable after changing streams and draining data.
    host.set_fab_in(1)
    await ClockCycles(dut.clk, 12)
    for level in [0] + [(0xA5 >> k) & 1 for k in range(8)] + [1]:
        host.set_fab_in(level)
        await ClockCycles(dut.clk, 16)
    await ClockCycles(dut.clk, 64)
    assert (await host.status()).rx_valid
    assert parse_byte(await host.xfer(tx_ch_read())) == 0xA5
    await host.xfer(tx_simple(Op.STOP))
    await ClockCycles(dut.clk, 12)
    assert bit(dut.uo_out, 2) == 0 and int(dut.uio_oe.value) == 0
    await bs.leave_fabric(dut)
