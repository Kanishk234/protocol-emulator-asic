import os
from pathlib import Path
import subprocess

import pytest

from banked_sram_hold_screen import CORNERS, SOURCE_RUN, qualified, validate_source


def data():
    return {'corners': {c: {'after': {
        f'timing__setup__ws__corner:{c}': 0,
        f'timing__setup_vio__count__corner:{c}': 0,
        f'timing__hold__ws__corner:{c}': -0.0223693 if i == 0 else 0.05,
        f'timing__hold_vio__count__corner:{c}': 1 if i == 0 else 0,
    }} for i, c in enumerate(CORNERS)}}


@pytest.mark.parametrize('failure', [None, 'run', 'setup', 'setup-count', 'hold-count', 'hold-budget', 'slow-hold'])
def test_exact_hold_only_source_is_required(failure):
    d = data()
    run = SOURCE_RUN
    row = d['corners'][CORNERS[0]]['after']
    if failure == 'run': run += 1
    if failure == 'setup': row[f'timing__setup__ws__corner:{CORNERS[0]}'] = -0.001
    if failure == 'setup-count': row[f'timing__setup_vio__count__corner:{CORNERS[0]}'] = 1
    if failure == 'hold-count': row[f'timing__hold_vio__count__corner:{CORNERS[0]}'] = 2
    if failure == 'hold-budget': row[f'timing__hold__ws__corner:{CORNERS[0]}'] = -0.026
    if failure == 'slow-hold': d['corners'][CORNERS[1]]['after'][f'timing__hold__ws__corner:{CORNERS[1]}'] = -0.001
    if failure:
        with pytest.raises(ValueError): validate_source(d, run)
    else:
        validate_source(d, run)


@pytest.mark.parametrize('failure', [None, 'fast-budget', 'hold-count', 'slow-setup', 'antenna'])
def test_route_review_requires_all_timing_and_physical_gates(failure):
    d = data()
    row = d['corners'][CORNERS[0]]['after']
    row[f'timing__hold__ws__corner:{CORNERS[0]}'] = 0.06
    row[f'timing__hold_vio__count__corner:{CORNERS[0]}'] = 0
    antenna = {'antenna__violating__nets': 0, 'antenna__violating__pins': 0}
    if failure == 'fast-budget': row[f'timing__hold__ws__corner:{CORNERS[0]}'] = 0.049
    if failure == 'hold-count': row[f'timing__hold_vio__count__corner:{CORNERS[0]}'] = 1
    if failure == 'slow-setup': d['corners'][CORNERS[1]]['after'][f'timing__setup__ws__corner:{CORNERS[1]}'] = -0.001
    if failure == 'antenna': antenna['antenna__violating__pins'] = 1
    assert qualified(d, antenna) == (failure is None)


@pytest.mark.parametrize('reads', [0, 1, 2])
def test_wrapper_inserts_after_one_read_and_before_repair(tmp_path, reads):
    installed = tmp_path / 'openroad-banked-wrapper'
    installed.write_text(Path(__file__).with_name('openroad_banked_hold_wrapper.sh').read_text())
    script = tmp_path / 'rsz_timing_postgrt.tcl'
    script.write_text('read_current_odb\n' * reads + 'repair_timing\n')
    fake = tmp_path / 'tripwire-openroad-hotspot'
    fake.write_text('#!/bin/bash\ncat "${@: -1}"\n')
    fake.chmod(0o755)
    result = subprocess.run(['bash', str(installed), str(script)], capture_output=True, text=True,
                            env={**os.environ, 'PATH': '/usr/bin:/bin', 'RUNNER_TEMP': str(tmp_path)})
    if reads != 1:
        assert result.returncode != 0
        assert 'tripwire_delay_banked_sram_addr8' not in result.stdout
    else:
        assert result.returncode == 0
        assert result.stdout.count('tripwire_delay_banked_sram_addr8') == 1
        assert result.stdout.index('read_current_odb') < result.stdout.index('tripwire_delay_banked_sram_addr8') < result.stdout.index('repair_timing')
        assert '/openroad/common/dpl.tcl' in result.stdout


def test_repair_workflow_is_bound_to_reviewed_source_and_separate_image():
    import yaml
    p = Path(__file__).resolve().parents[2] / '.github/workflows/gds-banked-sram-hold-screen.yaml'
    workflow = yaml.load(p.read_text(), Loader=yaml.BaseLoader)
    job = workflow['jobs']['harden']
    assert job['env']['SOURCE_RUN_ID'] == str(SOURCE_RUN)
    assert job['env']['SOURCE_VARIANT'] == 'bs-event-pin-banked'
    downloads = [s for s in job['steps'] if s.get('uses', '').startswith('actions/download-artifact@')]
    assert downloads[0]['with']['run-id'] == str(SOURCE_RUN)
    runs = '\n'.join(s.get('run', '') for s in job['steps'])
    assert 'banked_sram_hold_screen.py' in runs
    assert 'Dockerfile.openroad-banked-hold' in runs
    assert 'scripts/ci/placement_route.py' not in runs


@pytest.mark.parametrize('failure', [None, 'density', 'placement-density', 'placement-mode', 'repair-clock', 'repair-sdc', 'missing-base-density'])
def test_density_comes_from_base_and_actual_placement_not_resizer(failure):
    from banked_sram_hold_screen import validate_configs
    repair = {'CLOCK_PERIOD': 20, 'GRT_ADJUSTMENT': 0.16,
              'PL_OPTIMIZE_MIRRORING': False, 'PNR_SDC_FILE': 'src/signoff.sdc'}
    base = {**repair, 'PL_TARGET_DENSITY_PCT': 56, 'PL_TIMING_DRIVEN': True}
    placement = {'PL_TARGET_DENSITY_PCT': 56, 'PL_TIMING_DRIVEN': True}
    if failure == 'density': base['PL_TARGET_DENSITY_PCT'] = 57
    if failure == 'placement-density': placement['PL_TARGET_DENSITY_PCT'] = 57
    if failure == 'placement-mode': placement['PL_TIMING_DRIVEN'] = False
    if failure == 'repair-clock': repair['CLOCK_PERIOD'] = 21
    if failure == 'repair-sdc': repair['PNR_SDC_FILE'] = 'src/pnr.sdc'
    if failure == 'missing-base-density': del base['PL_TARGET_DENSITY_PCT']
    if failure:
        with pytest.raises((ValueError, KeyError)):
            validate_configs(repair, base, placement)
    else:
        validate_configs(repair, base, placement)


def test_sta_wrapper_delegates_without_install_directory_on_path(tmp_path):
    installed = tmp_path / 'openroad-banked-wrapper'
    installed.write_text(Path(__file__).with_name('openroad_banked_hold_wrapper.sh').read_text())
    fake = tmp_path / 'tripwire-openroad-hotspot'
    fake.write_text('#!/bin/bash\nprintf "%s\\n" "$@"\n')
    fake.chmod(0o755)
    result = subprocess.run(['bash', str(installed), '-exit', '/tmp/sta.tcl'],
                            capture_output=True, text=True, env={**os.environ, 'PATH': '/usr/bin:/bin'})
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ['-exit', '/tmp/sta.tcl']
