"""Same-job triggered fault bitstream, actual shell load, chip-port observations."""
import os
from pathlib import Path

import cocotb
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge, Timer

from compile.bitfile import BitFile
from host.protocol import (Op, State, checked_load_transactions, parse_byte,
                           parse_read_id, tx_read_id, tx_simple, tx_user_status)
from test_bitstream import REAL_FABRIC, hold_x, leave_fabric, settle_routing_loops
from warp_host import bit, expect, parked, reset


async def capture_window(dut, host, busy_edge=False, held=False, monitor=False):
    """Cycle zero is the first external-trigger sampling edge, before shell synchronization."""
    low_cycles = []
    for cycle in range(28):
        trigger = cycle == 0 or (busy_edge and cycle == 4) or held
        event = monitor and cycle == 7
        await FallingEdge(dut.clk)
        host.set_fab_in(1 | (int(event) << 1) | (int(trigger) << 2))
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        if bit(dut.uo_out, 2) == 0:
            low_cycles.append(cycle)
    # Two synchronizer flops then user edge acceptance: acceptance at index2;
    # user inversion is at indices6..9; ARCHITECTURE §6 output register
    # adds one clock before chip-port observation: indices7..10. Idle UART is high.
    assert low_cycles == [7, 8, 9, 10], f"wrong delayed inversion schedule: {low_cycles}"
    await FallingEdge(dut.clk)
    host.set_fab_in(1)
    await ClockCycles(dut.clk, 6)


@cocotb.test(skip=not REAL_FABRIC)
async def test_triggered_fault_loaded(dut):
    path = Path(os.environ["WARP_TRIGGER_BITFILE"]).resolve()
    assert path.is_file(), f"missing same-job trigger bitstream {path}"
    bf = BitFile.load(path)
    host = await reset(dut)
    host.set_fab_in(1)  # UART RX idle high; event and trigger low
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
    assert bit(dut.uo_out, 2) == 1
    assert parse_byte(await host.xfer(tx_user_status())) >> 4 == 0

    # Busy retrigger must not restart/extend the inversion. Independent monitor
    # sees one event edge while inversion is active, observable through SPI.
    await capture_window(dut, host, busy_edge=True, monitor=True)
    assert parse_byte(await host.xfer(tx_user_status())) >> 4 == 1
    # Held-high trigger must generate one bounded window, not periodic faults.
    await capture_window(dut, host, held=True)
    assert parse_byte(await host.xfer(tx_user_status())) >> 4 == 1
    # A fresh edge after idle is independently accepted.
    await capture_window(dut, host)

    # USER_RESET clears monitor/history and allows another original schedule.
    # This case resets while idle; cancellation during an active window is not
    # established by this short-window loaded test.
    await host.xfer(tx_simple(Op.USER_RESET))
    await ClockCycles(dut.clk, 8)
    assert parse_byte(await host.xfer(tx_user_status())) >> 4 == 0
    assert bit(dut.uo_out, 2) == 1
    await capture_window(dut, host, monitor=True)
    assert parse_byte(await host.xfer(tx_user_status())) >> 4 == 1
    await host.xfer(tx_simple(Op.STOP))
    await expect(host, State.LOADED)
    assert parked(dut)
    await leave_fabric(dut)
