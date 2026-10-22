import ast
import hashlib
import json
from pathlib import Path
import subprocess

import pytest
import yaml

import wire600_clean_route as route
import wire600_clean_gl as gl


def bundle(tmp_path, monkeypatch):
    root = tmp_path
    receipt = dict(clean_synthesis=True, source_artifact_downloaded=False,
                   exact_source_reproduced=True, repaired_measured_gates_pass=True,
                   official_signoff=False, qualified=False, final_state='state.json')
    p = root/route.ROOT/'reproduction.json'
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(receipt))
    (root/'state.json').write_text('{}')
    (root/'netlist.v').write_text('module tt_um_tripwire; RM_IHPSG13_1P_512x16_c2_bm_bist m(); endmodule')
    run = dict(id=39718836864, head_sha='reviewed', conclusion='success', head_branch='main')
    bound = dict(run_binding=run, source_state='state.json', netlist='netlist.v',
                 files={str(x.relative_to(root)): hashlib.sha256(x.read_bytes()).hexdigest()
                        for x in (p, root/'state.json', root/'netlist.v')})
    monkeypatch.setattr(route, 'review', lambda: bound)
    monkeypatch.setattr(gl, 'review', lambda: bound)
    return root, run, bound, receipt, p


def test_bundle_accepts_only_reviewed_bytes(tmp_path, monkeypatch):
    root, run, bound, _, _ = bundle(tmp_path, monkeypatch)
    assert route.validate_bundle(root, run) == root/'state.json'
    result = gl.validate(root, run)
    assert result['functional_simulation_only'] and not result['official_signoff']
    assert not result['detailed_routing_proven']
    (root/'netlist.v').write_text('changed')
    with pytest.raises(ValueError, match='Changed clean'):
        gl.validate(root, run)


@pytest.mark.parametrize('key,value', [('conclusion','failure'), ('id',1), ('head_sha','other'), ('head_branch','other')])
def test_wrong_run_rejected(tmp_path, monkeypatch, key, value):
    root, run, _, _, _ = bundle(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='provenance'):
        route.validate_bundle(root, dict(run, **{key:value}))


@pytest.mark.parametrize('key,value', [('clean_synthesis',False), ('source_artifact_downloaded',True),
    ('exact_source_reproduced',False), ('repaired_measured_gates_pass',False), ('qualified',True),
    ('official_signoff',True), ('final_state','other.json')])
def test_receipt_claims_alone_never_authorize_other_sources(tmp_path, monkeypatch, key, value):
    root, run, bound, receipt, path = bundle(tmp_path, monkeypatch)
    receipt[key] = value
    path.write_text(json.dumps(receipt))
    bound['files'][str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        route.validate_bundle(root, run)


def test_route_cannot_start_when_preparation_validation_fails(monkeypatch):
    monkeypatch.setattr(route, 'validate_checkpoint', lambda: (_ for _ in ()).throw(ValueError('bad source')))
    monkeypatch.setattr(route, 'continue_route', lambda *a, **kw: pytest.fail('DRT launched'))
    with pytest.raises(ValueError, match='bad source'):
        route.main()


@pytest.mark.parametrize('filename', ['gds-wire600-clean-route.yaml', 'l3-wire600-clean-gl.yaml'])
def test_workflows_pin_clean_source_and_shell_python_parse(filename):
    root = Path(__file__).resolve().parents[2]
    w = yaml.safe_load((root/'.github/workflows'/filename).read_text())
    job = next(iter(w['jobs'].values()))
    downloads = [s['with'] for s in job['steps'] if 'download-artifact@' in s.get('uses','')]
    assert downloads == [dict(name='wire600-clean-evidence-area1-39718836864',
                            path='.' if filename.startswith('gds') else 'artifacts',
                            **{'github-token':'${{ secrets.GITHUB_TOKEN }}',
                               'repository':'${{ github.repository }}', 'run-id':39718836864})]
    if filename.startswith('l3'):
        assert any('COCOTB_TEST_MODULES=test_l3' in s.get('run','') for s in job['steps'])
    for step in job['steps']:
        if 'run' not in step:
            continue
        script = step['run']
        subprocess.run(['bash','-n'],input=script,text=True,check=True)
        for marker in ("<<'PY'\n", "<<'PYCODE'\n"):
            if marker in script:
                end = marker.split("'")[1]
                ast.parse(script.split(marker,1)[1].split('\n'+end,1)[0])
