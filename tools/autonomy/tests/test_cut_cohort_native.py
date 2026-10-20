from copy import deepcopy
import pytest
from autonomy import cut_cohort_native as adapter,coarse_global,capacity_cut
from autonomy.tests.test_corridor_extract import fixture
from autonomy.tests.test_coarse_global import add_fixed_repeated_net


def inputs():
    s,t,_=fixture();add_fixed_repeated_net(s,t)
    for edge,(_,usage,red,real) in list(s.edges.items()):s.edges[edge]=(0,usage,red,real)
    edge=('H',0,0,0);_,usage,red,real=s.edges[edge];s.edges[edge]=(1,usage,red,real)
    m=coarse_global.build(s,t,slots=[0])
    cut=capacity_cut.certify_partition(m['graph'],side_nodes=['p0_0'])
    assert cut['independently_verified_graph_infeasible']
    return s,t,dict(model=m,certificate=cut)


def test_native_adapter_binds_original_multiset_capacity_and_additional_pin_demand():
    s,t,r=inputs();result=adapter.build(s,t,baseline_slots=[0],records=[r]);p=result['problem']
    assert p['candidates']==[dict(id='1',old_steps=12)]
    assert p['cuts'][0]['required_demand']==1 and p['cuts'][0]['crossing_demand']=={'1':1}
    e=next(e for e in p['cuts'][0]['resources'] if e['id']=='H_0_0_0')
    assert e==dict(id='H_0_0_0',capacity=1,fixed_usage=4,releases={'1':4})
    assert not result['routing_feasibility_claimed'] and not result['native_inputs_authenticated']


@pytest.mark.parametrize('field',['model','certificate'])
def test_native_adapter_rejects_changed_model_or_certificate(field):
    s,t,r=inputs()
    if field=='model':r['model']['fixed_background_overflow']+=1
    else:r['certificate']['residual_crossing_capacity']+=1
    with pytest.raises(ValueError):adapter.build(s,t,baseline_slots=[0],records=[r])


def test_native_adapter_rejects_nondeficient_partition():
    s,t,_=fixture();m=coarse_global.build(s,t,slots=[0]);cut=capacity_cut.certify_partition(m['graph'],side_nodes=['p0_0'])
    assert not cut['independently_verified_graph_infeasible']
    with pytest.raises(ValueError):adapter.build(s,t,baseline_slots=[0],records=[dict(model=m,certificate=cut)])


@pytest.mark.parametrize('records',[[],[{}],None])
def test_native_adapter_requires_finite_explicit_records(records):
    s,t,_=fixture()
    with pytest.raises(ValueError):adapter.build(s,t,baseline_slots=[0],records=records)


def test_native_adapter_does_not_mutate_inputs():
    s,t,r=inputs();before=deepcopy(r);adapter.build(s,t,baseline_slots=[0],records=[r]);assert r==before
