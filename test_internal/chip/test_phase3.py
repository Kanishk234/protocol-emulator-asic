"""Phase 3 firmware showcases through chip pins; also runnable on the official gate netlist."""
import cocotb
from cocotb.triggers import ClockCycles

from chiplib import Wire, hex_bytes, load, sigrok, start, write_vcd
from protomodels.i2c_memory import MemoryController, check_result, exercise
from protomodels.i2c_recovery import RecoveryController


async def memory_scenarios(dut, program, clock=True):
    """SRAM-backed memory: page writes, repeated START, pointer/wrap, NACK and ACK setup."""
    for index, (clocks_per_bit, high_clocks) in enumerate(((125, 60), (50, 25), (50, 13))):
        p = await start(dut, uio=0xFF, clock=clock and index == 0)
        image = await load(p, program)
        assert len(image['sram']) == 304
        ctrl = MemoryController(clocks_per_bit, high_clocks)
        expected = exercise(ctrl)

        def environment(uo, outputs, enables, bus):
            assert not (enables & outputs & 1), 'Open-drain SDA actively driven high'
            assert not (enables & 2), 'Target must never drive SCL'
            scl, sda = ctrl.step(bus >> 1 & 1, bus & 1)
            return {}, {0: sda, 1: scl}

        wire = Wire(p, environment, {'scl': lambda uo, bus: bus >> 1 & 1,
                                     'sda': lambda uo, bus: bus & 1})
        try:
            for _ in range(clocks_per_bit * 15 + 100):
                if ctrl.done():
                    break
                await ClockCycles(dut.clk, 100)
            assert ctrl.done(), 'Memory transactions did not complete'
            setup = check_result(ctrl, expected)
            dut._log.info('I2C memory %d clocks/bit: minimum observed ACK setup %d clocks (%d ns)',
                          clocks_per_bit, setup, setup * 20)
        finally:
            wire.stop()
        path = f'i2c_memory_{clocks_per_bit}_{high_clocks}.vcd'
        write_vcd(path, wire.rec)
        decoded = sigrok(path, 'i2c:scl=scl:sda=sda', 'i2c')
        assert decoded is not None, 'Independent sigrok decode is required for this showcase'
        assert hex_bytes(decoded, 'Data read: ') == expected, decoded
    return p


async def recovery_scenarios(dut, program, cases, clock=True, pins=None):
    """Pin-only abort/bus-clear checks, also usable with the official netlist."""
    for index, case in enumerate(cases):
        if pins is None:
            p = await start(dut, uio=0xFF, clock=clock and index == 0)
            await load(p, program)
        else:
            p = pins
        ctrl = RecoveryController(*case)

        def environment(uo, outputs, enables, bus):
            assert not (enables & outputs & 1), 'SDA actively driven high'
            assert not (enables & 2), 'Target drove SCL'
            scl, sda = ctrl.step(bus >> 1 & 1, bus & 1)
            return {}, {0: sda, 1: scl}

        wire = Wire(p, environment, {'scl': lambda uo, bus: bus >> 1 & 1,
                                     'sda': lambda uo, bus: bus & 1})
        try:
            for _ in range(1000):
                if ctrl.done():
                    break
                await ClockCycles(dut.clk, 100)
            ctrl.check_recovered()
        finally:
            wire.stop()
        path = f'{program}_recovery_{index}.vcd'
        write_vcd(path, wire.rec)
        # Decode the subsequent complete transaction from its idle preamble.
        # The decoder retains byte framing across a mid-byte STOP in the full
        # malformed trace. Preserve that trace; do not treat it as read data.
        verify_path = f'{program}_recovery_{index}_verify.vcd'
        offset = ctrl.verify_start_clock - 1
        if not ctrl.restart:
            assert all(wire.rec[name][offset] == 1 for name in ('scl', 'sda'))
        write_vcd(verify_path, {name: samples[offset:] for name, samples in wire.rec.items()})
        decoded = sigrok(verify_path, 'i2c:scl=scl:sda=sda', 'i2c')
        assert decoded is not None, 'Recovery requires independent decode'
        assert hex_bytes(decoded, 'Data read: ') == ctrl.expected_reads, decoded


@cocotb.test()
async def test_i2c_memory_eeprom(dut):
    await memory_scenarios(dut, 'i2c_target_eeprom')


@cocotb.test()
async def test_i2c_memory_recovery(dut):
    await recovery_scenarios(dut, 'i2c_target_eeprom', [
        ('address', 6, False), ('write', 6, False),
        ('read', 0, True), ('read', 7, True)])


@cocotb.test()
async def test_i2c_memory_guard(dut):
    """Two-unit firmware variant; unchanged hardware and explicit extra pad cost."""
    pins = await memory_scenarios(dut, 'i2c_target_eeprom_guard')
    cases = [(kind, 7, False, period, high, restart, 0)
             for period, high in [(125, 60), (50, 13)]
             for kind in ('address', 'write') for restart in (False, True)]
    cases += [('read', bits, True, 50, 13, False, 0) for bits in (0, 7)]
    cases += [('write', 7, False, 50, 25, False, 0, phase) for phase in (1, 3)]
    # Run the fault sequence without host reset/reload between cases: recovery
    # must leave the firmware usable for the next real bus transaction.
    await recovery_scenarios(dut, 'i2c_target_eeprom_guard', cases, clock=False, pins=pins)
