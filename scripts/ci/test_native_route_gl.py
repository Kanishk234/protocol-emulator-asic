import json
import pytest
from native_route_gl import SOURCES, validate


def fixture(tmp_path, run_id):
    sha, profile, source, workflow = SOURCES[run_id]
    run = dict(id=run_id, head_sha=sha, head_branch='main', conclusion='success',
               path=f'.github/workflows/{workflow}.yaml')
    root = tmp_path
    route = root / 'runs/native-stock-route'
    step = route / 'drt/1-openroad-detailedrouting'
    step.mkdir(parents=True)
    (route / 'gates.json').write_text(json.dumps(dict(qualified=True, profile=profile,
            source_run=source, minimum_fast_hold_ns=0.05)))
    (step / 'state_out.json').write_text(json.dumps(dict(metrics={'route__drc_errors': 0},
        nl='/runner/runs/native-stock-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v')))
    (step / 'config.json').write_text(json.dumps(dict(CLOCK_PERIOD=20,
        SYNTH_STRATEGY='AREA 1', GRT_ADJUSTMENT=0.16, PNR_SDC_FILE='/runner/src/signoff.sdc')))
    (step / 'tt_um_tripwire.nl.v').write_text('module tt_um_tripwire; RM_IHPSG13_1P_512x16_c2_bm_bist s(); endmodule')
    return root, run, step


@pytest.mark.parametrize('run_id', list(SOURCES))
def test_both_exact_native_routes(tmp_path, run_id):
    root, run, step = fixture(tmp_path, run_id)
    result = validate(root, run)
    assert result['functional_simulation_only'] is True
    assert result['official_signoff'] is False
    assert len(result['sha256']) == 64


@pytest.mark.parametrize('field,value', [('conclusion', 'failure'), ('head_branch', 'other'),
    ('head_sha', 'wrong'), ('path', '.github/workflows/gds.yaml'), ('id', 1)])
def test_wrong_provenance(tmp_path, field, value):
    root, run, step = fixture(tmp_path, 37870374707)
    run[field] = value
    with pytest.raises(ValueError):
        validate(root, run)


@pytest.mark.parametrize('file,key,value', [
    ('state_out.json', 'nl', '/wrong/netlist.v'),
    ('state_out.json', 'metrics', {'route__drc_errors': 1}),
    ('config.json', 'CLOCK_PERIOD', 25),
    ('config.json', 'PNR_SDC_FILE', '/runner/src/pnr.sdc')])
def test_wrong_physical_evidence(tmp_path, file, key, value):
    root, run, step = fixture(tmp_path, 37870374707)
    path = step / file
    data = json.loads(path.read_text()); data[key] = value
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        validate(root, run)


def test_native_workflow_uses_exact_candidate_and_validator():
    from pathlib import Path
    import yaml
    path = Path(__file__).resolve().parents[2] / '.github/workflows/l3-native-routed-gl.yaml'
    workflow = yaml.safe_load(path.read_text())
    steps = workflow['jobs']['l3']['steps']
    validation = next(step['run'] for step in steps if step['name'] == 'Validate artifact and repaired netlist')
    assert 'from native_route_gl import validate' in validation
    assert 'test "$CANDIDATE_SHA" = "3393eea9a58c5cad9077cc360a8515d0e5ec8284"' in validation
    download = next(step for step in steps if 'download-artifact@' in step.get('uses', ''))
    assert 'gds-native-' in download['with']['name']
    assert download['with']['run-id'] == '${{ github.event.workflow_run.id || inputs.route_run_id }}'
