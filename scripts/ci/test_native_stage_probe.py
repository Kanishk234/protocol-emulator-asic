import copy
from pathlib import Path

import pytest
import yaml
import native_stage_probe as probe


def source():
    return dict(id=probe.SOURCE_RUN, head_sha=probe.SOURCE_SHA, head_branch='main',
                conclusion='failure', path='.github/workflows/gds-native-tx-cursor-setup-reserve-screen.yaml')


@pytest.mark.parametrize('fault', [None, 'id', 'head_sha', 'head_branch', 'conclusion', 'path', 'hash', 'clock'])
def test_only_exact_failed_source_is_diagnostic_input(monkeypatch, fault):
    run = source(); config = dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56)
    monkeypatch.setattr(probe, 'digest', lambda p: 'wrong' if fault == 'hash' else probe.HASHES[p.name])
    if fault in run:
        run[fault] = 'wrong'
    if fault == 'clock':
        config['CLOCK_PERIOD'] = 21
    if fault:
        with pytest.raises(ValueError):
            probe.validate(run, config)
    else:
        probe.validate(run, config)


def test_diagnostic_replaces_inherited_flow_with_sta_only():
    original = dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56,
                    meta={'version': 1, 'flow': 'Classic'}, GRT_RESIZER_HOLD_SLACK_MARGIN=.125)
    saved = copy.deepcopy(original)
    result = probe.stage_config(original)
    assert original == saved
    assert result['meta'] == {'version': 1, 'flow': ['OpenROAD.STAMidPNR']}
    assert result['PNR_CORNERS'] == [probe.CORNER]
    assert result['CLOCK_PERIOD'] == 20
    assert result['GRT_RESIZER_HOLD_SLACK_MARGIN'] == .125
    assert result['PNR_SDC_FILE'] == result['SIGNOFF_SDC_FILE']


def test_workflow_downloads_failed_source_and_never_runs_route():
    root = Path(__file__).resolve().parents[2]
    job = yaml.safe_load((root/'.github/workflows/gds-native-tx-stage-diagnosis.yaml').read_text())['jobs']['harden']
    download = next(s for s in job['steps'] if 'download-artifact@' in s.get('uses', ''))
    assert download['with']['run-id'] == probe.SOURCE_RUN
    assert download['with']['name'].endswith(str(probe.SOURCE_RUN))
    commands = '\n'.join(s.get('run', '') for s in job['steps'])
    assert 'native_stage_probe.py' in commands
    assert 'native_arithmetic_screen.py' not in commands
    assert '--prepare' not in commands
    tcl = (root/'scripts/ci/native_stage_probe.tcl').read_text()
    assert 'repair_design' not in tcl and 'repair_timing' not in tcl
    assert 'detailed_route' not in tcl
    for net in ['_09431_', '_21816_']:
        assert net in tcl
