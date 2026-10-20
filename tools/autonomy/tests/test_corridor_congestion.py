from copy import deepcopy
from importlib.util import find_spec
import itertools
import pytest
from autonomy import corridor_congestion as congestion
from autonomy.tests.test_corridor_solver import graph
from autonomy.tests.test_capacity_cut import graph as private_graph
requires_solver=pytest.mark.skipif(find_spec('ortools') is None,reason='optional routing solver')


def fixture(caps=(1,1,1),fixed=0,nets=1,demand=1):
    g=graph();g['edges']=g['edges'][:2]+[dict(id='ac',u='a',v='c',direction='horizontal',capacity=1,fixed_usage=0)]
    for e,cap in zip(g['edges'],caps):e.update(capacity=cap,fixed_usage=fixed)
    n=g['nets'][0];g['nets']=[]
    for i in range(nets):
        item=deepcopy(n);item['id']=str(i);item['track_demand_by_layer']['M1']=demand;g['nets'].append(item)
    return g


def oracle(g):
    choices=[]
    for n in g['nets']:
        possible=[]
        for bits in itertools.product((0,1),repeat=len(g['edges'])):
            if any(on and e['capacity']==0 for on,e in zip(bits,g['edges'])):continue
            seen={n['terminals'][0]}
            for _ in g['nodes']:
                for on,e in zip(bits,g['edges']):
                    if on and ({e['u'],e['v']}&seen):seen.update((e['u'],e['v']))
            if set(n['terminals'])<=seen:possible.append(bits)
        choices.append(possible)
    costs=[]
    for routes in itertools.product(*choices):
        over=sum(max(0,e['fixed_usage']+sum(route[i]*n['track_demand_by_layer']['M1'] for route,n in zip(routes,g['nets']))-e['capacity']) for i,e in enumerate(g['edges']))
        costs.append((over,sum(sum(route) for route in routes)))
    return min(costs) if costs else None


@requires_solver
@pytest.mark.parametrize('caps,fixed,nets,demand',itertools.product(itertools.product((1,2),repeat=3),(0,3),(1,2),(1,2)))
def test_congestion_objective_matches_independent_subset_oracle(caps,fixed,nets,demand):
    g=fixture(caps,fixed,nets,demand);before=deepcopy(g);expected=oracle(g)
    r=congestion.solve(g,max_overflow=50)
    assert r['status']=='PROPOSAL' and r['optimal']
    assert (r['witness_check']['total_overflow'],sum(len(v) for v in r['witness'].values()))==expected
    assert r['witness_check']==congestion.check(g,r['witness'],max_overflow=50)
    assert not r['physical_acceptance'] and not r['native_route_installed'] and g==before


@requires_solver
def test_budget_is_enforced_without_changing_original_capacity():
    g=fixture(caps=(1,1,1),fixed=1,nets=2)
    assert oracle(g)[0]==2
    assert congestion.solve(g,max_overflow=1)['status']=='INFEASIBLE'
    r=congestion.solve(g,max_overflow=2)
    assert r['status']=='PROPOSAL' and r['witness_check']['total_overflow']==2
    assert not r['witness_check']['capacity_feasible']
    assert all(e['capacity']==1 for e in g['edges'])


@requires_solver
def test_zero_capacity_planar_shortcut_is_not_accepted_as_overuse_proposal():
    g=fixture(caps=(1,1,0))
    r=congestion.solve(g,max_overflow=5)
    assert r['witness']=={'0':['ab','bc']} and r['witness_check']['total_overflow']==0
    with pytest.raises(ValueError,match='Zero-capacity'):congestion.check(g,{'0':['ac']},max_overflow=5)


@requires_solver
def test_private_exterior_connection_cannot_be_borrowed_by_another_net():
    g=private_graph(capacity=1);g['nets']=g['nets'][:1]
    g['nets'][0]['frozen_exterior_components']=[['left','right']]
    g['edges'][0]['fixed_usage']=1
    r=congestion.solve(g,max_overflow=0)
    assert r['witness']=={'0':[]}
    other=deepcopy(g['nets'][0]);other.update(id='other',frozen_exterior_components=[]);g['nets'].append(other)
    assert congestion.solve(g,max_overflow=0)['status']=='INFEASIBLE'


@pytest.mark.parametrize('witness',[{'0':[]},{'0':['missing']},{'0':['ac','ac']},{'other':['ac']}])
def test_independent_checker_rejects_invalid_connectivity_or_inventory(witness):
    with pytest.raises(ValueError):congestion.check(fixture(),witness,max_overflow=5)


def test_independent_checker_rejects_actual_overuse_above_budget():
    with pytest.raises(ValueError,match='budget'):congestion.check(fixture(fixed=3),{'0':['ac']},max_overflow=0)


@pytest.mark.parametrize('kwargs',[{'max_overflow':True},{'max_overflow':-1},{'max_overflow':0,'max_variables':1}])
def test_invalid_limits_reject_before_solver_import(kwargs):
    with pytest.raises(ValueError):congestion.solve(fixture(),**kwargs)


@requires_solver
def test_explicit_old_zero_capacity_permission_preserves_baseline_without_credit():
    g=fixture(caps=(1,1,0));g['edges']=g['edges'][-1:]
    assert congestion.solve(g,max_overflow=1)['status']=='INFEASIBLE'
    permission={'0':['ac']};r=congestion.solve(g,max_overflow=1,zero_capacity_permissions=permission)
    assert r['status']=='PROPOSAL' and r['witness_check']['total_overflow']==1
    assert g['edges'][0]['capacity']==0
    n=deepcopy(g['nets'][0]);n['id']='other';g['nets'].append(n)
    assert congestion.solve(g,max_overflow=2,zero_capacity_permissions={'0':['ac'],'other':[]})['status']=='INFEASIBLE'


@pytest.mark.parametrize('permission',[{'other':[]},{'0':['missing']},{'0':['ac']},{'0':['ab','ab']}])
def test_invalid_zero_resource_permissions_rejected(permission):
    with pytest.raises(ValueError):congestion.check(fixture(),{'0':['ac']},max_overflow=5,zero_capacity_permissions=permission)
