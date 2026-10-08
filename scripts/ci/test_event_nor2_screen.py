import json
from pathlib import Path
import subprocess

import pytest

from event_nor2_screen import promote_netlists, validate_netlist, validate_overflow, validate_run, validate_physical_baseline, validate_antenna_only_changes, promote_antenna_netlists


ORIGINAL = 'sg13cmos5l_nor2_1 _27853_ (.A(_21095_), .B(_02509_), .Y(_02510_));'
CHANGED = ORIGINAL.replace('nor2_1', 'nor2_2')
ANTENNAS = '\n'.join(f'sg13cmos5l_antennanp antenna{i} (.A(net{i}));' for i in range(92))


def test_exact_change_only():
    validate_netlist(ORIGINAL, CHANGED)
    for bad in (ORIGINAL, CHANGED.replace('_02509_', 'other'), CHANGED + '\n' + CHANGED,
                CHANGED + '\nsg13cmos5l_buf_1 extra (.A(a), .X(b));'):
        with pytest.raises(ValueError):
            validate_netlist(ORIGINAL, bad)


@pytest.mark.parametrize('key,value', [('id', 1), ('head_branch', 'trial'),
                                      ('conclusion', 'failure'), ('path', 'wrong')])
def test_run_provenance(key, value):
    run = dict(id=37574267994, head_branch='main', conclusion='success',
               path='.github/workflows/gds-placement-route.yaml')
    validate_run(run)
    run[key] = value
    with pytest.raises(ValueError):
        validate_run(run)


def test_fresh_netlists_replace_stale_views(tmp_path):
    original = tmp_path / 'original.v'
    original.write_text(ORIGINAL)
    state = tmp_path / 'state_out.json'
    state.write_text(json.dumps(dict(odb=str(tmp_path / 'chip.odb'), nl=str(original),
                                    pnl='old', spef='old', sdf='old', lib='old')))
    with pytest.raises(ValueError, match='Fresh'):
        promote_netlists(state, original)
    (tmp_path / 'chip.baseline.nl.v').write_text(ORIGINAL + '\n' + ANTENNAS)
    (tmp_path / 'chip.eco.nl.v').write_text(CHANGED + '\n' + ANTENNAS)
    (tmp_path / 'chip.eco.pnl.v').write_text(CHANGED + '\n' + ANTENNAS)
    new = json.loads(promote_netlists(state, original).read_text())
    assert new['nl'].endswith('chip.eco.nl.v')
    assert new['pnl'].endswith('chip.eco.pnl.v')
    assert all(new[k] is None for k in ('spef', 'sdf', 'lib'))
    assert json.loads(state.read_text())['nl'] == str(original)


def test_source_antenna_materialization_is_exact_and_eco_preserves_it():
    physical = ORIGINAL + '\n' + ANTENNAS
    validate_physical_baseline(ORIGINAL, physical)
    for bad in (ORIGINAL, physical.replace('antennanp', 'buf_1', 1),
                physical.replace('_21095_', 'wrong'), physical.replace('antenna91', 'antenna90')):
        with pytest.raises(ValueError):
            validate_physical_baseline(ORIGINAL, bad)
    with pytest.raises(ValueError):
        validate_netlist(physical, CHANGED + '\n' + ANTENNAS.replace('net91', 'wrong'))


def test_antenna_repair_allows_only_diodes_on_existing_nets():
    diode = '\nsg13cmos5l_antennanp new_diode (.A(_02510_));'
    validate_antenna_only_changes(CHANGED, CHANGED + diode)
    validate_antenna_only_changes(CHANGED, CHANGED)
    for bad in (CHANGED + diode.replace('_02510_', 'unknown'),
                CHANGED + diode.replace('antennanp', 'buf_1'),
                CHANGED.replace('_02509_', 'wrong') + diode, '',
                CHANGED + diode.replace('.A(', '.Y(')):
        with pytest.raises(ValueError):
            validate_antenna_only_changes(CHANGED, bad)


def test_antenna_views_are_fresh_and_original_state_is_preserved(tmp_path):
    original = tmp_path / 'original.v'
    original.write_text(CHANGED)
    state = tmp_path / 'state_out.json'
    state.write_text(json.dumps(dict(odb=str(tmp_path / 'chip.odb'), nl=str(original), pnl='old')))
    with pytest.raises(ValueError, match='Fresh'):
        promote_antenna_netlists(state, original)
    (tmp_path / 'chip.eco.nl.v').write_text(CHANGED + '\nsg13cmos5l_antennanp diode (.A(_02510_));')
    (tmp_path / 'chip.eco.pnl.v').write_text(CHANGED)
    new = json.loads(promote_antenna_netlists(state, original).read_text())
    assert new['nl'].endswith('chip.eco.nl.v')
    assert all(new[k] is None for k in ('spef', 'sdf', 'lib'))
    assert json.loads(state.read_text())['nl'] == str(original)


def test_overflow_requires_complete_fresh_zero_report():
    good = 'Final congestion report:\n' + ''.join(
        f'Metal{i} 100 50 50.00% 0 / 0 / 0\n' for i in range(1, 5))
    validate_overflow(good)
    for bad in ('', good.replace('Metal4', 'Other'), good.replace('0 / 0 / 0', '0 / 1 / 1')):
        with pytest.raises(ValueError):
            validate_overflow(bad)


def test_wrapper_injection_and_delegation(tmp_path):
    root = Path(__file__).parent
    wrapper = tmp_path / 'wrapper'
    wrapper.write_text((root / 'openroad_event_nor2_wrapper.sh').read_text())
    companion = tmp_path / 'tripwire-openroad-hotspot'
    companion.write_text('#!/bin/bash\ncat "${@: -1}"\n')
    companion.chmod(0o755)
    grt = tmp_path / 'grt.tcl'
    grt.write_text('read_current_odb\nwrite_views\n')
    result = subprocess.run(['bash', str(wrapper), '-exit', str(grt)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    text = result.stdout
    assert text.index('read_current_odb') < text.index('tripwire_size_event_nor2')
    assert text.index('.baseline.nl.v') < text.index('tripwire_size_event_nor2')
    assert text.index('tripwire_size_event_nor2') < text.index('common/dpl.tcl') < text.index('write_views')
    assert 'SAVE_NL' in text and 'SAVE_PNL' in text
    grt.write_text('read_current_odb\nread_current_odb\n')
    result = subprocess.run(['bash', str(wrapper), str(grt)], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'tripwire_size_event_nor2' not in result.stdout
    other = tmp_path / 'sta.tcl'
    other.write_text('UNMODIFIED\n')
    result = subprocess.run(['bash', str(wrapper), str(other)], capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout == 'UNMODIFIED\n'
    antenna = tmp_path / 'antenna_repair.tcl'
    antenna.write_text('read_current_odb\nrepair_antennas diode\nwrite_views\n')
    result = subprocess.run(['bash', str(wrapper), str(antenna)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'tripwire_size_event_nor2' not in result.stdout
    assert 'SAVE_NL' in result.stdout and 'SAVE_PNL' in result.stdout
