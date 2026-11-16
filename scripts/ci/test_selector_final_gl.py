import hashlib
import json
import zipfile
from pathlib import Path

import pytest
import yaml

import selector_final_gl as final
from selector_route import SOURCE_RUN, SOURCE_SHA, WORKFLOW, ARTIFACT_NAME


def context():
    return (dict(id=final.ROUTE_RUN, head_sha=final.ROUTE_SHA,
                 head_branch='tripwire/closure-8x4', run_attempt=1,
                 path='.github/workflows/tripwire-selector-route.yaml',
                 status='completed', conclusion='success'),
            dict(name=f'tripwire-selector-route-{final.ROUTE_RUN}', expired=False,
                 workflow_run=dict(id=final.ROUTE_RUN, head_sha=final.ROUTE_SHA),
                 digest='sha256:' + 'a' * 64))


@pytest.mark.parametrize('fault', ['failed', 'running', 'sha', 'attempt', 'artifact'])
def test_final_replay_requires_exact_successful_selector_route(fault):
    run, artifact = context()
    final.source_context(run, artifact)
    if fault == 'failed': run['conclusion'] = 'failure'
    if fault == 'running': run['status'] = 'in_progress'
    if fault == 'sha': run['head_sha'] = 'wrong'
    if fault == 'attempt': run['run_attempt'] = 2
    if fault == 'artifact': artifact['workflow_run']['id'] = 1
    with pytest.raises(ValueError): final.source_context(run, artifact)


@pytest.mark.parametrize('fault', [None, 'digest', 'view', 'incomplete'])
def test_independent_original_screen_views_are_hash_bound(tmp_path, fault):
    run = dict(id=SOURCE_RUN, head_sha=SOURCE_SHA, head_branch='tripwire/closure-8x4',
               path=WORKFLOW, run_attempt=1, status='completed', conclusion='success')
    data = {f'runs/stock-official-baseline/{i}': str(i).encode() for i in range(6)}
    views = {name: hashlib.sha256(value).hexdigest() for name, value in data.items()}
    recorded = dict(views)
    if fault == 'view': recorded[next(iter(recorded))] = '0' * 64
    if fault == 'incomplete': recorded.pop(next(iter(recorded)))
    archive = tmp_path / 'screen.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        for name, value in data.items(): z.writestr(name, value)
        z.writestr('runs/stock-corner-audit/read_only_audit.json',
                   json.dumps(dict(unchanged_physical_view_hashes=recorded)))
    artifact = dict(name=ARTIFACT_NAME, expired=False,
                    workflow_run=dict(id=SOURCE_RUN, head_sha=SOURCE_SHA),
                    digest='sha256:' + hashlib.sha256(archive.read_bytes()).hexdigest())
    if fault == 'digest': artifact['digest'] = 'sha256:' + '0' * 64
    if fault is None: assert final.screen_views(run, artifact, archive) == views
    else:
        with pytest.raises(ValueError): final.screen_views(run, artifact, archive)


def test_workflow_keeps_real_protocol_replay_and_verifies_selector_inputs():
    root = Path(__file__).resolve().parents[2]
    w = yaml.safe_load((root / '.github/workflows/tripwire-selector-final-gl.yaml').read_text())
    steps = w['jobs']['replay']['steps']
    by_name = {step.get('name'): step for step in steps}
    replay = by_name['Replay 22 protocols on the exact extracted-state netlist']['run']
    original = yaml.safe_load((root / '.github/workflows/tripwire-closure-final-gl.yaml').read_text())
    reference = next(s['run'] for s in original['jobs']['replay']['steps']
                     if s.get('name') == 'Replay 22 protocols on the exact extracted-state netlist')
    assert replay == reference
    assert 'verify_expected' in by_name['Check actual XML and unchanged inputs']['run']
    admission = by_name['Authenticate qualified route and exact extracted-state netlist']['run']
    assert 'screen_archive=' in admission and 'screen_context(screen_run, screen_artifact)' in admission


@pytest.mark.parametrize('wrong_views', [False, True])
def test_shared_final_validator_keeps_all_gates_with_selector_provenance(tmp_path, monkeypatch, wrong_views):
    import closure_final_gl as shared
    from test_closure_final_gl import fixture
    _, _, archive, expected, output = fixture(tmp_path, monkeypatch)
    with zipfile.ZipFile(archive) as z:
        members = {name: z.read(name) for name in z.namelist()}
    key = 'runs/closure-route/completion.json'
    completion = json.loads(members[key])
    completion.update(source_run=SOURCE_RUN, source_sha=SOURCE_SHA)
    members[key] = json.dumps(completion).encode()
    with zipfile.ZipFile(archive, 'w') as z:
        for name, data in members.items(): z.writestr(name, data)
    run, artifact = context()
    artifact.update(id=7, digest='sha256:' + hashlib.sha256(archive.read_bytes()).hexdigest())
    views = {} if wrong_views else json.loads(shared.SCREEN_RECEIPT.read_text())['frozen_views']
    kwargs = dict(admit=final.source_context, screen_identity=(SOURCE_RUN, SOURCE_SHA),
                  route_identity=(final.ROUTE_RUN, final.ROUTE_SHA), frozen_views=views)
    if wrong_views:
        with pytest.raises(ValueError): shared.validate(run, artifact, archive, expected, output, **kwargs)
        assert not output.exists()
    else:
        receipt = shared.validate(run, artifact, archive, expected, output, **kwargs)
        assert receipt['route_run'] == final.ROUTE_RUN
        assert receipt['exact_extracted_state_netlist'] is True
