"""Phase 3 volatile I2C memory firmware on the independent chip model."""
import shutil
import subprocess

import pytest
import tripc
from kernels import PROGRAMS
from protomodels.i2c_memory import MemoryController, check_result, exercise
from tripsim import Chip
from tripsim.vcd import VcdRecorder


@pytest.mark.parametrize('clocks_per_bit, high_clocks', [(500, 250), (125, 60), (50, 25), (50, 13)])
@pytest.mark.parametrize('addr', [0x50, 0x2A])
def test_i2c_memory_transactions(clocks_per_bit, high_clocks, addr, tmp_path):
    image, report = tripc.compile_file(PROGRAMS / 'i2c_target_eeprom.trw', {'ADDR': addr})
    assert [len(image['lanes'][name]['slots']) for name in ['L0', 'L1']] == [12, 11]
    assert len(image['sram']) <= 512 and 'Warnings' not in report
    chip = Chip(lanes=2)
    tripc.load(chip, image)
    ctrl = MemoryController(clocks_per_bit, high_clocks)
    expected = exercise(ctrl, addr)
    rec = VcdRecorder({'scl': lambda c: c.uio_in >> 1 & 1,
                       'sda': lambda c: c.uio_in & 1})
    chip.observers.append(rec)
    for _ in range(clocks_per_bit * 1500 + 10_000):
        _, outputs, enables = chip.outputs()
        scl = int(ctrl.scl and not (enables >> 1 & 1 and not (outputs >> 1 & 1)))
        sda = int(ctrl.sda and not (enables & 1 and not (outputs & 1)))
        chip.uio_in = 0xFC | scl << 1 | sda
        chip.step()
        ctrl.step(scl, sda)
        if ctrl.done():
            break
    else:
        pytest.fail('I2C memory scenario timed out')
    setup = check_result(ctrl, expected, addr)
    assert not chip.pins[0].flags['OVERRUN']
    print(f'{clocks_per_bit=}, {high_clocks=}, {addr=:#x}, ACK setup minimum={setup} clocks')
    # Independent decode is required, not optional, for this new showcase test.
    assert shutil.which('sigrok-cli'), 'Install sigrok-cli for Phase 3 verification'
    path = tmp_path / 'i2c_memory.vcd'
    rec.write(path)
    out = subprocess.run(['sigrok-cli', '-i', str(path), '-I', 'vcd', '-P',
                          'i2c:scl=scl:sda=sda', '-A', 'i2c'],
                         text=True, capture_output=True, check=True).stdout
    import re
    assert [int(x, 16) for x in re.findall(r'Data read: ([0-9A-F]{2})', out)] == expected, out


def test_controller_rejects_nonconforming_fast_mode_low_time():
    # 50% duty at 400 kHz gives only 1.26 us low; Fast-mode needs 1.3 us.
    with pytest.raises(ValueError, match='SCL phases'):
        MemoryController(125, 62)


@pytest.mark.parametrize('period, high, low_min, start_min', [
    (500, 250, 235, 200), (125, 60, 65, 30),
    (50, 25, 25, 13), (50, 13, 25, 13),
])
def test_controller_bus_phase_lengths(period, high, low_min, start_min):
    """Check emitted edges, including the first low phase, against Table 11."""
    ctrl = MemoryController(period, high)
    ctrl.write(0x50, b'')
    levels = []
    for _ in range(period * 30):
        levels.append((ctrl.scl, ctrl.sda))
        ctrl.step(ctrl.scl, ctrl.sda)
        if ctrl.done(): break
    assert ctrl.done()
    falls = [n for n in range(1, len(levels)) if levels[n-1][0] and not levels[n][0]]
    rises = [n for n in range(1, len(levels)) if not levels[n-1][0] and levels[n][0]]
    start = next(n for n in range(1, len(levels))
                 if levels[n][0] and levels[n-1][1] and not levels[n][1])
    assert falls[0] - start >= start_min
    assert len(rises) == 10
    assert all(b-a == period for a, b in zip(rises[:8], rises[1:9]))
    for rise in rises[:9]:
        before = max(n for n in falls if n < rise)
        after = min(n for n in falls if n > rise)
        assert rise - before >= low_min
        assert after - rise == high


def ack_oracle_trace(samples):
    """Inject sampled pin levels into the monitor, without running a chip or controller FSM."""
    ctrl = MemoryController(50, 25)
    ctrl._gen = False
    ctrl._ack_window = {'byte': 0xA0}
    for sample in samples:
        scl, sda = sample[:2]
        ctrl.sda = sample[2] if len(sample) == 3 else 1
        ctrl.step(scl, sda)
    record = dict(ctrl._ack_window, acked=True)
    ctrl.ack_records = [record,
        {'byte': 0xA2, 'acked': False, 'sda_on_rise': 1, 'controller_released_on_rise': True},
        {'byte': 0xA3, 'acked': False, 'sda_on_rise': 1, 'controller_released_on_rise': True}]
    return ctrl, record


@pytest.mark.parametrize('samples', [
    [(0, 0), (0, 1), (0, 0), (1, 0)],
    [(0, 0), (0, 1), (0, 1), (1, 0)],
    [(0, 0)]*5 + [(0, 1), (0, 0), (1, 0)],
    [(0, 0, 1), (0, 0, 0), (0, 0, 1), (1, 0, 1)],
    [(0, 0)]*3 + [(1, 0), (0, 0), (1, 0)],
])
def test_ack_oracle_rejects_interrupted_or_invalid_setup(samples):
    from protomodels.i2c_memory import check_result
    ctrl, _ = ack_oracle_trace(samples)
    with pytest.raises(AssertionError):
        check_result(ctrl, [])


@pytest.mark.parametrize('samples, expected', [
    ([(0, 0)]*4 + [(1, 0)], 3),
    ([(0, 0)]*5 + [(1, 0)], 4),
    ([(0, 0), (0, 1)] + [(0, 0)]*4 + [(1, 0)], 3),
])
def test_ack_oracle_accepts_only_final_stable_low_interval(samples, expected):
    from protomodels.i2c_memory import check_result
    ctrl, record = ack_oracle_trace(samples)
    assert record['setup_clocks'] == expected
    assert check_result(ctrl, []) == expected


@pytest.mark.parametrize('samples', [
    [(0, 0)]*3 + [(1, 0)],  # two clocks after the observation-uncertainty reserve
    [(0, 0)]*3 + [(1, 0), (1, 1), (1, 0)],
    [(0, 0)]*3 + [(1, 0), (1, 0, 0), (1, 0, 1)],
])
def test_ack_oracle_rejects_short_setup_or_bad_high_phase(samples):
    from protomodels.i2c_memory import check_result
    ctrl, _ = ack_oracle_trace(samples)
    with pytest.raises(AssertionError):
        check_result(ctrl, [])
