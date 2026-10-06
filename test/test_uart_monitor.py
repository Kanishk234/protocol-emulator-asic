"""Real SPI-loaded G1: UART TX while a separate input monitor runs."""
import os
from pathlib import Path

import cocotb
from cocotb.triggers import ClockCycles

import test_bitstream as bs
from warp_host import bit, reset
from host.protocol import Op, parse_byte, tx_ch_read, tx_ch_write, tx_simple, tx_user_status


@cocotb.test()
async def test_uart_and_independent_events(dut):
    image = Path(os.environ["WARP_UART_MONITOR_BITFILE"]).resolve()
    bs.BITS = image.parent
    host = await reset(dut)
    host.set_fab_in(1)
    await bs.load_and_run(host, image.stem)
    wave = []
    running = [True]

    async def record():
        while running[0]:
            await ClockCycles(dut.clk, 1)
            wave.append(bit(dut.uo_out, 2))

    async def events():
        # Wait until the UART actually transmits, then overlap 20 events.
        for _ in range(4000):
            if not bit(dut.uo_out, 2):
                break
            await ClockCycles(dut.clk, 1)
        else:
            raise AssertionError("UART did not start while monitor was armed")
        for _ in range(20):
            host.set_fab_in(3)
            await ClockCycles(dut.clk, 8)
            host.set_fab_in(1)
            await ClockCycles(dut.clk, 8)

    rec = cocotb.start_soon(record())
    ev = cocotb.start_soon(events())
    sent = [0x55, 0x00, 0xC3]
    for byte in sent:
        await host.xfer(tx_ch_write(byte))
    await ev
    await ClockCycles(dut.clk, 200)
    running[0] = False
    await rec
    decoded = []
    i = 0
    while i + 160 < len(wave):
        if wave[i] == 0:
            mid = i + 8
            assert wave[mid] == 0
            decoded.append(sum(wave[mid + (k + 1) * 16] << k for k in range(8)))
            assert wave[mid + 9 * 16] == 1, "bad UART stop bit"
            i += 160
        else:
            i += 1
    assert decoded == sent, decoded
    status = parse_byte(await host.xfer(tx_user_status()))
    assert status == 0x40, hex(status)  # 20 modulo 16, idle/error-free UART
    await host.xfer(tx_simple(Op.USER_RESET))
    await ClockCycles(dut.clk, 8)
    assert parse_byte(await host.xfer(tx_user_status())) == 0

    # Receive a complete byte while a different pin rises once per bit.
    # This exercises the independent input synchronizers and both users of
    # the same host status/data interface, without sending host SPI in parallel.
    for level in [0] + [(0xA5 >> k) & 1 for k in range(8)] + [1]:
        host.set_fab_in(level | 2)
        await ClockCycles(dut.clk, 8)
        host.set_fab_in(level)
        await ClockCycles(dut.clk, 8)
    host.set_fab_in(1)
    await ClockCycles(dut.clk, 64)
    assert (await host.status()).rx_valid
    assert parse_byte(await host.xfer(tx_ch_read())) == 0xA5
    assert parse_byte(await host.xfer(tx_user_status())) == 0xA0

    # Deliberately hold a bad stop bit low. Framing error must remain visible
    # even though the independent count occupies the upper status nibble.
    for level in [0] + [1] * 8 + [0]:
        host.set_fab_in(level)
        await ClockCycles(dut.clk, 16)
    host.set_fab_in(1)
    await ClockCycles(dut.clk, 64)
    assert parse_byte(await host.xfer(tx_ch_read())) == 0xFF
    assert parse_byte(await host.xfer(tx_user_status())) == 0xA2
    await host.xfer(tx_simple(Op.USER_RESET))
    await ClockCycles(dut.clk, 8)
    assert parse_byte(await host.xfer(tx_user_status())) == 0
    await host.xfer(tx_simple(Op.STOP))
    await bs.leave_fabric(dut)
