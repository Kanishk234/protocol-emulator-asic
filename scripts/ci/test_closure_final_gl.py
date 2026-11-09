import hashlib
import json
from pathlib import Path
import zipfile

import pytest

import closure_final_gl as final
from test_closure_route import restored_fixture, timing


def context():
    return (dict(id=final.ROUTE_RUN, head_sha=final.ROUTE_SHA, head_branch='tripwire/closure-8x4',
                 path='.github/workflows/tripwire-closure-route.yaml', run_attempt=1,
                 status='completed', conclusion='success'),
            dict(id=123, name=f'tripwire-qualified-route-{final.ROUTE_RUN}', expired=False,
                 workflow_run=dict(id=final.ROUTE_RUN, head_sha=final.ROUTE_SHA),
                 digest='sha256:' + 'a' * 64))


@pytest.mark.parametrize('change', ['running', 'failed', 'foreignsha', 'rerun', 'artifact'])
def test_unqualified_route_or_artifact_cannot_start_replay(change):
    run, artifact = context()
    if change == 'running': run['status'] = 'in_progress'
    if change == 'failed': run['conclusion'] = 'failure'
    if change == 'foreignsha': run['head_sha'] = 'foreign'
    if change == 'rerun': run['run_attempt'] = 2
    if change == 'artifact': artifact['workflow_run']['id'] = 1
    with pytest.raises(ValueError): final.source_context(run, artifact)


@pytest.mark.parametrize('path', ['../outside.v', 'runs/stock-official-baseline/original.v',
                                '/other/runner/runs/closure-route/a.v'])
def test_wrong_stage_netlist_refused(path):
    with pytest.raises(ValueError): final.member(path, 'runs/closure-route')


def fixture(tmp_path, monkeypatch, *, inherited=False, change=None):
    _, frozen, expected = restored_fixture(tmp_path)
    known = {}
    members = {}
    for n in range(6):
        name = 'runs/stock-official-baseline/' + str(n)
        data = ('source view ' + str(n)).encode()
        members[name] = data; known[name] = hashlib.sha256(data).hexdigest()
    p = tmp_path / 'trusted-screen.json'; p.write_text(json.dumps({'frozen_views': known}))
    monkeypatch.setattr(final, 'SCREEN_RECEIPT', p)
    completion = dict(source_run=final.SOURCE_RUN, source_sha=final.SOURCE_SHA,
        detailed_routing_completed=True, extracted_timing_passed=True, route_drc_errors=0,
        final_antenna_nets=0, final_antenna_pins=0, disconnected_pin_checker_passed=True,
        minimum_fast_hold_ns=0.05, official_gds_signoff=False,
        routed_protocol_replay_performed=False, source_views=known)
    if change == 'incomplete': completion['extracted_timing_passed'] = False
    if change == 'source': completion['source_views'] = {}
    members['runs/closure-route/completion.json'] = json.dumps(completion).encode()
    for folder in ('src', 'macro'):
        for path in (expected / folder).rglob('*'):
            if path.is_file(): members[str(path.relative_to(expected))] = path.read_bytes()
    members['info.yaml'] = (expected / 'info.yaml').read_bytes()
    text = ('module tt_um_tripwire();\n'
            'sg13cmos5l_buf_2 b (.A(a), .X(x));\n'
            'RM_IHPSG13_1P_512x16_c2_bm_bist s (.CLK(clk));\nendmodule\n')
    route_nl = 'runs/closure-route/1-openroad-detailedrouting/chip.nl.v'
    extracted_nl = route_nl if inherited else 'runs/extracted-timing/7-openroad-fillinsertion/chip.nl.v'
    members[route_nl] = text.encode()
    members[extracted_nl] = text.replace('.A(a)', '.A(wrong)' if change == 'logic' else '.A(a)').encode()
    members['runs/closure-route/1-openroad-detailedrouting/state_out.json'] = json.dumps(
        dict(nl=str(final.RUNNER_ROOT / route_nl), metrics={'route__drc_errors': 0})).encode()
    members['runs/extracted-timing/10-openroad-stapostpnr/state_out.json'] = json.dumps(
        dict(nl=str(final.RUNNER_ROOT / extracted_nl))).encode()
    rows = timing()['corners']
    summary = {k: v for row in rows.values() for k, v in row['before'].items() if k.startswith('timing__')}
    if change == 'hold': summary[f'timing__hold__ws__corner:{final.CORNERS[0]}'] = -1
    members['runs/extracted-timing/corner_summary.json'] = json.dumps(summary).encode()
    members['runs/extracted-timing/electrical_summary.json'] = json.dumps(
        {c: {'counts': {'slew': 0, 'fanout': 0, 'capacitance': 0}} for c in final.CORNERS}).encode()
    archive = tmp_path / 'route.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        for name, data in members.items(): z.writestr(name, data)
    run, artifact = context(); artifact['digest'] = 'sha256:' + hashlib.sha256(archive.read_bytes()).hexdigest()
    return run, artifact, archive, expected, tmp_path / 'replay/netlist.v'


@pytest.mark.parametrize('inherited', [False, True])
def test_exact_extracted_or_inherited_route_netlist_selected(tmp_path, monkeypatch, inherited):
    args = fixture(tmp_path, monkeypatch, inherited=inherited)
    result = final.validate(*args)
    assert result['exact_extracted_state_netlist'] is True and result['sdf_annotated'] is False
    assert args[-1].is_file()


@pytest.mark.parametrize('change', ['incomplete', 'source', 'logic', 'hold'])
def test_final_replay_rejects_failed_gates_or_drift(tmp_path, monkeypatch, change):
    args = fixture(tmp_path, monkeypatch, change=change)
    with pytest.raises(ValueError): final.validate(*args)
    assert not args[-1].exists()
