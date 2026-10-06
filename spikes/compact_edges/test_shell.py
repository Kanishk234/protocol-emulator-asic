"""Real SPI loading and UART pins on the compact 5 x 3 shell candidate."""

import os
from pathlib import Path
import sys

import cocotb
from cocotb.triggers import ClockCycles, Timer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "test"))
from warp_host import bit, expect, parked, reset
from host.protocol import Op, State, parse_byte, tx_ch_read, tx_ch_write, tx_simple


@cocotb.test()
async def load_uart_through_shell(dut):
    host = await reset(dut)
    host.set_fab_in(1)
    words = [int(line, 16) for line in Path(os.environ["WARP_COMPACT_WORDS"]).read_text().split()]
    # D-023: hold unused combinational routing at X during load, then settle
    # it with a brief pulse. Configuration latches and user state are excluded.
    dut.hold_x.value = 1
    await Timer(2, unit="ns")
    if os.environ.get("WARP_COMPACT_SHARED_CRC") == "1":
        sys.path.insert(0, str(ROOT / "test_internal"))
        from shared_crc_probe import monitor_word_stability
        crc_stats = {"checked_cycles": 0}
        cocotb.start_soon(monitor_word_stability(dut, crc_stats))
    await host.load(words, arch_version=0x00F3, chunk=16)
    await expect(host, State.LOADED)
    if os.environ.get("WARP_COMPACT_SHARED_CRC") == "1":
        assert crc_stats["checked_cycles"] >= 32 * len(words)
        dut._log.info("CRC input stable for %d checked processing cycles", crc_stats["checked_cycles"])
    assert parked(dut)
    dut.hold_x.value = 0
    await Timer(2, unit="ns")
    dut.settle_routing.value = 1
    await Timer(2, unit="ns")
    dut.settle_routing.value = 0
    await Timer(2, unit="ns")
    if os.environ.get("WARP_COMPACT_DIAG") == "1":
        sys.path.insert(0, str(ROOT / "test_internal"))
        from compact_gate_probe import report_loaded_config
        report_loaded_config(dut, words)
        from compact_gate_probe import report_runtime
        report_runtime(dut, "before RUN")
    await host.xfer(tx_simple(Op.RUN))
    await expect(host, State.RUNNING)
    if os.environ.get("WARP_COMPACT_DIAG") == "1":
        from compact_gate_probe import report_runtime
        report_runtime(dut, "after RUN")
    if os.environ.get("WARP_COMPACT_RESET_PROBE") == "1":
        await host.xfer(tx_simple(Op.USER_RESET))
        await ClockCycles(dut.clk, 32)
        if os.environ.get("WARP_COMPACT_DIAG") == "1":
            report_runtime(dut, "after USER_RESET")

    samples = []

    async def record():
        for _ in range(4000):
            await ClockCycles(dut.clk, 1)
            samples.append(bit(dut.uo_out, 2))

    capture = cocotb.start_soon(record())
    sent = [0x55, 0x00, 0xC3]
    for byte in sent:
        await host.xfer(tx_ch_write(byte))
    await capture
    decoded, offset = [], 0
    while offset + 160 < len(samples):
        if samples[offset] == 0:
            middle = offset + 8
            assert samples[middle] == 0
            decoded.append(sum(samples[middle + 16 * (i + 1)] << i for i in range(8)))
            assert samples[middle + 16 * 9] == 1, "invalid UART stop bit"
            offset = middle + 16 * 9
        else:
            offset += 1
    assert decoded == sent, (decoded, sent)

    received = 0x69
    host.set_fab_in(0)
    await ClockCycles(dut.clk, 16)
    for i in range(8):
        host.set_fab_in((received >> i) & 1)
        await ClockCycles(dut.clk, 16)
    host.set_fab_in(1)
    await ClockCycles(dut.clk, 32)
    assert (await host.status()).rx_valid
    assert parse_byte(await host.xfer(tx_ch_read())) == received
    await host.xfer(tx_simple(Op.STOP))
    await expect(host, State.LOADED)
    assert parked(dut)
    dut._log.info("Loaded %d real words through SPI; UART TX/RX and STOP parking pass", len(words))
