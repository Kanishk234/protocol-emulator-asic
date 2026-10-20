import hashlib
import json
from pathlib import Path
import pytest
from autonomy import native_solver_campaign as campaign,corridor_solver as model
from autonomy.tests.test_capacity_cut import graph


@pytest.fixture
def inputs(tmp_path,monkeypatch):
    bundle=tmp_path/'bundle';stage=bundle/'default_identity/replay/1-openroad-globalrouting';stage.mkdir(parents=True)
    raw,term,segments=b'raw-fixture',b'term-fixture',b'segments-fixture'
    (stage/'corridor-initial').mkdir();(stage/'terminal-initial').mkdir()
    (stage/'corridor-initial/native-corridor.tsv').write_bytes(raw)
    (stage/'terminal-initial/native-terminals.tsv').write_bytes(term)
    (stage/'initial-segments.txt').write_bytes(segments)
    monkeypatch.setattr(campaign,'RAW_SHA',hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(campaign,'TERMINAL_SHA',hashlib.sha256(term).hexdigest())
    monkeypatch.setattr(campaign.repair_evidence.hosted,'EXPECTED_SEGMENTS',hashlib.sha256(segments).hexdigest())
    calls=[]
    monkeypatch.setattr(campaign.capacity_cut,'discover_partition_certificate',lambda g:None)
    monkeypatch.setattr(campaign.repair_evidence,'audit',lambda *a,**k:(calls.append('audit') or {'result_sha256':'a'*64}))
    monkeypatch.setattr(campaign.native_corridor,'parse_bytes',lambda *a:'raw')
    monkeypatch.setattr(campaign.native_terminals,'parse_bytes',lambda *a:'term')
    def make(capacity):
        g=graph(capacity)
        for n in g['nodes']:n['x']+=16
        return {'graph':model.validate_graph(g)}
    monkeypatch.setattr(campaign.corridor_extract,'extract',lambda *a,**k:make(4))
    monkeypatch.setattr(campaign.coarse_global,'build',lambda *a,**k:make(5))
    def solve(g,**kw):
        assert kw==dict(max_seconds=30,max_memory_mb=1024,max_variables=100000)
        calls.append('solve')
        return dict(status='INFEASIBLE' if g['edges'][0]['capacity']==4 else 'UNKNOWN',
            graph_sha256=model.digest(model.canonical_bytes(g)),model_size={'nodes':2},
            native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False)
    monkeypatch.setattr(campaign.corridor_solver,'solve',solve)
    kwargs=dict(revision='b'*40,run_id='123',attempt=1,output=tmp_path/'out')
    return bundle,kwargs,calls,stage


def test_bounded_campaign_retains_unknown_without_promoting(inputs):
    bundle,kwargs,calls,_=inputs;r=campaign.run(bundle,{},**kwargs)
    assert calls==['audit','solve','solve']
    assert r['diagnostic_completed'] and r['local']['independent_cut_infeasible']
    assert r['global']['status']=='UNKNOWN' and not r['physical_acceptance']
    assert json.loads((kwargs['output']/'summary.json').read_text())==r


def test_extractor_consumes_the_same_segment_buffer_that_was_hashed(inputs,monkeypatch):
    bundle,kwargs,calls,stage=inputs;original=Path.read_text
    def reject_second_read(path,*a,**k):
        if path==stage/'initial-segments.txt':pytest.fail('Segments must not be reread after their hash gate')
        return original(path,*a,**k)
    monkeypatch.setattr(Path,'read_text',reject_second_read)
    def extract(snapshot,terminals,text,**kw):
        assert text=='segments-fixture'
        g=graph(4)
        for n in g['nodes']:n['x']+=16
        return {'graph':model.validate_graph(g)}
    monkeypatch.setattr(campaign.corridor_extract,'extract',extract)
    assert campaign.run(bundle,{},**kwargs)['diagnostic_completed']


def test_failed_authentication_prevents_any_model_or_solver(inputs,monkeypatch):
    bundle,kwargs,calls,_=inputs
    def fail(*a,**kw):raise ValueError('Invalid API identity')
    monkeypatch.setattr(campaign.repair_evidence,'audit',fail)
    with pytest.raises(ValueError,match='API identity'):campaign.run(bundle,{},**kwargs)
    assert not calls and not kwargs['output'].exists()


@pytest.mark.parametrize('filename',['corridor-initial/native-corridor.tsv','terminal-initial/native-terminals.tsv','initial-segments.txt'])
def test_changed_checkpoint_rejected_before_solving(inputs,filename):
    bundle,kwargs,calls,stage=inputs;(stage/filename).write_text('tampered')
    with pytest.raises(ValueError):campaign.run(bundle,{},**kwargs)
    assert calls==['audit'] and not kwargs['output'].exists()


def test_existing_good_output_cannot_be_overwritten(inputs):
    bundle,kwargs,calls,_=inputs;kwargs['output'].mkdir();(kwargs['output']/'good').write_text('keep')
    with pytest.raises(FileExistsError):campaign.run(bundle,{},**kwargs)
    assert (kwargs['output']/'good').read_text()=='keep' and calls==['audit']


def test_solver_failure_is_retained_as_error_not_unknown(inputs,monkeypatch):
    bundle,kwargs,calls,_=inputs
    def fail(*a,**k):raise RuntimeError('Solver model invalid')
    monkeypatch.setattr(campaign.corridor_solver,'solve',fail)
    with pytest.raises(RuntimeError):campaign.run(bundle,{},**kwargs)
    r=json.loads((kwargs['output']/'summary.json').read_text())
    assert not r['diagnostic_completed'] and 'invalid' in r['error']


def test_unknown_backend_rejected_without_fetch_or_execution(inputs):
    bundle,kwargs,calls,_=inputs
    with pytest.raises(ValueError,match='backend'):campaign.run(bundle,{},backend='arbitrary',**kwargs)
    assert not calls


@pytest.mark.parametrize('field,value',[('graph_sha256','f'*64),('physical_acceptance',True),('status','MODEL_INVALID')])
def test_backend_cannot_change_graph_identity_scope_or_status(inputs,monkeypatch,field,value):
    bundle,kwargs,calls,_=inputs;original=campaign.corridor_solver.solve
    def corrupt(*a,**k):r=original(*a,**k);r[field]=value;return r
    monkeypatch.setattr(campaign.corridor_solver,'solve',corrupt)
    with pytest.raises(ValueError):campaign.run(bundle,{},**kwargs)
    assert not json.loads((kwargs['output']/'summary.json').read_text())['diagnostic_completed']


def test_campaign_retains_independent_global_certificate(inputs,monkeypatch):
    bundle,kwargs,_,_=inputs
    certificate={'independently_verified_graph_infeasible':True,'fixture':'independent-cut'}
    monkeypatch.setattr(campaign.capacity_cut,'discover_partition_certificate',lambda g:certificate)
    result=campaign.run(bundle,{},**kwargs)
    assert result['global']['independent_cut_infeasible']
    assert json.loads((kwargs['output']/'global-cut.json').read_text())==certificate
    assert result['global']['status']=='UNKNOWN'


def test_campaign_refuses_feasible_solver_contradicting_global_cut(inputs,monkeypatch):
    bundle,kwargs,_,_=inputs;original=campaign.corridor_solver.solve
    def solve(g,**kw):
        r=original(g,**kw)
        if r['status']=='UNKNOWN':r['status']='FEASIBLE'
        return r
    monkeypatch.setattr(campaign.corridor_solver,'solve',solve)
    monkeypatch.setattr(campaign.capacity_cut,'discover_partition_certificate',lambda g:{'independently_verified_graph_infeasible':True})
    with pytest.raises(ValueError,match='independent global capacity cut'):campaign.run(bundle,{},**kwargs)
    assert not json.loads((kwargs['output']/'summary.json').read_text())['diagnostic_completed']
