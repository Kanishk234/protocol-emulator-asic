import json
from pathlib import Path

import pytest
import yaml

import native_drop_parallel_screen as trial
import native_stock_screen as stock
import native_setup_reserve_screen as reserve
from test_native_setup_reserve import evidence
from test_native_no_final_grt_control import coverage
from native_stock_screen import configure as base_configure


@pytest.mark.parametrize('wrong', [False, True])
def test_wrapper_requires_proved_source_before_build(monkeypatch, wrong):
    monkeypatch.setenv('VARIANT', 'bs-resync-cfg-tx-cached-lane-mask-drop-parallel')
    monkeypatch.setattr(trial, 'digest', lambda path: 'wrong' if wrong else trial.TRIAL_HASH)
    calls = []
    monkeypatch.setattr(trial.subprocess, 'run', lambda *a, **kw: calls.append('build'))
    def screen(**kw):
        assert kw['image_override'] == trial.IMAGE
        assert kw['config_transform'] is trial.configure
        assert kw['audit_tcl'].name == 'native_no_final_grt_audit.tcl'
        calls.append('screen')
    monkeypatch.setattr(trial, 'reserve_screen', screen)
    monkeypatch.setattr(trial, 'enforce_routing_objects', lambda root: calls.append('coverage'))
    if wrong:
        with pytest.raises(ValueError): trial.main()
        assert not calls
    else:
        trial.main()
        assert calls == ['build', 'screen', 'coverage']


def test_unknown_image_rejected_before_any_flow():
    with pytest.raises(ValueError, match='image'):
        stock.main(image_override='arbitrary:latest')


def test_disabled_final_route_rejected_before_flow():
    base = base_configure(dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56),
                          'AREA 1', Path('src/signoff.sdc'), hold_target=.10, clock_cluster=8)
    assert trial.configure(base)['GRT_RESIZER_HOLD_SLACK_MARGIN'] == .125
    with pytest.raises(ValueError, match='final native route branch'):
        trial.configure(dict(base, GRT_RESIZER_RUN_GRT=False))


def test_setup_gate_retained_with_explicit_image(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    def screen(**options):
        assert options['image_override'] == trial.IMAGE
        evidence(Path('runs/native-stock-screen'), slack='3.0')
    monkeypatch.setattr(reserve, 'margin_screen', screen)
    with pytest.raises(ValueError):
        reserve.main(image_override=trial.IMAGE)


def test_workflow_one_hardware_delta_and_same_gates():
    root = Path(__file__).resolve().parents[2]
    job = yaml.safe_load((root/'.github/workflows/gds-native-drop-parallel-screen.yaml').read_text())['jobs']['harden']
    assert job['env']['VARIANT'] == 'bs-resync-cfg-tx-cached-lane-mask-drop-parallel'
    assert job['strategy']['matrix']['strategy'] == ['AREA 1']
    text = '\n'.join(s.get('run', '') for s in job['steps'])
    assert 'native_drop_parallel_screen.py' in text and trial.TRIAL_HASH in text


@pytest.mark.parametrize('prior', [False, True])
@pytest.mark.parametrize('missing', [0, 1])
def test_route_objects_required_without_overriding_other_failures(tmp_path, monkeypatch, prior, missing):
    (tmp_path/'gates.json').write_text(json.dumps({'qualified': prior, 'estimated_margin_pass': prior}))
    stage = tmp_path/'flow/1-openroad-resizertimingpostgrt'
    stage.mkdir(parents=True)
    (stage/'state_out.json').write_text('{}')
    (stage/'openroad-resizertimingpostgrt.log').write_text('TRIPWIRE_INCREMENTAL begin\nTRIPWIRE_INCREMENTAL end\n')
    monkeypatch.setattr(trial, 'collect', lambda *a: {'verified': 'snapshot views'})
    for c in trial.CORNERS:
        stage = tmp_path/'timing'/f'after-{c}'/'1-openroad-stamidpnr'
        stage.mkdir(parents=True)
        (stage/'route_coverage.rpt').write_text(coverage(c, missing))
    if missing:
        with pytest.raises(ValueError, match='Missing signal'):
            trial.enforce_routing_objects(tmp_path)
    else:
        trial.enforce_routing_objects(tmp_path)
    gates = json.loads((tmp_path/'gates.json').read_text())
    assert gates['qualified'] is (prior and not missing)
    assert gates['estimated_margin_pass'] is prior
    assert gates['routing_completeness_proven'] is False


def test_missing_route_report_cannot_leave_qualified_true(tmp_path):
    (tmp_path/'gates.json').write_text(json.dumps({'qualified': True}))
    with pytest.raises(ValueError):
        trial.enforce_routing_objects(tmp_path)
    assert json.loads((tmp_path/'gates.json').read_text())['qualified'] is False
