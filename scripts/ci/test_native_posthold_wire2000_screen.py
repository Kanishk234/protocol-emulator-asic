from pathlib import Path

import pytest
import yaml
import native_posthold_wire2000_screen as trial
from test_native_posthold_repair_screen import config


def test_one_effective_control_differs_from_previous_repair():
    original = config()
    original.pop('GRT_DESIGN_REPAIR_RUN_GRT')
    base = trial.base_configure(original)
    candidate = trial.configure(original)
    assert {k for k in base if base[k] != candidate[k]} == {'GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH'}
    assert candidate['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH'] == 2000
    assert candidate['CLOCK_PERIOD'] == 20
    assert candidate['GRT_RESIZER_HOLD_SLACK_MARGIN'] == .125
    assert candidate['GRT_DESIGN_REPAIR_MAX_SLEW_PCT'] == candidate['GRT_DESIGN_REPAIR_MAX_CAP_PCT'] == 60
    assert candidate['GRT_DESIGN_REPAIR_RUN_GRT'] is True


def test_wrong_base_is_rejected():
    original = config(); original['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH'] = 2000
    with pytest.raises(ValueError): trial.configure(original)


def test_wrapper_keeps_common_all_corner_qualification(monkeypatch):
    calls = []
    monkeypatch.setattr(trial, 'run_screen', lambda **kw: calls.append(kw))
    trial.main()
    assert calls == [{'config_transform': trial.configure, 'output': Path('runs/native-posthold-wire2000')}]


def test_workflow_reuses_original_source_not_the_overbuffered_result():
    root = Path(__file__).resolve().parents[2]
    job = yaml.safe_load((root/'.github/workflows/gds-native-posthold-wire2000-screen.yaml').read_text())['jobs']['harden']
    download = next(s for s in job['steps'] if 'download-artifact@' in s.get('uses', ''))
    assert download['with']['run-id'] == 39468700509
    commands = '\n'.join(s.get('run', '') for s in job['steps'])
    assert 'native_posthold_wire2000_screen.py' in commands
    assert 'native_arithmetic_screen.py' not in commands
