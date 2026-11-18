"""Recovery contracts on the independent model; incomplete-byte cases only."""
import pytest
import tripc
from kernels import PROGRAMS
from protomodels.i2c_recovery import RecoveryController
from tripsim import Chip


@pytest.mark.parametrize('kind,bits,clear',
    [(kind, bits, False) for kind in ('address', 'write') for bits in range(7)] +
    [('read', bits, True) for bits in range(8)])
def test_interrupted_i2c_recovers(kind, bits, clear):
    ctrl = RecoveryController(kind, bits, clear)
    chip = Chip(lanes=2)
    image, _ = tripc.compile_file(PROGRAMS / 'i2c_target_eeprom.trw')
    tripc.load(chip, image)
    for _ in range(100_000):
        _, outputs, enables = chip.outputs()
        assert not (outputs & enables & 1), 'SDA driven high'
        assert not (enables & 2), 'Target drove SCL'
        scl = ctrl.scl
        sda = int(ctrl.sda and not (enables & 1 and not (outputs & 1)))
        chip.uio_in = 0xFC | scl << 1 | sda
        chip.step()
        ctrl.step(scl, sda)
        if ctrl.done():
            break
    ctrl.check_recovered()
