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
