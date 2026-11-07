import pytest
from host_idle_residual_selection import select, validate_orientations, scoped_plan


def test_isolation_keeps_full_plan_immutable_and_bounds_edits():
    plan=dict(diodes=[dict(net='net15518'),dict(net='other')],
              allowed_signal_nets_to_reroute=['net15518','other'],
              congestion_signal_nets=['other'],residual_edges=[{'edge':1}])
    only=scoped_plan(plan,'net15518_only')
    assert only['diodes']==[dict(net='net15518')]
    assert only['congestion_signal_nets']==only['residual_edges']==[]
    omitted=scoped_plan(plan,'omit_net15518')
    assert omitted['allowed_signal_nets_to_reroute']==['other']
    assert omitted['residual_edges']==[{'edge':1}]
    assert len(plan['diodes'])==2 and 'isolation_scope' not in plan
    assert scoped_plan(plan,'full')['diodes']==plan['diodes']
    with pytest.raises(ValueError,match='Unreviewed'):
        scoped_plan(plan,'unknown')


@pytest.mark.parametrize('orient',['R0','MX','MY','R180'])
def test_accepts_native_orientation_names(orient):
    validate_orientations({'diodes':[{'locked_orientation':orient}]})


@pytest.mark.parametrize('orient',['N','FS','FN','S',None,'bad'])
def test_rejects_def_and_invalid_orientations_before_edit(orient):
    with pytest.raises(ValueError,match='native OpenDB'):
        validate_orientations({'diodes':[{'locked_orientation':orient}]})


def test_selects_actual_crossing_and_eligible_data_only():
    seg = ((0,0,'Metal3'),(7200,0,'Metal3'))
    routes = {'clock':[seg], 'data':[seg], 'wrong_layer':[((0,0,'Metal2'),(7200,0,'Metal2'))]}
    edge = dict(direction='HORIZONTAL',layer='Metal3',start_dbu=[0,0],end_dbu=[7200,0])
    assert select(routes,[edge],{'data':2,'wrong_layer':1}) == ['data']
    assert 'crossing_route_names' not in edge
    with pytest.raises(ValueError,match='eligible'):
        select(routes,[edge],{'wrong_layer':1})


def test_one_distinct_net_per_edge_and_deterministic_cost():
    seg = ((0,0,'Metal3'),(14400,0,'Metal3'))
    routes = {'a':[seg], 'b':[seg]}
    edges = [dict(direction='HORIZONTAL',layer='Metal3',start_dbu=[x,0],end_dbu=[x+7200,0]) for x in (0,7200)]
    assert select(routes,edges,{'a':2,'b':1}) == ['b','a']
    with pytest.raises(ValueError,match='distinct'):
        select(routes,edges,{'a':1})
