from pathlib import Path
import subprocess

import pytest
import yaml

import native_sample_delta8_screen as trial
from timing_trial import CANDIDATE, PATCHES
from verify_drop_parallel import TRIAL_HASH
from verify_sample_delta_low8 import ROOT


def prepared(tmp_path):
    files = PATCHES[trial.VARIANT][1]
    for name in files:
        path = tmp_path / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(subprocess.check_output(['git', 'show', CANDIDATE + ':' + name], cwd=ROOT))
    subprocess.run(['git', 'apply', str(ROOT / 'spikes/r4_floorplan' /
                    PATCHES[trial.VARIANT][0])], cwd=tmp_path, check=True)
    return files


@pytest.mark.parametrize('bad', [None, 'variant', *PATCHES[trial.VARIANT][1]])
def test_all_seven_sources_required_before_flow(tmp_path, monkeypatch, bad):
    prepared(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('VARIANT', 'wrong' if bad == 'variant' else trial.VARIANT)
    if bad and bad != 'variant':
        with Path(bad).open('a') as f:
            f.write('// unreviewed source change\n')
    calls = []
    monkeypatch.setattr(trial, 'run_screen', lambda: calls.append('screen'))
    if bad:
        with pytest.raises(ValueError, match='Wrong verified'):
            trial.main()
        assert calls == []
    else:
        trial.main()
        assert calls == ['screen']


def test_separate_workflow_pins_sources_and_stops_before_detailed_route():
    workflow = ROOT / '.github/workflows/gds-native-sample-delta8-screen.yaml'
    job = yaml.safe_load(workflow.read_text())['jobs']['harden']
    assert job['env']['VARIANT'] == trial.VARIANT
    assert job['env']['CANDIDATE_SHA'] == CANDIDATE
    assert job['strategy']['matrix']['strategy'] == ['AREA 1']
    text = '\n'.join(s.get('run', '') for s in job['steps'])
    assert 'native_sample_delta8_screen.py' in text
    assert TRIAL_HASH in text
    assert "final < ids.index('OpenROAD.DetailedRouting')" in text
    for step in job['steps']:
        if 'run' in step:
            subprocess.run(['bash', '-n'], input=step['run'], text=True, check=True)
