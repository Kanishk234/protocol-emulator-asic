"""SPI-loaded UART corruption and independent monitoring through top ports."""
import os
from pathlib import Path

import cocotb
from cocotb.triggers import ClockCycles

import test_bitstream as bs
from warp_host import bit, reset
from host.protocol import Op, parse_byte, tx_ch_write, tx_simple, tx_user_status


@cocotb.test()
async def test_loaded_uart_fault_monitor(dut):
    image = Path(os.environ["WARP_UART_FAULT_BITFILE"]).resolve()
    bs.BITS = image.parent
    host = await reset(dut)
    host.set_fab_in(1)
    await bs.load_and_run(host, image.stem)

    async def transmit(inject):
        wave = []
        done = [False]

        async def observe():
            while not done[0]:
                await ClockCycles(dut.clk, 1)
                wave.append(bit(dut.uo_out, 2))

        async def controls():
            for _ in range(4000):
                if not bit(dut.uo_out, 2):
                    break
                await ClockCycles(dut.clk, 1)
            else:
                raise AssertionError("UART never started")
            # Event counting overlaps transmission. Fault pulse targets data
            # bit 1, allowing shell synchronizer/output-register latency.
            host.set_fab_in(3)
            await ClockCycles(dut.clk, 8)
            host.set_fab_in(1)
            await ClockCycles(dut.clk, 22)
            host.set_fab_in(5 if inject else 1)
            await ClockCycles(dut.clk, 16)
            host.set_fab_in(1)

        rec = cocotb.start_soon(observe())
        ctl = cocotb.start_soon(controls())
        await host.xfer(tx_ch_write(0x55))
        await ctl
        await ClockCycles(dut.clk, 200)
        done[0] = True
        await rec
        start = wave.index(0)
        mid = start + 8
        assert wave[mid] == 0
        assert wave[mid + 9 * 16] == 1, "stop bit unexpectedly corrupted"
        value = sum(wave[mid + (k + 1) * 16] << k for k in range(8))
        assert value == (0x57 if inject else 0x55), hex(value)
        assert wave[-1] == 1, "TX failed to recover to idle"

    await transmit(False)
    await transmit(True)
    await transmit(False)
    assert parse_byte(await host.xfer(tx_user_status())) == 0x30
    # A held-high fault control inverts idle; STOP must still park the pin.
    host.set_fab_in(5)
    await ClockCycles(dut.clk, 12)
    assert bit(dut.uo_out, 2) == 0
    host.set_fab_in(1)
    await ClockCycles(dut.clk, 12)
    assert bit(dut.uo_out, 2) == 1
    await host.xfer(tx_simple(Op.USER_RESET))
    await ClockCycles(dut.clk, 12)
    assert parse_byte(await host.xfer(tx_user_status())) == 0
    host.set_fab_in(5)
    await host.xfer(tx_simple(Op.STOP))
    await ClockCycles(dut.clk, 12)
    assert bit(dut.uo_out, 2) == 0, "fault control bypassed STOP parking"
    assert int(dut.uio_oe.value) == 0
    await bs.leave_fabric(dut)
