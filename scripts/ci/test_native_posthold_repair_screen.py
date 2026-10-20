import copy
import json
from pathlib import Path

import pytest
import yaml
import native_posthold_repair_screen as trial


def config():
    return dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56,
        GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=150, GRT_DESIGN_REPAIR_MAX_SLEW_PCT=55,
        GRT_DESIGN_REPAIR_MAX_CAP_PCT=55, GRT_RESIZER_HOLD_SLACK_MARGIN=.125,
        GRT_RESIZER_SETUP_SLACK_MARGIN=0, GRT_DESIGN_REPAIR_RUN_GRT=True,
        GRT_ALLOW_CONGESTION=False)


@pytest.mark.parametrize('fault', [None, 'GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH',
    'GRT_DESIGN_REPAIR_MAX_SLEW_PCT', 'GRT_DESIGN_REPAIR_MAX_CAP_PCT',
    'GRT_RESIZER_HOLD_SLACK_MARGIN', 'GRT_RESIZER_SETUP_SLACK_MARGIN',
    'GRT_DESIGN_REPAIR_RUN_GRT', 'GRT_ALLOW_CONGESTION'])
def test_only_repair_targets_change(fault):
    before = config()
    if fault:
        before[fault] = 'wrong'
        with pytest.raises(ValueError): trial.configure(before)
        return
    saved = copy.deepcopy(before)
    after = trial.configure(before)
    assert saved == before
    assert {k for k in after if after[k] != before[k]} == {
        'GRT_DESIGN_REPAIR_MAX_SLEW_PCT', 'GRT_DESIGN_REPAIR_MAX_CAP_PCT'}
    assert after['GRT_DESIGN_REPAIR_MAX_SLEW_PCT'] == after['GRT_DESIGN_REPAIR_MAX_CAP_PCT'] == 60


@pytest.mark.parametrize('value', ['omitted', True, False, None, 1])
def test_pinned_rerouting_default_is_accepted_but_explicit_disable_is_rejected(value):
    before = config()
    before.pop('GRT_DESIGN_REPAIR_RUN_GRT')
    if value != 'omitted':
        before['GRT_DESIGN_REPAIR_RUN_GRT'] = value
    saved = copy.deepcopy(before)
    if value == 'omitted' or value is True:
        result = trial.configure(before)
        assert result['GRT_DESIGN_REPAIR_RUN_GRT'] is True
    else:
        with pytest.raises(ValueError, match='requires global rerouting'):
            trial.configure(before)
    assert before == saved


@pytest.mark.parametrize('fault', [None, 'setup', 'electrical'])
def test_checkpoint_never_authorizes_route_and_retains_strict_gates(tmp_path, monkeypatch, fault):
    monkeypatch.chdir(tmp_path); monkeypatch.setenv('PDK_ROOT', '/pdk')
    # Real source artifact omits the pinned step's default rerouting setting.
    original = config(); original.pop('GRT_DESIGN_REPAIR_RUN_GRT')
    Path('src').mkdir(); Path('src/config_native_stock.json').write_text(json.dumps(original))
    source = Path('runs/native-stock-screen/flow/44-openroad-resizertimingpostgrt')
    source.mkdir(parents=True); odb = source/'tt_um_tripwire.odb'; odb.write_bytes(b'original')
    (source/'state_out.json').write_text(json.dumps({'odb': str(odb.resolve())}))
    original_read = Path.read_text
    def read(p, *a, **k):
        if str(p) == '/tmp/native-source-run.json': return '{}'
        return original_read(p, *a, **k)
    monkeypatch.setattr(Path, 'read_text', read)
    monkeypatch.setattr(trial, 'validate', lambda *a: None)
    calls = []
    def run_step(cfg, state, output, steps):
        calls.append(steps)
        output.mkdir(parents=True)
        for i, step in enumerate(steps):
            p = output/f'{i+1}-{step.lower().replace(".", "-")}'
            p.mkdir(); (p/'state_out.json').write_text('{}')
            if 'RepairDesign' in step:
                (p/'openroad-repairdesignpostgrt.log').write_text('checked separately')
            if step == 'OpenROAD.CheckAntennas': (p/'or_metrics_out.json').write_text('{}')
    monkeypatch.setattr(trial, 'run_step', run_step)
    monkeypatch.setattr(trial, 'validate_overflow', lambda *a: None)
    monkeypatch.setattr(trial, 'check_post_antenna_command', lambda *a: None)
    monkeypatch.setattr(trial, 'audit_post_antenna', lambda before, after, timing: after)
    def screen(path, state, output, *a, **kw):
        assert path.parent == Path('src') and kw['repaired'] == state
        output.mkdir()
        (output/'comparison.json').write_text('{}')
        for corner in trial.CORNERS:
            p = output/f'after-{corner}'/'1-openroad-stamidpnr'; p.mkdir(parents=True)
            (p/'checks.rpt').write_text('electrical reports')
            slack = 3.0 if fault == 'setup' else 3.8
            (p/'capture_setup.rpt').write_text(
                'Startpoint: latch\nEndpoint: ff (rising edge-triggered flip-flop)\nPath Type: max\n'
                f' {slack} slack (MET)\n')
    monkeypatch.setattr(trial, 'screen', screen)
    monkeypatch.setattr(trial, 'measure', lambda paths: {})
    monkeypatch.setattr(trial, 'evaluate', lambda *a: {'qualified': fault != 'electrical'})
    if fault:
        with pytest.raises(ValueError): trial.main()
    else:
        trial.main()
    receipt = json.loads(Path('runs/native-posthold-margin60/gates.json').read_text())
    assert receipt['qualified'] is False and receipt['route_authorized'] is False
    assert receipt['clean_synthesis'] is False and receipt['reproduction_required'] is True
    assert receipt['minimum_slow_capture_setup_ns'] == 3.5
    assert odb.read_bytes() == b'original'
    assert calls == [['OpenROAD.RepairDesignPostGRT', 'OpenROAD.RepairAntennas'], ['OpenROAD.CheckAntennas']]


def test_workflow_uses_exact_failed_source_and_no_routing():
    root = Path(__file__).resolve().parents[2]
    job = yaml.safe_load((root/'.github/workflows/gds-native-posthold-margin60-screen.yaml').read_text())['jobs']['harden']
    download = next(s for s in job['steps'] if 'download-artifact@' in s.get('uses', ''))
    assert download['with']['run-id'] == 39468700509
    commands = '\n'.join(s.get('run', '') for s in job['steps'])
    assert 'native_posthold_repair_screen.py' in commands
    assert 'native_arithmetic_screen.py' not in commands
