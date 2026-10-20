"""Small subset enumeration is independent of the mixed-integer formulation."""
from copy import deepcopy
from importlib.util import find_spec
import itertools
import pytest
from autonomy import cut_cohort as planner
requires_solver=pytest.mark.skipif(find_spec('ortools') is None,reason='optional routing solver')


def problem(cap=1,fixed=2,release=(1,1),demand=(0,0),required=1):
    return dict(schema_version=1,max_additional=2,
        candidates=[dict(id='a',old_steps=3),dict(id='b',old_steps=1)],
        cuts=[dict(id='cut',required_demand=required,crossing_demand=dict(zip(['a','b'],demand)),
            resources=[dict(id='edge',capacity=cap,fixed_usage=fixed,
                releases={i:r for i,r in zip(['a','b'],release) if r})])])


def oracle(p):
    ids=[c['id'] for c in p['candidates']];valid=[]
    for count in range(min(p['max_additional'],len(ids))+1):
        for selected in itertools.combinations(ids,count):
            ok=True
            for cut in p['cuts']:
                spare=0
                for r in cut['resources']:
                    usage=r['fixed_usage']
                    for i in selected:usage-=r['releases'].get(i,0)
                    if usage<r['capacity']:spare+=r['capacity']-usage
                traffic=cut['required_demand']+sum(cut['crossing_demand'][i] for i in selected)
                if spare<traffic:ok=False
            if ok:valid.append((len(selected),sum(c['old_steps'] for c in p['candidates'] if c['id'] in selected)))
    return min(valid) if valid else None


@requires_solver
@pytest.mark.parametrize('cap,fixed,demand',itertools.product(range(3),range(2,5),[(0,0),(0,1),(1,1)]))
def test_solver_matches_exhaustive_original_usage_arithmetic(cap,fixed,demand):
    p=problem(cap,fixed,demand=demand);expected=oracle(p);result=planner.solve(p)
    if expected is None:
        assert result['status']=='INFEASIBLE' and result['selected'] is None
    else:
        assert result['status']=='FEASIBLE' and result['optimal']
        assert (len(result['selected']),result['selection_check']['old_steps'])==expected
        assert result['selection_check']==planner.check_selection(p,result['selected'])
    assert not result['routing_feasibility_claimed'] and not result['native_inputs_authenticated']


@requires_solver
def test_joint_release_recovers_capacity_only_after_existing_overflow_is_removed():
    p=problem();r=planner.solve(p)
    assert r['selected']==['a','b'] and r['nonlinear_resources']==1
    with pytest.raises(ValueError,match='necessary cut'):planner.check_selection(p,['a'])


@requires_solver
def test_nonnegative_offset_has_no_auxiliary_activation_and_unused_candidates_pruned():
    p=problem(cap=2,fixed=2,release=(0,1));r=planner.solve(p)
    assert r['selected']==['b'] and r['nonlinear_resources']==0
    assert r['variables']==r['retained_candidates']==1


@requires_solver
def test_joint_cuts_differ_from_repairing_only_one_boundary():
    p=problem(cap=2,fixed=2,release=(1,0))
    second=deepcopy(p['cuts'][0]);second['id']='other';second['resources'][0]['releases']={'b':1};p['cuts'].append(second)
    assert planner.solve(p)['selected']==['a','b']
    p['max_additional']=1
    assert planner.solve(p)['status']=='INFEASIBLE'


@requires_solver
def test_minimum_number_of_routes_precedes_old_step_tie_break():
    p=problem(cap=3,fixed=3,release=(2,1),required=2)
    p['candidates'][0]['old_steps']=1000
    assert planner.solve(p)['selected']==['a']


@pytest.mark.parametrize('selected',[['a'],['missing'],['a','a'],[1],'a'])
def test_arithmetic_checker_rejects_bad_or_insufficient_selection(selected):
    with pytest.raises(ValueError):planner.check_selection(problem(),selected)


@pytest.mark.parametrize('mutate',[
    lambda p:p.update(schema_version=True),
    lambda p:p.update(max_additional=True),
    lambda p:p['candidates'].append(deepcopy(p['candidates'][0])),
    lambda p:p['cuts'][0]['crossing_demand'].update(a=2),
    lambda p:p['cuts'][0]['resources'][0].update(fixed_usage=1),
    lambda p:p['cuts'][0]['resources'][0]['releases'].update(missing=1),
    lambda p:p['cuts'][0]['resources'][0].update(capacity=-1),
    lambda p:p.update(extra='not accepted'),
])
def test_invalid_model_rejected(mutate):
    p=problem();mutate(p)
    with pytest.raises(ValueError):planner.validate(p)


def test_validation_and_selection_preserve_input():
    p=problem();before=deepcopy(p);planner.check_selection(p,['a','b']);assert p==before
