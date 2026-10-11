"""Helper compilation -> real SPI configuration -> observable fabric behavior.

Set WARP_HELPER_BITFILE to the helper_demo.wbit produced by this CI job.
All behavior observations use chip ports. Existing loader utilities retain the
standard simulation-only routing settling accommodations (D-023).
"""
import os
from pathlib import Path

import cocotb
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge, Timer

from compile.bitfile import BitFile
from host.protocol import (Op, State, checked_load_transactions, parse_read_id,
                           tx_read_id, tx_simple)
from test_bitstream import (REAL_FABRIC, fab_out, hold_x, leave_fabric,
                           settle_routing_loops)
from warp_host import expect, parked, reset


async def sample_edge(dut):
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    return fab_out(dut)


async def request_step(dut, host, expected_bit, final):
    # Drive on the falling edge, leaving a full half-cycle before the chip's
    # synchronizer. Request stays high for exactly one source clock cycle.
    await FallingEdge(dut.clk)
    host.set_fab_in(1)  # request=1, rx=0
    await sample_edge(dut)
    await FallingEdge(dut.clk)
    host.set_fab_in(0)
    ticks = []
    completions = []
    for cycle in range(12):
        value = await sample_edge(dut)
        if value & 8:  # tick is pre-shift terminal condition at this sampling edge
            ticks.append(cycle)
            assert value & 1 == expected_bit, "wrong outgoing bit before delayed shift"
        if value & 4:
            completions.append(cycle)
    assert len(ticks) == 1, f"one request must produce one delayed step: {ticks}"
    assert len(completions) == int(final), f"completion pulses: {completions}"
    assert bool(fab_out(dut) & 2) == final, "ready must return only after final step"
    if final:
        assert completions[0] == ticks[0] + 1, "complete must follow the terminal shift"


@cocotb.test(skip=not REAL_FABRIC)
async def test_helpers_loaded_through_shell(dut):
    bitfile = Path(os.environ["WARP_HELPER_BITFILE"]).resolve()
    assert bitfile.is_file(), f"missing same-job helper bitstream {bitfile}"
    bf = BitFile.load(bitfile)
    host = await reset(dut)
    host.set_fab_in(0)
    ok, chip_arch = parse_read_id(await host.xfer(tx_read_id()))
    assert ok
    hold_x(dut, True)
    await Timer(1, unit="ns")
    for transaction in checked_load_transactions(bf.words, bf.arch_version, chip_arch, chunk=16):
        await host.xfer(transaction)
    await expect(host, State.LOADED)
    assert parked(dut), "loaded fabric must remain parked before RUN"
    hold_x(dut, False)
    await Timer(1, unit="ns")
    await settle_routing_loops(dut)
    await host.xfer(tx_simple(Op.RUN))
    await expect(host, State.RUNNING)
    await ClockCycles(dut.clk, 6)
    assert fab_out(dut) == 2, "reset leaves shifter empty and ready, timer idle"

    # MSB-first A5 transmission, one delayed shift per request. Later requests
    # must not reload the busy shifter. Incoming zeros leave serial=0 at the end.
    for index in range(8):
        await request_step(dut, host, (0xA5 >> (7 - index)) & 1, index == 7)
    assert fab_out(dut) == 2

    # Start a new transfer, then cancel it using the actual shell command.
    await request_step(dut, host, 1, False)
    await host.xfer(tx_simple(Op.USER_RESET))
    await ClockCycles(dut.clk, 6)
    assert fab_out(dut) == 2, "USER_RESET cancels busy and clears serial data"
    # Reloading after USER_RESET must reproduce the original word.
    await request_step(dut, host, 1, False)
    await host.xfer(tx_simple(Op.STOP))
    await expect(host, State.LOADED)
    assert parked(dut), "STOP must park every fabric output and output enable"
    await leave_fabric(dut)
