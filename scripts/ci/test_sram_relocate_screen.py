import json
import os
from pathlib import Path
import subprocess
import pytest
from sram_relocate_screen import promote, promote_antenna
from test_native_hold100_size import netlist


def checkpoint(tmp_path):
    odb = tmp_path / 'chip.odb'
    baseline = tmp_path / 'source.v'
    baseline.write_text(netlist())
    odb.with_suffix('.baseline.nl.v').write_text(netlist())
    odb.with_suffix('.eco.nl.v').write_text(netlist())
    odb.with_suffix('.eco.pnl.v').write_text(netlist())
    state = tmp_path / 'state_out.json'
    state.write_text(json.dumps(dict(odb=str(odb), nl=str(baseline), spef='stale.spef')))
    return odb, baseline, state


def test_fresh_views_replace_stale_state(tmp_path):
    odb, baseline, state = checkpoint(tmp_path)
    result = json.loads(promote(state, baseline).read_text())
    assert result['nl'].endswith('.eco.nl.v')
    assert result['pnl'].endswith('.eco.pnl.v')
    assert result['spef'] is None


@pytest.mark.parametrize('failure', ['baseline', 'rewire', 'missing'])
def test_physical_audit_rejects_wrong_views(tmp_path, failure):
    odb, baseline, state = checkpoint(tmp_path)
    if failure == 'baseline': baseline.write_text(netlist() + '\nsg13cmos5l_buf_1 added (.A(a), .X(b));')
    if failure == 'rewire': odb.with_suffix('.eco.nl.v').write_text(netlist().replace('net7221', 'wrong'))
    if failure == 'missing': odb.with_suffix('.eco.pnl.v').unlink()
    with pytest.raises(ValueError): promote(state, baseline)


def test_antenna_exports_preserve_six_changes(tmp_path):
    odb, baseline, state = checkpoint(tmp_path)
    baseline.write_text(netlist())
    odb.with_suffix('.eco.nl.v').write_text(netlist() + '\nsg13cmos5l_antennanp ant (.A(net7221));')
    result = json.loads(promote_antenna(state, baseline).read_text())
    assert result['spef'] is None
    odb.with_suffix('.eco.nl.v').write_text(netlist().replace('net7221','bad'))
    with pytest.raises(ValueError): promote_antenna(state, baseline)


def test_workflow_exact_source_and_screen_only():
    import yaml
    path = Path(__file__).resolve().parents[2] / '.github/workflows/gds-sram-relocate-screen.yaml'
    data = yaml.safe_load(path.read_text())
    steps = data['jobs']['harden']['steps']
    download = next(s for s in steps if 'download-artifact@' in s.get('uses', ''))
    assert int(download['with']['run-id']) == 37954320974
    assert download['with']['name'] == 'gds-native-strength-route-37954320974'
    assert next(s for s in steps if s['name'].startswith('Relocate one'))['run'].endswith('sram_relocate_screen.py')


