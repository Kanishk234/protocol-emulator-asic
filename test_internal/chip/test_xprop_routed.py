"""Opt-in gate-level check using a generated monitor of routed flop outputs."""
import cocotb
from cocotb.triggers import ClockCycles, ReadOnly

from chiplib import load, start


@cocotb.test()
async def xprop_after_firmware_load(dut):
    pins = await start(dut, ui=1)
    await load(pins, 'uart', BAUD=115200)
    await ClockCycles(dut.clk, 32)
    observed = ('uo_out', 'uio_out', 'uio_oe', 'routed_flops')
    for offset in range(16):
        await ClockCycles(dut.clk, 1)
        await ReadOnly()
        unknown = [name for name in observed if not getattr(dut, name).value.is_resolvable]
        assert not unknown, f'Unknown outputs at post-load sample {offset}: {unknown}'
