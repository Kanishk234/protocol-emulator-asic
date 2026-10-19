import json
from pathlib import Path
import pytest
import native_setup_reserve_screen as target
from native_stock_screen import configure as base_configure
from native_wire150_screen import configure as wire_configure


def report(slack='4.1', endpoint='rising edge-triggered flip-flop', kind='max'):
    return f'Startpoint: latch0 (positive level-sensitive latch clocked by clk)\nEndpoint: ff0 ({endpoint} clocked by clk)\nPath Type: {kind}\n {slack} slack (MET)\n'


def test_native_trial_changes_only_setup_repair_margin():
    base=base_configure(dict(CLOCK_PERIOD=20,PL_TARGET_DENSITY_PCT=56),'AREA 1',
        Path('src/signoff.sdc'),hold_target=.10,clock_cluster=8)
    before=wire_configure(base);after=target.configure(base)
    assert {k for k in before if before[k]!=after[k]}=={'GRT_RESIZER_SETUP_SLACK_MARGIN'}
    assert after['GRT_RESIZER_SETUP_SLACK_MARGIN']==4.0
    assert after['GRT_RESIZER_HOLD_SLACK_MARGIN']==.125
    assert after['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH']==150
    assert after['CLOCK_PERIOD']==20 and before['GRT_RESIZER_SETUP_SLACK_MARGIN']==0


@pytest.mark.parametrize('text',['','No paths found',report(kind='min'),
    report(endpoint='positive level-sensitive latch'),report('1e999'),report('nan'),
    report().replace('slack (MET)','slack unknown'),report()+report().replace('Path Type: max','')])
def test_bad_capture_evidence_rejected(text):
    with pytest.raises(ValueError):target.capture_setup(text)


def test_capture_uses_minimum_over_all_paths():
    assert target.capture_setup(report('4.0')+report('3.8')+report('-1.0'))==-1.0


def evidence(root, slack='3.6', prior=True):
    root.mkdir(parents=True,exist_ok=True)
    (root/'gates.json').write_text(json.dumps(dict(qualified=prior,minimum_fast_hold_ns=.05,official_signoff=False)))
    for c in target.CORNERS:
        stage=root/'timing'/f'after-{c}'/'1-openroad-stamidpnr';stage.mkdir(parents=True)
        (stage/'capture_setup.rpt').write_text(report(slack))


@pytest.mark.parametrize('fault',[None,'insufficient','missing','duplicate','prior','malformed'])
def test_gate_fails_closed_and_preserves_original_qualification(tmp_path,fault):
    evidence(tmp_path,slack='1.483047' if fault=='insufficient' else '3.5',prior=fault!='prior')
    stage=tmp_path/'timing'/f'after-{target.CORNERS[1]}'/'1-openroad-stamidpnr'
    if fault=='missing':(stage/'capture_setup.rpt').unlink()
    if fault=='malformed':(stage/'capture_setup.rpt').write_text(report('nan'))
    if fault=='duplicate':
        d=stage.with_name('2-openroad-stamidpnr');d.mkdir();(d/'capture_setup.rpt').write_text(report())
    if fault:
        with pytest.raises(ValueError):target.enforce(tmp_path)
    else:target.enforce(tmp_path)
    gate=json.loads((tmp_path/'gates.json').read_text())
    assert gate['qualified'] is (fault is None)
    assert gate['minimum_fast_hold_ns']==.05 and gate['official_signoff'] is False
    assert gate['minimum_slow_capture_setup_ns']==3.5


@pytest.mark.parametrize('override', [False, True])
def test_entrypoint_reuses_all_original_native_gates(tmp_path,monkeypatch,override):
    monkeypatch.chdir(tmp_path);called=[]
    def screen(**options):
        called.append(options)
        evidence(Path('runs/native-stock-screen'))
    monkeypatch.setattr(target,'margin_screen',screen)
    transform = (lambda config: config) if override else target.configure
    target.main(config_transform=transform)
    assert called[0]['config_transform'] is transform
    assert called[0]['final_antenna_repair'] is True
    assert called[0]['audit_tcl'].name=='native_timing_headroom_audit.tcl'
    assert json.loads(Path('runs/native-stock-screen/gates.json').read_text())['estimated_setup_reserve_pass'] is True


def test_workflow_keeps_capture_reports_and_exact_runner_setup():
    import yaml
    p=Path(__file__).resolve().parents[2]/'.github/workflows/gds-native-wire150-setup4-screen.yaml'
    w=yaml.safe_load(p.read_text());steps=w['jobs']['harden']['steps']
    commands='\n'.join(s.get('run','') for s in steps)
    assert 'native_setup_reserve_screen.py' in commands
    assert 'from librelane.flows.classic import Classic' in commands
    assert 'librelane==3.1.0.dev3' in commands
    early=next(s for s in steps if s['name']=='Upload early gate evidence')['with']['path']
    assert 'capture_setup.rpt' in early and 'gates.json' in early
