import pytest
from host_idle_residual_selection import select


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
