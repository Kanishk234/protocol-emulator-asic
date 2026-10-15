"""Cancel a long autonomous window through actual SPI, on frozen fabric RTL."""
import os
from pathlib import Path
import cocotb
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge, Timer
from compile.bitfile import BitFile
from host.protocol import Op, State, checked_load_transactions, parse_read_id, tx_read_id, tx_simple
from test_bitstream import REAL_FABRIC, hold_x, leave_fabric, settle_routing_loops
from warp_host import bit, expect, parked, reset


async def pulse(dut, host):
    await FallingEdge(dut.clk)
    host.set_fab_in(5)  # idle RX plus trigger
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    host.set_fab_in(1)


async def idle_for(dut, cycles):
    for _ in range(cycles):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert bit(dut.uo_out, 2) == 1, "cancelled window resumed or retriggered"


@cocotb.test(skip=not REAL_FABRIC)
async def test_active_window_cancel_loaded(dut):
    bf = BitFile.load(Path(os.environ["WARP_TRIGGER_BITFILE"]))
    host = await reset(dut)
    host.set_fab_in(1)
    ok, chip_arch = parse_read_id(await host.xfer(tx_read_id()))
    assert ok
    hold_x(dut, True)
    await Timer(1, unit="ns")
    for transaction in checked_load_transactions(bf.words, bf.arch_version, chip_arch, chunk=16):
        await host.xfer(transaction)
    await expect(host, State.LOADED)
    assert parked(dut)
    hold_x(dut, False)
    await Timer(1, unit="ns")
    await settle_routing_loops(dut)
    await host.xfer(tx_simple(Op.RUN))
    await expect(host, State.RUNNING)
    await ClockCycles(dut.clk, 8)

    for command in (Op.USER_RESET, Op.STOP):
        await pulse(dut, host)
        await ClockCycles(dut.clk, 12)
        await Timer(1, unit="ns")
        assert bit(dut.uo_out, 2) == 0, "long fault window was not active before command"
        # The one-byte command takes80 clocks; the256-clock window must still
        # be active absent cancellation. No status transaction precedes this check.
        await host.xfer(tx_simple(command))
        await ClockCycles(dut.clk, 5)
        await Timer(1, unit="ns")
        if command == Op.STOP:
            assert parked(dut), "STOP did not park active output"
            await expect(host, State.LOADED)
            await host.xfer(tx_simple(Op.RUN))
        else:
            assert bit(dut.uo_out, 2) == 1, "USER_RESET did not cancel active fault"
        await idle_for(dut, 300)
        await expect(host, State.RUNNING)

    # A new edge after both cancellations must produce the original complete
    #256-clock window, proving recovery rather than permanent output disabling.
    low = []
    for cycle in range(280):
        await FallingEdge(dut.clk)
        host.set_fab_in(5 if cycle == 0 else 1)
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        if bit(dut.uo_out, 2) == 0:
            low.append(cycle)
    assert low == list(range(7, 263)), f"wrong fresh window after cancellation: {low}"
    await host.xfer(tx_simple(Op.STOP))
    assert parked(dut)
    await leave_fabric(dut)
