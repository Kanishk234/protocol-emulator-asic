import hashlib
import json
from pathlib import Path
import zipfile

import pytest
import yaml

import selector_drt_final_gl as final
from test_closure_final_gl import fixture as route_fixture
from test_selector_drt_diagnostic import metadata
from selector_drt_diagnostic import assess
from closure_final_gl import RUNNER_ROOT
from postgrt_timing import CORNERS


def context():
    run = dict(id=final.ROUTE_RUN, head_sha=final.ROUTE_SHA,
               head_branch='tripwire/closure-8x4', run_attempt=1,
               path='.github/workflows/tripwire-selector-drt-diagnostic.yaml',
               status='completed', conclusion='success')
    artifact = dict(id=42, name=final.ARTIFACT_NAME, expired=False,
                    workflow_run=dict(id=final.ROUTE_RUN, head_sha=final.ROUTE_SHA),
                    digest='sha256:' + 'a' * 64)
    return run, artifact


@pytest.mark.parametrize('fault', ['failed', 'sha', 'attempt', 'artifact', 'expired'])
def test_requires_exact_successful_measured_diagnostic(fault):
    run, artifact = context()
    final.source_context(run, artifact)
    if fault == 'failed': run['conclusion'] = 'failure'
    if fault == 'sha': run['head_sha'] = 'foreign'
    if fault == 'attempt': run['run_attempt'] = 2
    if fault == 'artifact': artifact['workflow_run']['id'] = 1
    if fault == 'expired': artifact['expired'] = True
    with pytest.raises(ValueError): final.source_context(run, artifact)


def fixture(tmp_path, monkeypatch, fault=None):
    _, _, archive, expected, output = route_fixture(tmp_path, monkeypatch)
    with zipfile.ZipFile(archive) as z:
        members = {n: z.read(n) for n in z.namelist()}
    old = 'runs/closure-route'
    prefix = final.PREFIX
    completion = json.loads(members.pop(old + '/completion.json'))
    members = {n.replace(old, prefix + '/route'): b.replace(old.encode(), (prefix + '/route').encode())
               for n, b in members.items()}
    timing = json.loads(members['runs/extracted-timing/corner_summary.json'])
    electrical = json.loads(members['runs/extracted-timing/electrical_summary.json'])
    antenna = dict(antenna__violating__nets=0, antenna__violating__pins=0)
    result = assess(timing, electrical, antenna)
    result.update(source_run=final.SOURCE_RUN, source_sha=final.SOURCE_SHA,
                  native_stock_constraints=True, clock_uncertainty_ns=0.25,
                  logical_connectivity_preserved=True, source_views=completion['source_views'],
                  extracted_timing=timing, extracted_electrical=electrical, final_antenna=antenna)
    if fault == 'promotion': result['release_qualified'] = True
    members[prefix + '/diagnostic_result.json'] = json.dumps(result).encode()
    members[prefix + '/final-native-checks/1-openroad-checkantennas/or_metrics_out.json'] = json.dumps(
        dict(antenna, antenna__violating__nets=1) if fault == 'antenna' else antenna).encode()
    members[prefix + '/final-native-checks/4-checker-disconnectedpins/state_out.json'] = json.dumps(
        dict(metrics={'design__critical_disconnected_pin__count': 1 if fault == 'disconnected' else 0})).encode()
    sdc = b'source $::env(SCRIPTS_DIR)/base.sdc\n'
    members['runs/extracted-timing/effective-stock-signoff.sdc'] = sdc
    members['runs/extracted-timing/constraint_identity.json'] = json.dumps(dict(
        policy='stock-native-base-sdc', clock_uncertainty_ns=0.25, legacy_source_sdc_used=False,
        sta_constraint_file=str(RUNNER_ROOT / 'runs/extracted-timing/effective-stock-signoff.sdc'),
        sha256=hashlib.sha256(sdc).hexdigest())).encode()
    for corner in CORNERS:
        for name in ('max.rpt', 'min.rpt'):
            value = '0.10' if fault == 'uncertainty' else '0.25'
            members[f'runs/extracted-timing/10-openroad-stapostpnr/{corner}/{name}'] = f'{value} 0.25 clock uncertainty'.encode()
    if fault == 'timing':
        timing[f'timing__setup__ws__corner:{CORNERS[1]}'] = -1
        members['runs/extracted-timing/corner_summary.json'] = json.dumps(timing).encode()
    if fault == 'logic':
        n = 'runs/extracted-timing/7-openroad-fillinsertion/chip.nl.v'
        members[n] = members[n].replace(b'.A(a)', b'.A(wrong)')
    if fault == 'source': members['src/new.v'] = b'foreign'
    if fault == 'wrong_stage':
        n = 'runs/extracted-timing/10-openroad-stapostpnr/state_out.json'
        state = json.loads(members[n]); state['nl'] = 'runs/stock-official-baseline/wrong.v'
        members[n] = json.dumps(state).encode()
    with zipfile.ZipFile(archive, 'w') as z:
        for name, data in members.items(): z.writestr(name, data)
    run, artifact = context()
    artifact['digest'] = 'sha256:' + hashlib.sha256(archive.read_bytes()).hexdigest()
    if fault == 'digest': artifact['digest'] = 'sha256:' + '0' * 64
    screen_run, screen_artifact = metadata()
    # The separate source-screen archive/provenance adapter is covered by
    # test_selector_final_gl and test_selector_drt_diagnostic. Retain exact
    # source-view comparisons here while isolating the new result validation.
    monkeypatch.setattr(final, 'screen_views', lambda *a, **k: completion['source_views'])
    monkeypatch.setattr(final, 'verify_expected', lambda p: None)
    return (run, artifact, archive, expected, output), dict(
        screen_run=screen_run, screen_artifact=screen_artifact, screen_archive=Path('unused.zip'))


