from copy import deepcopy
import pytest
from autonomy import cut_refinement as loop,corridor_solver as solver
from autonomy.tests.test_corridor_reduce import graph


@pytest.fixture
def setup(monkeypatch):
    p=dict(schema_version=1,max_additional=1,candidates=[dict(id='1',old_steps=1)],
        cuts=[dict(id='known',required_demand=1,crossing_demand={'1':0},
            resources=[dict(id='edge',capacity=1,fixed_usage=1,releases={'1':1})])])
    monkeypatch.setattr(loop.cut_cohort_native,'build',lambda *a,**k:dict(problem=deepcopy(p)))
    monkeypatch.setattr(loop.cut_cohort,'solve',lambda *a,**k:dict(status='FEASIBLE',selected=['1']))
    monkeypatch.setattr(loop.coarse_global,'build',lambda *a,**k:dict(graph=graph()))
    monkeypatch.setattr(loop.capacity_cut,'discover_partition_certificate',lambda *a:None)
    route_calls=[]
    def routing(g,**kw):
        route_calls.append(kw)
        return dict(status='UNKNOWN',graph_sha256=solver.digest(solver.canonical_bytes(g)),
            native_inputs_authenticated=False,physical_acceptance=False,timing_acceptance=False)
    monkeypatch.setattr(loop.corridor_mip,'solve',routing)
    return dict(baseline_slots=[0],records=[dict(model={},certificate={'fixture':'seed'})]),route_calls


def test_only_cut_clear_proposal_reaches_one_bounded_route_solve(setup):
    args,calls=setup;r=loop.run(None,None,**args)
    assert r['diagnostic_completed'] and r['termination']=='routing_UNKNOWN'
    assert calls==[dict(max_seconds=30,max_memory_mb=1024,max_variables=100000)]
    assert not r['native_route_installed'] and not r['physical_acceptance']


@pytest.mark.parametrize('status',['UNKNOWN','INFEASIBLE'])
def test_selection_failure_never_dispatches_routing(setup,monkeypatch,status):
    args,calls=setup;monkeypatch.setattr(loop.cut_cohort,'solve',lambda *a,**k:dict(status=status,selected=None))
    r=loop.run(None,None,**args)
    assert r['termination']=='selection_'+status and not calls


def test_new_certified_counterexamples_refine_to_finite_round_limit(setup,monkeypatch):
    args,calls=setup;seen=[]
    def cut(*a):
        c=dict(independently_verified_graph_infeasible=True,round=len(seen));seen.append(c);return c
    monkeypatch.setattr(loop.capacity_cut,'discover_partition_certificate',cut)
    r=loop.run(None,None,max_rounds=2,**args)
    assert r['termination']=='round_limit' and len(r['history'])==2 and not calls
    assert [e['known_cuts'] for e in r['history']]==[1,2]
    assert args['records']==[dict(model={},certificate={'fixture':'seed'})]


def test_repeated_counterexample_stops_as_error_and_preserves_history(setup,monkeypatch):
    args,calls=setup;monkeypatch.setattr(loop.capacity_cut,'discover_partition_certificate',lambda *a:dict(independently_verified_graph_infeasible=True))
    r=loop.run(None,None,max_rounds=3,**args)
    assert not r['diagnostic_completed'] and r['termination']=='error'
    assert 'Repeated counterexample' in r['error'] and len(r['history'])==2 and not calls


def test_bad_selection_cannot_reach_model_or_router(setup,monkeypatch):
    args,calls=setup;monkeypatch.setattr(loop.cut_cohort,'solve',lambda *a,**k:dict(status='FEASIBLE',selected=['missing']))
    r=loop.run(None,None,**args)
    assert r['termination']=='error' and not calls and 'route_model' not in r['history'][0]


@pytest.mark.parametrize('field,value',[('graph_sha256','changed'),('physical_acceptance',True),('status','INVALID')])
def test_bad_routing_status_identity_or_authority_stays_error(setup,monkeypatch,field,value):
    args,calls=setup;old=loop.corridor_mip.solve
    def routing(*a,**k):r=old(*a,**k);r[field]=value;return r
    monkeypatch.setattr(loop.corridor_mip,'solve',routing)
    r=loop.run(None,None,**args)
    assert not r['diagnostic_completed'] and r['termination']=='error'
    assert 'routing_solution' in r['history'][0]


def test_feasible_proposal_must_expand_and_pass_original_layer_check(setup,monkeypatch):
    args,_=setup;old=loop.corridor_mip.solve;checks=[]
    def routing(g,**kw):
        r=old(g,**kw);r.update(status='FEASIBLE',witness={'0':[e['id'] for e in g['edges']]});return r
    monkeypatch.setattr(loop.corridor_mip,'solve',routing)
    monkeypatch.setattr(loop.coarse_global,'allocate_and_check',lambda s,t,m,w:(checks.append(w) or {'scope':'fixture only'}))
    r=loop.run(None,None,**args)
    assert r['termination']=='routing_FEASIBLE' and checks==[{'0':['0','1','2']}]
    assert 'original_layer_check' in r['history'][0] and not r['native_route_installed']


@pytest.mark.parametrize('kw',[{'max_rounds':True},{'max_rounds':9},{'max_additional':0},{'max_variables':True}])
def test_bounds_reject_before_work(setup,kw):
    args,calls=setup
    with pytest.raises(ValueError):loop.run(None,None,**args,**kw)
    assert not calls


def test_stage_outputs_survive_later_failure(setup,monkeypatch,tmp_path):
    import json
    args,calls=setup
    def fail(*a,**k):raise ValueError('fixture admission failure')
    monkeypatch.setattr(loop.coarse_global,'build',fail)
    out=tmp_path/'stages';r=loop.run(None,None,output=out,**args)
    assert r['termination']=='error' and not calls
    assert json.loads((out/'round-0-selection.json').read_text())['status']=='FEASIBLE'
    assert json.loads((out/'summary.json').read_text())['diagnostic_completed'] is False


def test_existing_stage_directory_cannot_be_overwritten(setup,tmp_path):
    args,calls=setup;out=tmp_path/'preserved';out.mkdir();(out/'good').write_text('keep')
    with pytest.raises(FileExistsError):loop.run(None,None,output=out,**args)
    assert (out/'good').read_text()=='keep' and not calls
