"""Recovery contracts on the independent model; incomplete-byte cases only."""
import pytest
import json
import tripc
from kernels import PROGRAMS
from kernels.delimiter_path import DelimiterPathMonitor
from protomodels.i2c_recovery import RecoveryController
from tripsim import Chip


@pytest.mark.parametrize('kind,bits,clear',
    [(kind, bits, False) for kind in ('address', 'write') for bits in range(7)] +
    [('read', bits, True) for bits in range(8)])
def test_interrupted_i2c_recovers(kind, bits, clear):
    ctrl = RecoveryController(kind, bits, clear)
    run_controller('i2c_target_eeprom', ctrl)


def run_controller(program, ctrl):
    chip = Chip(lanes=2)
    image, _ = tripc.compile_file(PROGRAMS / f'{program}.trw')
    tripc.load(chip, image)
    monitor = DelimiterPathMonitor(image) if program == 'i2c_target_eeprom_guard' else None
    for _ in range(ctrl.period * 1600 + 10_000):
        _, outputs, enables = chip.outputs()
        assert not (outputs & enables & 1), 'SDA driven high'
        assert not (enables & 2), 'Target drove SCL'
        scl = ctrl.scl
        sda = int(ctrl.sda and not (enables & 1 and not (outputs & 1)))
        if monitor is not None:
            monitor.sample(chip, ctrl.clocks, scl, sda)
        chip.uio_in = 0xFC | scl << 1 | sda
        chip.step()
        ctrl.step(scl, sda)
        if ctrl.done():
            break
    ctrl.check_recovered()
    assert not any(pin.flags['OVERRUN'] for pin in chip.pins)
    if monitor is not None:
        print('DELIMITER_PATH ' + json.dumps(monitor.finish(), sort_keys=True))


@pytest.mark.parametrize('period,high', [(500, 250), (125, 60), (50, 25), (50, 13)])
@pytest.mark.parametrize('kind,bits,clear,restart',
    [(kind, bits, False, False) for kind in ('address', 'write') for bits in range(8)] +
    [('read', bits, True, False) for bits in range(8)] +
    [(kind, bits, False, True) for kind in ('address', 'write') for bits in range(8)])
def test_guarded_i2c_recovers(period, high, kind, bits, clear, restart):
    ctrl = RecoveryController(kind, bits, clear, period, high,
                              restart=restart, idle_clocks=0)
    run_controller('i2c_target_eeprom_guard', ctrl)


@pytest.mark.parametrize('phase', [1, 2, 3])
@pytest.mark.parametrize('high', [25, 13])
@pytest.mark.parametrize('kind,clear,restart', [
    ('address', False, False), ('write', False, False),
    ('address', False, True), ('write', False, True), ('read', True, False)])
def test_guarded_recovery_clock_phases(phase, high, kind, clear, restart):
    ctrl = RecoveryController(kind, 7, clear, 50, high,
                              restart=restart, idle_clocks=0, initial_idle_clocks=phase)
    run_controller('i2c_target_eeprom_guard', ctrl)
