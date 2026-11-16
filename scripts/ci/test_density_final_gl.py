import hashlib
import json
import zipfile

import pytest

import density_final_gl as final
from density_route import SOURCE_RUN, SOURCE_SHA
from selector_density_trial import select, encoded


def context():
    return (dict(id=final.ROUTE_RUN, head_sha=final.ROUTE_SHA,
                 head_branch='tripwire/closure-8x4', run_attempt=1,
                 path='.github/workflows/tripwire-density-route.yaml',
                 status='completed', conclusion='success'),
            dict(id=8, name=final.ARTIFACT_NAME, expired=False,
                 workflow_run=dict(id=final.ROUTE_RUN, head_sha=final.ROUTE_SHA),
                 digest='sha256:' + 'a' * 64))


@pytest.mark.parametrize('fault', ['failure', 'running', 'sha', 'artifact'])
def test_density_replay_refuses_foreign_or_failed_route(fault):
    run, artifact = context()
    final.source_context(run, artifact)
    if fault == 'failure': run['conclusion'] = 'failure'
    if fault == 'running': run['status'] = 'in_progress'
    if fault == 'sha': run['head_sha'] = 'wrong'
    if fault == 'artifact': artifact['workflow_run']['id'] = 1
    with pytest.raises(ValueError): final.source_context(run, artifact)


@pytest.mark.parametrize('explicit_recipe', [False, True])
def test_shared_replay_requires_exact_density_recipe_and_provenance(tmp_path, monkeypatch, explicit_recipe):
    import closure_final_gl as shared
    from test_closure_final_gl import fixture
    _, _, archive, expected, output = fixture(tmp_path, monkeypatch)
    with zipfile.ZipFile(archive) as z:
        members = {name: z.read(name) for name in z.namelist()}
    completion = json.loads(members['runs/closure-route/completion.json'])
    completion.update(source_run=SOURCE_RUN, source_sha=SOURCE_SHA)
    members['runs/closure-route/completion.json'] = json.dumps(completion).encode()
    config = encoded(select(json.loads(members['src/config.json'])))
    members['src/config.json'] = config.encode()
    (expected / 'src/config.json').write_text(config)
    with zipfile.ZipFile(archive, 'w') as z:
        for name, data in members.items(): z.writestr(name, data)
    run, artifact = context()
    artifact['digest'] = 'sha256:' + hashlib.sha256(archive.read_bytes()).hexdigest()
    views = json.loads(shared.SCREEN_RECEIPT.read_text())['frozen_views']
    kwargs = dict(admit=final.source_context, screen_identity=(SOURCE_RUN, SOURCE_SHA),
                  route_identity=(final.ROUTE_RUN, final.ROUTE_SHA), frozen_views=views)
    if not explicit_recipe:
        with pytest.raises(ValueError): shared.validate(run, artifact, archive, expected, output, **kwargs)
        assert not output.exists()
    else:
        result = shared.validate(run, artifact, archive, expected, output,
                                 config_sha=final.CONFIG_SHA, **kwargs)
        assert result['route_run'] == final.ROUTE_RUN
        assert result['exact_extracted_state_netlist'] is True


@pytest.mark.parametrize('policy', ['legacy', 'wrong_report', 'stock'])
def test_final_qualification_requires_actual_stock_constraints(tmp_path, monkeypatch, policy):
    import closure_final_gl as shared
    from test_closure_final_gl import fixture
    run, artifact, archive, expected, output = fixture(tmp_path, monkeypatch)
    with zipfile.ZipFile(archive) as z:
        members = {name: z.read(name) for name in z.namelist()}
    if policy != 'legacy':
        key = 'runs/closure-route/completion.json'
        completion = json.loads(members[key])
        completion.update(stock_signoff_constraints=True, clock_uncertainty_ns=0.25)
        members[key] = json.dumps(completion).encode()
        sdc = 'runs/extracted-timing/effective-stock-signoff.sdc'
        data = b'source $::env(SCRIPTS_DIR)/base.sdc\n'
        members[sdc] = data
        members['runs/extracted-timing/constraint_identity.json'] = json.dumps(dict(
            policy='stock-native-base-sdc', clock_uncertainty_ns=0.25,
            legacy_source_sdc_used=False, sta_constraint_file=sdc,
            sha256=hashlib.sha256(data).hexdigest())).encode()
        uncertainty = '0.100000' if policy == 'wrong_report' else '0.250000'
        for corner in shared.CORNERS:
            for report in ('max.rpt', 'min.rpt'):
                members[f'runs/extracted-timing/10-openroad-stapostpnr/{corner}/{report}'] = (
                    f'{corner}\n {uncertainty} 1.234567 clock uncertainty\n').encode()
    with zipfile.ZipFile(archive, 'w') as z:
        for name, data in members.items(): z.writestr(name, data)
    artifact['digest'] = 'sha256:' + hashlib.sha256(archive.read_bytes()).hexdigest()
    if policy != 'stock':
        with pytest.raises(ValueError):
            shared.validate(run, artifact, archive, expected, output, require_stock_constraints=True)
        assert not output.exists()
    else:
        result = shared.validate(run, artifact, archive, expected, output, require_stock_constraints=True)
        assert result['exact_extracted_state_netlist'] is True
