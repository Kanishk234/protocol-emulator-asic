"""Required protocols through the Tiny Tapeout ports, shared by RTL and official GL.

Use the same reviewed firmware/reference-model/sigrok cases as routed replay.
No internal design signals are accessed; tb supplies only pad wiring/loopback.
"""
import sys
from pathlib import Path
import cocotb
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"test_internal/chip"))
import test_l3 as protocol_cases

@cocotb.test()
async def test_uart(dut):
    await protocol_cases.test_l3_uart_tx.func(dut)

@cocotb.test()
async def test_spi(dut):
    await protocol_cases.test_l3_spi_controller.func(dut)

@cocotb.test()
async def test_i2c(dut):
    await protocol_cases.test_l3_i2c_controller.func(dut)
