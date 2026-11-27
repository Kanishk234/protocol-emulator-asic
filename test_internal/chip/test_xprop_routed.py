"""Opt-in gate-level check using a generated monitor of routed flop outputs."""
import cocotb
from cocotb.triggers import ClockCycles, ReadOnly

from chiplib import HM, load, start


@cocotb.test()
@cocotb.parametrize(program=['uart', 'spi_controller', 'i2c_controller'])
async def xprop_after_firmware_load(dut, program):
    pins = await start(dut, ui=1, uio=0xff)
    if program != 'uart':
        # Exercise both ends of the SRAM address space through the SPI host.
        for offset, word in ((0, 0xa659), (511, 0x59a6)):
            await pins.write(HM['sram'] + offset, [word])
            assert await pins.read(HM['sram'] + offset) == [word]
    await load(pins, program)
    await ClockCycles(dut.clk, 32)
    observed = ('uo_out', 'uio_out', 'uio_oe', 'routed_flops')
    for offset in range(16):
        await ClockCycles(dut.clk, 1)
        await ReadOnly()
        unknown = [name for name in observed if not getattr(dut, name).value.is_resolvable]
        assert not unknown, f'Unknown outputs at post-load sample {offset}: {unknown}'
