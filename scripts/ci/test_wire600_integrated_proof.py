import ast
import json
from pathlib import Path
import subprocess

import pytest
import yaml

import wire600_integrated_proof as trial


def live_run():
    return dict(id=123, head_sha='new-head', head_branch='main',
                path=trial.WORKFLOW, conclusion=None, status='in_progress')


def test_live_binding_uses_current_run_and_retains_physical_identity():
    p = trial.live_profile(live_run(), '123', 'new-head')
    b = p['binding']
    assert b['run_binding']['id'] == 123
    assert b['run_binding']['conclusion'] is None
    assert b['source_state'] in b['files']
    assert any(n.endswith('.odb') for n in b['files'])
    assert not any('process_stats' in n or n.endswith('.log') for n in b['files'])
    assert trial.route_profile()['binding']['run_binding']['id'] == 39856540600


@pytest.mark.parametrize('field,value', [('id', 5), ('head_sha', 'other'),
    ('head_branch', 'other'), ('conclusion', 'success'), ('status', 'completed'),
    ('path', '.github/workflows/other.yaml')])
def test_wrong_live_run_rejected(field, value):
    run = live_run()
    run[field] = value
    with pytest.raises(ValueError, match='provenance'):
        trial.live_profile(run, '123', 'new-head')


def test_fresh_workspace_required_before_any_flow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path/'runs/native-stock-screen').mkdir(parents=True)
    monkeypatch.setattr(trial, 'clean', lambda: pytest.fail('Flow must not start'))
    with pytest.raises(ValueError, match='fresh workspace'):
        trial.main()


def test_workflow_no_physical_download_and_real_precheck():
    root = Path(__file__).resolve().parents[2]
    text = (root/trial.WORKFLOW).read_text()
    w = yaml.safe_load(text)
    harden = w['jobs']['harden']
    assert harden['timeout-minutes'] <= 360
    assert not any('download-artifact' in s.get('uses', '') for s in harden['steps'])
    assert w['jobs']['precheck']['needs'] == 'harden'
    assert w['jobs']['precheck']['steps'] == [{'uses': 'TinyTapeout/tt-gds-action/precheck@ihp-cmos5l'}]
    assert 'Checker.LVS' in trial.TAIL
    assert 'Magic.DRC' not in trial.TAIL  # Merged-GDS DRC is the unchanged TT precheck.
    for s in harden['steps']:
        if 'run' not in s:
            continue
        subprocess.run(['bash', '-n'], input=s['run'], text=True, check=True)
        for marker in ("<<'PY'\n", "<<'PYCODE'\n"):
            if marker in s['run']:
                tag = marker.split("'")[1]
                ast.parse(s['run'].split(marker, 1)[1].split('\n'+tag, 1)[0])


@pytest.mark.parametrize('fault', [None, 'lvs', 'overlap', 'foreign_gds'])
def test_export_requires_fresh_outputs_and_preserves_precheck_requirement(tmp_path, monkeypatch, fault):
    output = tmp_path/'export'
    package = tmp_path/'package'

    def fake_run(config, state, dest, steps):
        dest.mkdir()
        for name in ('1-klayout-streamout', '2-magic-writelef',
                     '3-magic-spiceextraction', '4-netgen-lvs'):
            (dest/name).mkdir()
        gds = dest/'1-klayout-streamout/chip.gds'
        if fault == 'foreign_gds':
            gds = tmp_path/'foreign.gds'
        gds.write_bytes(b'fresh GDS fixture')
        lef = dest/'2-magic-writelef/chip.lef'
        lef.write_bytes(b'fresh LEF fixture')
        (dest/'1-klayout-streamout/state_out.json').write_text(json.dumps({'gds': str(gds)}))
        (dest/'2-magic-writelef/state_out.json').write_text(json.dumps({'lef': str(lef)}))
        extraction = dest/'3-magic-spiceextraction'
        item = "<item><category>'obsm4-metal4.ILLEGAL_OVERLAP'</category><values><value>polygon: (28.190,186.135;30.290,186.135;30.290,189.280;28.190,189.280)</value></values></item>"
        (extraction/'feedback.xml').write_text('<report-database><items>'+item*10+'</items></report-database>')
        (extraction/'state_out.json').write_text(json.dumps({'metrics': {
            'magic__illegal_overlap__count': 9 if fault == 'overlap' else 10}}))
        (dest/'4-netgen-lvs/state_out.json').write_text(json.dumps({'metrics': {
            'design__lvs_error__count': 1 if fault == 'lvs' else 0}}))

    monkeypatch.setattr(trial, 'run_step', fake_run)
    if fault:
        with pytest.raises(ValueError):
            trial.export_package({}, tmp_path/'state', output, package)
        assert not (package/'tt_submission/tt_um_tripwire.gds').exists()
    else:
        result = trial.export_package({}, tmp_path/'state', output, package)
        assert not result['precheck_passed'] and result['precheck_required']
        assert not result['magic_markers_waived']
        assert (package/'tt_submission/tt_um_tripwire.gds').read_bytes() == b'fresh GDS fixture'
