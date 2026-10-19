"""Identity and retained-result tamper checks for read-only native repair audit."""
import json
from pathlib import Path
import pytest
from autonomy import repair_evidence as audit

REV = 'a'*40


def identity():
    return dict(id=123, head_sha=REV, run_attempt=2, head_branch='efpga',
                name='controlled native pair repair', status='completed', conclusion='success')


def result():
    return dict(source_revision=REV, workflow_run='123', workflow_attempt='2',
                diagnostic_completed=True, physical_acceptance=False)


@pytest.mark.parametrize('key,value', [('id',124), ('head_sha','b'*40), ('run_attempt',1),
    ('head_branch','main'), ('status','in_progress'), ('conclusion','failure'), ('name','unit')])
def test_rejects_wrong_api_identity(key,value):
    i=identity();i[key]=value
    with pytest.raises(ValueError):
        audit.check_identity(i,result(),revision=REV,run_id='123',attempt=2)


@pytest.mark.parametrize('key,value', [('source_revision','b'*40), ('workflow_run','124'),
    ('workflow_attempt','1'), ('diagnostic_completed',False), ('physical_acceptance',True)])
def test_rejects_wrong_collector_identity_or_promotion(key,value):
    r=result();r[key]=value
    with pytest.raises(ValueError):
        audit.check_identity(identity(),r,revision=REV,run_id='123',attempt=2)


@pytest.mark.parametrize('revision,run_id,attempt', [('main','123',2),(REV,'0',2),
    (REV,'123',True),(REV,'123',0),(REV,'123',1.5)])
def test_requires_explicit_exact_expected_identity(revision,run_id,attempt):
    with pytest.raises(ValueError):
        audit.check_identity(identity(),result(),revision=revision,run_id=run_id,attempt=attempt)


def test_accepts_exact_identity():
    audit.check_identity(identity(),result(),revision=REV,run_id='123',attempt=2)


def fixture(tmp_path,monkeypatch):
    r=result();r['patch_sha256']='0'*64
    base=dict(final_observed_full_grid_overflow=121,native_repair_passed=False,
              native_error='GRT-0116',physical_acceptance=False)
    r['cases']={name:dict(base) for name in ('default_identity','forced_pair')}
    r['cases']['forced_pair']['observer']={'passes':[]}
    for name in r['cases']:
        (tmp_path/name/'replay'/'1-openroad-globalrouting').mkdir(parents=True)
    (tmp_path/'result.json').write_text(json.dumps(r))
    monkeypatch.setattr(audit,'source_hash',lambda *a:'0'*64)
    monkeypatch.setattr(audit.hosted,'validate_stage',lambda *a:dict(base))
    monkeypatch.setattr(audit.hosted,'validate_observer',lambda *a:{'passes':[]})
    return r


def test_reparses_instead_of_trusting_stored_success(tmp_path,monkeypatch):
    r=fixture(tmp_path,monkeypatch)
    output=audit.audit(tmp_path,identity(),revision=REV,run_id='123',attempt=2)
    assert output['verified'] and output['physical_acceptance'] is False
    r['cases']['forced_pair']['native_repair_passed']=True
    (tmp_path/'result.json').write_text(json.dumps(r))
    with pytest.raises(ValueError,match='contradicts'):
        audit.audit(tmp_path,identity(),revision=REV,run_id='123',attempt=2)


def test_old_observer_cannot_be_presented_as_candidate(tmp_path,monkeypatch):
    fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match='cases'):
        audit.audit(tmp_path,identity(),revision=REV,run_id='123',attempt=2,candidate=True)


def test_rejects_linked_evidence(tmp_path,monkeypatch):
    fixture(tmp_path,monkeypatch)
    (tmp_path/'linked').symlink_to(tmp_path/'result.json')
    with pytest.raises(ValueError,match='Linked'):
        audit.audit(tmp_path,identity(),revision=REV,run_id='123',attempt=2)


def corridor_fixture(tmp_path,monkeypatch):
    """Isolate portable-adapter delegation; retain a real native TSV parser."""
    from autonomy.native_corridor import audit_file
    r=fixture(tmp_path,monkeypatch)
    r['used_grid_patch_sha256']='0'*64
    r['corridor_observer_patch_sha256']='0'*64
    r['cases']['rebuilt_pair']=dict(r['cases']['default_identity'])
    (tmp_path/'rebuilt_pair/replay/1-openroad-globalrouting').mkdir(parents=True)
    for name,row in r['cases'].items():row['used_grid_rebuild_calls']=5 if name=='rebuilt_pair' else 0
    monkeypatch.setattr(audit.hosted,'validate_rebuild_witness',lambda stage,name:5 if name=='rebuilt_pair' else 0)
    # One unit-cost native tree step accounts for the one used raw edge.
    raw='''SCHEMA\twarp-native-corridor-v1
INDEXING\tzero_based_fast_route_layers_and_grid
MODEL_GATE\tusage_ledger_verified\tfalse
VIA_MODEL\tglobal_route_steps_only_no_physical_cut_capacity
GRID\t2\t2\t1\t0\t0\t100
EDGE\tH\t0\t0\t0\t1\t1\t0\t1
EDGE\tH\t0\t0\t1\t1\t0\t0\t1
EDGE\tV\t0\t0\t0\t1\t0\t0\t1
EDGE\tV\t0\t1\t0\t1\t0\t0\t1
NET\t0\t11\tnet\t0\t0\t1\t0\t0\t0\t2
DEMAND\t0\t0\t1
PIN\t0\t0\t0\t0\t0
PIN\t0\t1\t1\t0\t0
TREE\t0\t2\t2\t1
TREE_EDGE\t0\t0\t1\t0\t1\t0\t1\t1\t2
STEP\t0\t0\t0\t0\t0\t0\t1\t0\t0\t1
COMPLETE\t1\t1\t1
'''
    stages={}
    for name in r['cases']:
        stages[name]=tmp_path/name/'replay/1-openroad-globalrouting'
        for phase in ('initial','final'):
            directory=stages[name]/('corridor-'+phase);directory.mkdir()
            (directory/'native-corridor.tsv').write_text(raw)
    calls=[]
    def qualify(actual_stages,actual_cases):
        assert set(actual_cases)==set(r['cases']) and actual_stages==stages
        calls.append('requalified')
        rows={name:{phase:audit_file(stage/('corridor-'+phase)/'native-corridor.tsv')
                    for phase in ('initial','final')} for name,stage in actual_stages.items()}
        return {'model_gate':all(row['model_gate']=='PASS' for phases in rows.values() for row in phases.values()),
                'observations':rows,'native_inputs_authenticated':False,'physical_acceptance':False}
    monkeypatch.setattr(audit.hosted,'qualify_native_corridors',qualify)
    r['native_corridor']=qualify(stages,r['cases']);calls.clear()
    (tmp_path/'result.json').write_text(json.dumps(r))
    return r,calls


