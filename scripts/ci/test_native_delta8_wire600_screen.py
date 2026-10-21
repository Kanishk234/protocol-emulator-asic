import ast
from pathlib import Path
import subprocess

import pytest
import yaml

import native_delta8_wire600_screen as trial
from native_stock_screen import configure as stock_configure
from native_sample_delta8_screen import VARIANT


def test_only_native_wire_target_changes():
    source = stock_configure(dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56),
                             'AREA 1', Path('src/signoff.sdc'),
                             hold_target=.10, clock_cluster=8)
    control = trial.control_configure(source)
    candidate = trial.configure(source)
    changed = {k for k in candidate if candidate[k] != control[k]}
    assert changed == {'GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH'}
    assert candidate['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH'] == 600
    assert candidate['GRT_RESIZER_HOLD_SLACK_MARGIN'] == .125
    with pytest.raises(ValueError):
        trial.configure(dict(source, GRT_RESIZER_RUN_GRT=False))


@pytest.mark.parametrize('wrong', [False, True])
def test_validate_before_shared_strict_flow(monkeypatch, wrong):
    calls = []
    def validate():
        calls.append('validate')
        if wrong:
            raise ValueError('Wrong source')
    def screen(**kwargs):
        assert kwargs == {'config_transform': trial.configure}
        calls.append('screen')
    monkeypatch.setattr(trial, 'validate_source', validate)
    monkeypatch.setattr(trial, 'run_screen', screen)
    if wrong:
        with pytest.raises(ValueError):
            trial.main()
        assert calls == ['validate']
    else:
        trial.main()
        assert calls == ['validate', 'screen']


def test_workflow_keeps_exact_rtl_source_and_native_stop():
    root = Path(__file__).resolve().parents[2]
    control = yaml.safe_load((root / '.github/workflows/gds-native-sample-delta8-screen.yaml').read_text())['jobs']['harden']
    job = yaml.safe_load((root / '.github/workflows/gds-native-delta8-wire600-screen.yaml').read_text())['jobs']['harden']
    assert job['env'] == control['env']
    assert job['env']['VARIANT'] == VARIANT
    assert job['strategy'] == control['strategy']
    for step in job['steps']:
        if 'run' not in step:
            continue
        s = step['run']
        subprocess.run(['bash', '-n'], input=s, text=True, check=True)
        if "<<'PY'\n" in s:
            ast.parse(s.split("<<'PY'\n", 1)[1].split('\nPY', 1)[0])
    text = '\n'.join(s.get('run', '') for s in job['steps'])
    assert 'native_delta8_wire600_screen.py' in text
    assert "final < ids.index('OpenROAD.DetailedRouting')" in text