@pytest.mark.parametrize('fault', [None, 'promotion', 'antenna', 'disconnected',
    'uncertainty', 'timing', 'logic', 'source', 'wrong_stage', 'digest'])
def test_actual_diagnostic_gates_and_scope_before_replay(tmp_path, monkeypatch, fault):
    args, kwargs = fixture(tmp_path, monkeypatch, fault)
    if fault is None:
        receipt = final.validate(*args, **kwargs)
        assert args[-1].is_file()
        assert receipt['exact_extracted_state_netlist'] is True
        assert receipt['release_qualified'] is False and receipt['sdf_annotated'] is False
    else:
        with pytest.raises(ValueError): final.validate(*args, **kwargs)
        assert not args[-1].exists()


def test_cloud_followup_preserves_real_replay_and_diagnostic_scope():
    root = Path(__file__).resolve().parents[2]
    workflow = yaml.safe_load((root / '.github/workflows/tripwire-selector-drt-final-gl.yaml').read_text())
    baseline = yaml.safe_load((root / '.github/workflows/tripwire-density-final-gl.yaml').read_text())
    steps = {s.get('name'): s for s in workflow['jobs']['replay']['steps']}
    reference = next(s['run'] for s in baseline['jobs']['replay']['steps']
                     if s.get('name') == 'Replay 22 protocols on the exact extracted-state netlist')
    assert steps['Replay 22 protocols on the exact extracted-state netlist']['run'] == reference
    authentication = steps['Authenticate passing measurements and exact diagnostic netlist']['run']
    assert 'from selector_drt_final_gl import' in authentication
    assert 'from selector_drt_diagnostic import context as screen_context' in authentication
    assert 'screen_archive=' in authentication
    assert 'hardware_promoted' in steps['Check actual XML and unchanged inputs']['run']
    wait = workflow['jobs']['source-gate']['steps'][-1]['run']
    assert 'from selector_drt_final_gl import ROUTE_RUN, source_context' in wait
    assert 'source_context(run)' in wait