def test_native_corridor_mode_requires_candidate_and_explicit_optin(tmp_path,monkeypatch):
    corridor_fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match='candidate mode'):
        audit.audit(tmp_path,identity(),revision=REV,run_id='123',attempt=2,native_corridor=True)
    with pytest.raises(ValueError,match='explicit native-corridor'):
        audit.audit(tmp_path,identity(),revision=REV,run_id='123',attempt=2,candidate=True)


def test_native_corridor_reaudits_all_six_files(tmp_path,monkeypatch):
    _,calls=corridor_fixture(tmp_path,monkeypatch)
    result=audit.audit(tmp_path,identity(),revision=REV,run_id='123',attempt=2,candidate=True,native_corridor=True)
    assert calls==['requalified'] and result['native_corridor']['model_gate']
    assert not result['native_corridor']['native_inputs_authenticated']


@pytest.mark.parametrize('value',[None,'1'*64])
def test_native_corridor_patch_must_match_git_object(tmp_path,monkeypatch,value):
    r,calls=corridor_fixture(tmp_path,monkeypatch)
    if value is None:r.pop('corridor_observer_patch_sha256')
    else:r['corridor_observer_patch_sha256']=value
    (tmp_path/'result.json').write_text(json.dumps(r))
    with pytest.raises(ValueError,match='observer patch'):
        audit.audit(tmp_path,identity(),revision=REV,run_id='123',attempt=2,candidate=True,native_corridor=True)
    assert not calls


def test_native_corridor_valid_accounting_tamper_contradicts_stored_result(tmp_path,monkeypatch):
    corridor_fixture(tmp_path,monkeypatch)
    path=tmp_path/'rebuilt_pair/replay/1-openroad-globalrouting/corridor-final/native-corridor.tsv'
    path.write_text(path.read_text().replace('EDGE\tH\t0\t0\t0\t1\t1\t','EDGE\tH\t0\t0\t0\t1\t2\t'))
    with pytest.raises(ValueError,match='contradicts independently audited exports'):
        audit.audit(tmp_path,identity(),revision=REV,run_id='123',attempt=2,candidate=True,native_corridor=True)


def test_native_corridor_honest_ledger_failure_remains_valid_diagnostic(tmp_path,monkeypatch):
    r,_=corridor_fixture(tmp_path,monkeypatch)
    path=tmp_path/'rebuilt_pair/replay/1-openroad-globalrouting/corridor-final/native-corridor.tsv'
    path.write_text(path.read_text().replace('EDGE\tH\t0\t0\t0\t1\t1\t','EDGE\tH\t0\t0\t0\t1\t2\t'))
    stages={name:tmp_path/name/'replay/1-openroad-globalrouting' for name in r['cases']}
    r['native_corridor']=audit.hosted.qualify_native_corridors(stages,r['cases'])
    (tmp_path/'result.json').write_text(json.dumps(r))
    output=audit.audit(tmp_path,identity(),revision=REV,run_id='123',attempt=2,candidate=True,native_corridor=True)
    assert output['verified'] and output['native_corridor']['model_gate'] is False
    assert output['physical_acceptance'] is False


def test_native_corridor_truncation_is_not_diagnostic_success(tmp_path,monkeypatch):
    corridor_fixture(tmp_path,monkeypatch)
    path=tmp_path/'forced_pair/replay/1-openroad-globalrouting/corridor-initial/native-corridor.tsv'
    path.write_bytes(path.read_bytes()[:-10])
    with pytest.raises(ValueError):
        audit.audit(tmp_path,identity(),revision=REV,run_id='123',attempt=2,candidate=True,native_corridor=True)


def test_native_corridor_stored_gate_forgery_rejected(tmp_path,monkeypatch):
    r,_=corridor_fixture(tmp_path,monkeypatch);r['native_corridor']['physical_acceptance']=True
    (tmp_path/'result.json').write_text(json.dumps(r))
    with pytest.raises(ValueError,match='contradicts independently audited exports'):
        audit.audit(tmp_path,identity(),revision=REV,run_id='123',attempt=2,candidate=True,native_corridor=True)
