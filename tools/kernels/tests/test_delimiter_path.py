"""Wire-origin delimiter timing on complete memory workloads."""
import json

import pytest
import tripc
from kernels import PROGRAMS
from kernels.ack_path import AckTimingController
from kernels.delimiter_path import DelimiterPathMonitor
from protomodels.i2c_memory import exercise, check_result
from tripsim import Chip


@pytest.mark.parametrize('period,high', [(500, 250), (125, 60), (50, 25), (50, 13)])
@pytest.mark.parametrize('phase', [0, 3])
def test_wire_delimiters_to_guard_and_memory_service(period, high, phase):
    image, _ = tripc.compile_file(PROGRAMS / 'i2c_target_eeprom_guard.trw')
    chip = Chip(lanes=2)
    tripc.load(chip, image)
    ctrl = AckTimingController(period, high, phase)
    expected = exercise(ctrl)
    monitor = DelimiterPathMonitor(image, fire_period=chip.lanes[0].fire_period)
    for _ in range(period * 1600 + 10_000):
        _, outputs, enables = chip.outputs()
        assert not enables & outputs & 1 and not enables & 2
        scl = ctrl.scl
        sda = int(ctrl.sda and not (enables & 1 and not outputs & 1))
        monitor.sample(chip, ctrl.clocks, scl, sda)
        chip.uio_in = 0xFC | scl << 1 | sda
        chip.step()
        ctrl.step(scl, sda)
        if ctrl.done():
            break
    check_result(ctrl, expected)
    assert not any(p.flags['OVERRUN'] for p in chip.pins)
    print('DELIMITER_PATH ' + json.dumps(monitor.finish(), sort_keys=True))
