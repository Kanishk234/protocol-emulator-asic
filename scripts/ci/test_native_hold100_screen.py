import json
import os
from pathlib import Path
import subprocess
import pytest
from native_hold100_screen import promote, promote_antenna
from test_native_hold100_size import netlist


def checkpoint(tmp_path):
    odb = tmp_path / 'chip.odb'
    baseline = tmp_path / 'source.v'
    baseline.write_text(netlist())
    odb.with_suffix('.baseline.nl.v').write_text(netlist())
    odb.with_suffix('.eco.nl.v').write_text(netlist(True))
    odb.with_suffix('.eco.pnl.v').write_text(netlist(True))
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
    if failure == 'rewire': odb.with_suffix('.eco.nl.v').write_text(netlist(True).replace('net7221', 'wrong'))
    if failure == 'missing': odb.with_suffix('.eco.pnl.v').unlink()
    with pytest.raises(ValueError): promote(state, baseline)


def test_antenna_exports_preserve_six_changes(tmp_path):
    odb, baseline, state = checkpoint(tmp_path)
    baseline.write_text(netlist(True))
    odb.with_suffix('.eco.nl.v').write_text(netlist(True) + '\nsg13cmos5l_antennanp ant (.A(net7221));')
    result = json.loads(promote_antenna(state, baseline).read_text())
    assert result['spef'] is None
    odb.with_suffix('.eco.nl.v').write_text(netlist())
    with pytest.raises(ValueError): promote_antenna(state, baseline)


@pytest.mark.parametrize('stage', ['grt', 'antenna_repair', 'sta'])
def test_wrapper_injects_only_reviewed_stages(tmp_path, stage):
    mock = tmp_path / 'openroad'
    mock.write_text('#!/usr/bin/env bash\ncat "${!#}"\n')
    mock.chmod(0o755)
    script = tmp_path / (stage + '.tcl')
    script.write_text('read_current_odb\nputs flow\n')
    wrapper = Path(__file__).with_name('openroad_native_hold100_wrapper.sh').resolve()
    env = dict(os.environ, PATH=str(tmp_path) + ':' + os.environ['PATH'])
    result = subprocess.run(['bash', str(wrapper), '-exit', str(script)], env=env,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert ('native_hold100_targets.tcl' in result.stdout) == (stage == 'grt')
    assert ('.eco.nl.v' in result.stdout) == (stage != 'sta')
    assert ('common/dpl.tcl' in result.stdout) == (stage == 'grt')
    if stage == 'grt':
        script.write_text('read_current_odb\nread_current_odb\n')
        result = subprocess.run(['bash', str(wrapper), str(script)], env=env,
                                capture_output=True, text=True)
        assert result.returncode != 0


def test_workflow_exact_source_and_screen_only():
    import yaml
    path = Path(__file__).resolve().parents[2] / '.github/workflows/gds-native-hold100-strength-screen.yaml'
    data = yaml.safe_load(path.read_text())
    steps = data['jobs']['harden']['steps']
    download = next(s for s in steps if 'download-artifact@' in s.get('uses', ''))
    assert int(download['with']['run-id']) == 37870374707
    assert download['with']['name'] == 'gds-native-hold100-route-37870374707'
    assert next(s for s in steps if s['name'].startswith('Size six'))['run'].endswith('native_hold100_screen.py')


@pytest.mark.parametrize('cleanup_needed', [False, True])
@pytest.mark.parametrize('timing_ok', [False, True])
def test_orchestration_uses_fresh_views_and_never_reroutes_after_cleanup(tmp_path, monkeypatch, cleanup_needed, timing_ok):
    import native_hold100_screen as runner
    from postgrt_timing import CORNERS
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('PDK_ROOT', '/pdk')
    def write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
    source = tmp_path / 'runs/native-stock-route/drt/1-openroad-detailedrouting/state_out.json'
    write(source, {})
    write(source.parent / 'config.json', {'GRT_RESIZER_HOLD_SLACK_MARGIN': .10})
    write(tmp_path / 'src/config_native_stock.json', {})
    baseline = tmp_path / 'runs/extracted-timing/final/nl/tt_um_tripwire.nl.v'
    baseline.parent.mkdir(parents=True)
    baseline.write_text(netlist())
    def read_json(path):
        path = Path(path)
        if str(path) == '/tmp/native-eco-source-run.json': return {'id': 37870374707}
        if str(path) in ('/tmp/native-trusted-config.json', '/tmp/native-trusted-files.json'): return {}
        return json.loads(original_read(path))
    original_read = Path.read_text
    monkeypatch.setattr(runner, 'validate', lambda *args: None)
    monkeypatch.setattr(runner, 'fingerprints', lambda *args: {})
    monkeypatch.setattr(runner, 'prepare', lambda *args: {})
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
            for ext in ('.eco.nl.v', '.eco.pnl.v'): odb.with_suffix(ext).write_text(netlist(True))
            (stage / 'openroad-globalrouting.log').write_text('TRIPWIRE native hold100 setup:\n' * 6)
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
                for ext in ('.eco.nl.v', '.eco.pnl.v'): odb.with_suffix(ext).write_text(netlist(True))
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
    assert calls.count(['OpenROAD.GlobalRouting']) == 1
    assert not any('OpenROAD.DetailedRouting' in steps for steps in calls)
    assert calls[-1] == (['OpenROAD.RepairAntennas', 'OpenROAD.CheckAntennas'] if cleanup_needed
                        else ['OpenROAD.CheckAntennas'])
