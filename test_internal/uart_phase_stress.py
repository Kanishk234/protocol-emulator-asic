"""Real-loader UART phase/read-delay stress on frozen G1; no physical claims."""
import hashlib
import json
import os
from pathlib import Path
import random

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge, Timer

from test_bitstream import BITS, UART_DIV, ch_recv, leave_fabric, load_and_run
from warp_host import expect, parked, reset
from host.protocol import Op, State, parse_byte, tx_simple, tx_user_status


@cocotb.test()
async def uart_phase_and_read_delay(dut):
    assert os.environ.get("WARP_FABRIC") == "rtl", "Real fabric required"
    output = Path(os.environ["WARP_PHASE_OUT"])
    trace = {"scope": "frozen_G1_SPI_loaded_RTL_function_only",
             "bitfile_sha256": hashlib.sha256((BITS / "uart16.wbit").read_bytes()).hexdigest(),
             "physical_or_timing_acceptance": False, "cases": [], "passed": False}
    host = await reset(dut)
    host.set_fab_in(1)
    try:
        await load_and_run(host, "uart16")
        for seed in (11, 20261007, 0x57415250):
            rng = random.Random(seed)
            values = [0, 255, 0x55, 0xAA, 1, 0x80, 0xFE, 0x7F]
            values += [rng.randrange(256) for _ in range(8)]
            for index, sent in enumerate(values):
                phases = ([1] * 10 if index == 0 else [19] * 10 if index == 1
                          else [rng.randrange(1, 20) for _ in range(10)])
                delay = rng.randrange(0, 8 * UART_DIV + 1)
                case = {"seed": seed, "index": index, "sent": sent,
                        "edge_phases_ns": phases, "read_delay_clocks": delay}
                trace["cases"].append(case)
                for level, phase in zip([0] + [(sent >> bit) & 1 for bit in range(8)] + [1], phases):
                    await RisingEdge(dut.clk)
                    await Timer(phase, "ns")
                    host.set_fab_in(level)
                    await ClockCycles(dut.clk, UART_DIV - 1)
                await ClockCycles(dut.clk, 2 * UART_DIV + delay)
                status = await host.status()
                case["rx_valid_before_read"] = status.rx_valid
                assert status.rx_valid, f"Missing byte: {case}"
                received = await ch_recv(host)
                case["received"] = received
                assert received == sent, f"Byte mismatch: {case}"
                assert not (await host.status()).rx_valid, f"Duplicate/stale byte: {case}"
                flags = parse_byte(await host.xfer(tx_user_status()))
                case["user_status"] = flags
                assert flags & 0x06 == 0, f"Overrun/framing error: {case}"
        await host.xfer(tx_simple(Op.USER_RESET))
        await ClockCycles(dut.clk, 8)
        assert not (await host.status()).rx_valid
        await host.xfer(tx_simple(Op.STOP))
        await expect(host, State.LOADED)
        assert parked(dut)
        await leave_fabric(dut)
        trace["passed"] = True
        dut._log.info("48 SPI-loaded UART RX bytes pass three seeds, boundary phases and read delays")
    except Exception as failure:
        trace["failure"] = str(failure)
        raise
    finally:
        output.mkdir(parents=True, exist_ok=True)
        (output / "phase_trace.json").write_text(json.dumps(trace, indent=2) + "\n")
