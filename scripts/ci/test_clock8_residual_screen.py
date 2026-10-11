import json
from pathlib import Path
import pytest
import clock8_residual_screen as runner
from test_clock8_residual_plan import fixture


@pytest.mark.parametrize('kind', ['antenna', 'hold'])
def test_promote_checks_actual_topology_and_clears_parasitics(tmp_path, monkeypatch, kind):
    before, layout, after, proposal = fixture(monkeypatch, kind)
    baseline = tmp_path / 'source.v'; baseline.write_text(before)
    physical = tmp_path / 'source.def'; physical.write_text(layout)
    odb = tmp_path / 'chip.odb'
    odb.with_suffix('.baseline.nl.v').write_text(before)
    odb.with_suffix('.eco.nl.v').write_text(after)
    odb.with_suffix('.eco.pnl.v').write_text(after)
    state = tmp_path / 'state_out.json'
    state.write_text(json.dumps(dict(odb=str(odb), spef='stale', sdf='stale', lib='stale')))
    promoted = runner.promote(state, baseline, physical, proposal)
    data = json.loads(promoted.read_text())
    assert data['spef'] is data['sdf'] is data['lib'] is None
    odb.with_suffix('.eco.nl.v').write_text(after.replace(proposal['buffer_master']+' tripwire', 'sg13cmos5l_inv_4 tripwire'))
    with pytest.raises(ValueError): runner.promote(state, baseline, physical, proposal)


@pytest.mark.parametrize('kind', ['antenna', 'hold', 'fanout', 'clock'])
def test_independent_workflows_pin_route_and_upload_new_results(kind):
    import yaml
    root = Path(__file__).resolve().parents[2]
    workflow = yaml.safe_load((root / f'.github/workflows/gds-clock8-{kind}-screen.yaml').read_text())
    job = workflow['jobs']['harden']
    assert job['env']['NATIVE_ROUTE_PROFILE'] == 'clock8'
    download = next(s for s in job['steps'] if 'download-artifact@' in s.get('uses',''))
    assert download['with']['run-id'] == 38019338907
    assert download['with']['name'] == 'gds-native-clock8-strength-route-38019338907'
    assert any(s.get('run','').endswith('clock8_residual_screen.py --kind '+kind) for s in job['steps'])
    upload = next(s for s in job['steps'] if 'upload-artifact@' in s.get('uses',''))
    assert 'runs/clock8-residual-'+kind+'/**' in upload['with']['path']
    assert job['timeout-minutes'] == 120


@pytest.mark.parametrize('key,value', [('id',1),('head_sha','wrong'),('head_branch','other'),
                                     ('conclusion','failure'),('path','wrong')])
def test_source_provenance_fails_before_reading_artifact(tmp_path, key, value):
    run = dict(id=runner.SOURCE_RUN, head_sha=runner.SOURCE_SHA, head_branch='main',
               conclusion='success', path='.github/workflows/gds-native-clock8-strength-route.yaml')
    run[key] = value
    with pytest.raises(ValueError, match='provenance'):
        runner.validate_inputs(tmp_path, run, {}, {})