@pytest.mark.parametrize('cleanup_needed', [False, True])
@pytest.mark.parametrize('timing_ok', [False, True])
def test_orchestration_uses_fresh_views_and_never_reroutes_after_cleanup(tmp_path, monkeypatch, cleanup_needed, timing_ok):
    import sram_relocate_screen as runner
    from postgrt_timing import CORNERS
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('PDK_ROOT', '/pdk')
    def write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
    source = tmp_path / 'runs/native-strength-route/drt/1-openroad-detailedrouting/state_out.json'
    write(source, {})
    (source.parent / 'tt_um_tripwire.nl.v').write_text(netlist())
    write(source.parent / 'config.json', {'GRT_RESIZER_HOLD_SLACK_MARGIN': .10})
    write(tmp_path / 'src/config_native_stock.json', {'GRT_RESIZER_HOLD_SLACK_MARGIN': .10})
    baseline = tmp_path / 'runs/extracted-timing/final/nl/tt_um_tripwire.nl.v'
    baseline.parent.mkdir(parents=True)
    baseline.write_text(netlist())
    def read_json(path):
        path = Path(path)
        if str(path) == '/tmp/native-eco-source-run.json': return {'id': 37954320974}
        if str(path) == '/tmp/native-trusted-config.json': return {'GRT_RESIZER_HOLD_SLACK_MARGIN': .10}
        if str(path) == '/tmp/native-trusted-files.json': return {}
        return json.loads(original_read(path))
    original_read = Path.read_text
    monkeypatch.setattr(runner, 'validate', lambda *args: None)
    monkeypatch.setattr(runner, 'fingerprints', lambda *args: {})
    monkeypatch.setattr(runner, 'plan', lambda *args: {})
    monkeypatch.setattr(Path, 'read_text', lambda path, *a, **kw: json.dumps(read_json(path))
                        if str(path).startswith('/tmp/native-') else original_read(path, *a, **kw))
    calls = []
    def run_step(config, state, output, steps):
        calls.append(steps)
        assert config['GRT_ALLOW_CONGESTION'] is False
        if steps == ['OpenROAD.GlobalRouting']:
            stage = output / '1-openroad-globalrouting'
            stage.mkdir(parents=True)
            odb = stage / 'chip.odb'
            write(stage / 'state_out.json', {'odb': str(odb)})
            odb.with_suffix('.baseline.nl.v').write_text(netlist())
            for ext in ('.eco.nl.v', '.eco.pnl.v'): odb.with_suffix(ext).write_text(netlist())
            (stage / 'openroad-globalrouting.log').write_text('TRIPWIRE SRAM relocation: wire9447 moved\nexact site/master/nets retained after legalization\n' +
                'TRIPWIRE native route reset: cleared 20 ordinary routed wires\n')
        else:
            inherited = json.loads(Path(state).read_text())
            assert inherited['nl'].endswith('.eco.nl.v')
            stage = output / '2-openroad-checkantennas'
            stage.mkdir(parents=True)
            violation = int(cleanup_needed and len(steps) == 1)
            write(stage / 'or_metrics_out.json', {'antenna__violating__nets': violation,
                                                'antenna__violating__pins': violation})
            if len(steps) > 1:
                odb = stage / 'chip.odb'
                inherited['odb'] = str(odb)
                for ext in ('.eco.nl.v', '.eco.pnl.v'): odb.with_suffix(ext).write_text(netlist())
                write(output / 'resolved.json', {'GRT_ALLOW_CONGESTION': False})
                log = output / '1-openroad-repairantennas/1-openroad-diodeinsertion/openroad-diodeinsertion.log'
                log.parent.mkdir(parents=True)
                log.write_text('repair_antennas\n')
            write(stage / 'state_out.json', inherited)
    def sta(config, state, output, pdk, repaired, sdc):
        assert state == repaired
        assert json.loads(Path(state).read_text())['nl'].endswith('.eco.nl.v')
        timing = {'corners': {c: {'after': {f'timing__setup__ws__corner:{c}': 0,
                  f'timing__hold__ws__corner:{c}': .06 if timing_ok else .049}} for c in CORNERS}}
        write(output / 'comparison.json', timing)
    monkeypatch.setattr(runner, 'run_step', run_step)
    monkeypatch.setattr(runner, 'screen', sta)
    monkeypatch.setattr(runner, 'validate_overflow', lambda log: None)
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: None)
    if timing_ok: runner.main()
    else:
        with pytest.raises(ValueError, match='fails timing'): runner.main()
    evidence = tmp_path / 'runs/native-sram-relocate'
    json.loads((evidence / 'source_plan.json').read_text())
    gates = json.loads((evidence / 'gates.json').read_text())
    assert gates['qualified'] is timing_ok
    assert gates['changes'] == 0 and gates['relocated_instances'] == 1
    assert gates['physical_screen_only'] is True
    assert calls.count(['OpenROAD.GlobalRouting']) == 1
    assert not any('OpenROAD.DetailedRouting' in steps for steps in calls)
    assert calls[-1] == (['OpenROAD.RepairAntennas', 'OpenROAD.CheckAntennas'] if cleanup_needed
                        else ['OpenROAD.CheckAntennas'])


@pytest.mark.parametrize('failure', ['missing', 'repeat', 'legalization', 'sizing', 'reset', 'empty_reset'])
def test_bad_physical_history_is_rejected(monkeypatch, failure):
    import sram_relocate_screen as runner
    monkeypatch.setattr(runner, 'validate_overflow', lambda log: None)
    moved = 'TRIPWIRE SRAM relocation: wire9447 moved\n'
    legal = 'exact site/master/nets retained after legalization\n'
    reset = 'TRIPWIRE native route reset: cleared 20 ordinary routed wires\n'
    log = moved + legal + reset
    if failure == 'missing': log = log.replace(moved, '')
    if failure == 'repeat': log += moved
    if failure == 'legalization': log = log.replace(legal, '')
    if failure == 'sizing': log += 'TRIPWIRE native hold100 setup:'
    if failure == 'reset': log = log.replace(reset, '')
    if failure == 'empty_reset': log = log.replace('cleared 20', 'cleared 0')
    with pytest.raises(ValueError): runner.validate_history(log)
