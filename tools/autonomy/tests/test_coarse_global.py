"""Independent small source-format fixtures and original-layer resource checks."""
from copy import deepcopy
import pytest
from autonomy import coarse_global as c,corridor_solver as solver
from autonomy.tests.test_corridor_extract import fixture


def witness():return {'0':['H_0_0','H_1_0','H_2_0']}


def test_unit_all_layer_model_maps_witness_back_to_original_resources():
    s,t,_=fixture();m=c.build(s,t,slots=[0]);r=c.allocate_and_check(s,t,m,witness())
    assert len(m['graph']['nodes'])==12 and len(m['graph']['edges'])==17
    assert m['model_variables']==34
    assert r['original_raw_overflow']==r['proposed_raw_overflow']==0
    assert r['routes']['0']['planar_resources']==[('H',0,0,0),('H',0,1,0),('H',0,2,0)]
    assert r['original_layer_capacity_allocation_checked']
    assert r['native_pin_connectivity_under_unlimited_vias_checked']
    assert not r['native_inputs_authenticated'] and not r['physical_acceptance']


def add_fixed_repeated_net(s,t):
    # Hand-built second net charges each of the three horizontal edges FOUR
    # times. This supplies an exact fixed overflow, not fabricated background.
    s.nets[1]=deepcopy(s.nets[0]);s.nets[1].update(db_id=12,name='fixed')
    for edge in s.nets[1]['planar_step_multiplicity']:
        s.nets[1]['planar_step_multiplicity'][edge]=4
        cap,use,red,real=s.edges[edge];s.edges[edge]=(cap,use+4,red,real)
    t.nets[1]=deepcopy(t.nets[0]);t.nets[1].update(db_id=12,name='fixed')
    t.database[12]=deepcopy(t.database[11]);t.database[12].update(name='fixed',slot=1)
    t.global_nets[12]=deepcopy(t.global_nets[11]);t.global_nets[12].update(name='fixed',slot=1)
    for p in t.global_nets[12]['pins']:
        p['ids']=(p['ids'][0]+10,0,0);p['slot']=1;p['members']=[(1,i) for _,i in p['members']]


def test_fixed_overflow_is_retained_and_never_made_available_capacity():
    s,t,_=fixture();add_fixed_repeated_net(s,t)
    m=c.build(s,t,slots=[0]);r=c.allocate_and_check(s,t,m,witness())
    assert m['fixed_background_overflow']==3
    assert r['original_raw_overflow']==6 and r['proposed_raw_overflow']==3
    assert all(edge[1]==1 for edge in r['routes']['0']['planar_resources'])
    assert r['routes']['0']['unlimited_coarse_vias']==[(0,0,0,1),(3,0,0,1)]
    assert next(e for e in m['graph']['edges'] if e['id']=='H_1_0')['capacity']==3


def test_native_old_multiplicity_released_exactly_before_unit_candidate():
    s,t,_=fixture([(0,0),(1,0),(2,0),(1,0),(2,0),(3,0)])
    m=c.build(s,t,slots=[0]);r=c.allocate_and_check(s,t,m,witness())
    assert next(e for e in m['graph']['edges'] if e['id']=='H_1_0')['capacity']==6
    assert r['proposed_raw_overflow']==0


def test_two_nets_share_aggregate_capacity_but_use_distinct_original_layers():
    s,t,_=fixture();add_fixed_repeated_net(s,t)
    for edge,(cap,use,red,real) in list(s.edges.items()):s.edges[edge]=(1,use,red,real)
    m=c.build(s,t,slots=[0,1]);w={'0':witness()['0'],'1':witness()['0']}
    result=c.allocate_and_check(s,t,m,w)
    assert result['original_raw_overflow']==12 and result['proposed_raw_overflow']==0
    assert {e[1] for e in result['routes']['0']['planar_resources']}=={0}
    assert {e[1] for e in result['routes']['1']['planar_resources']}=={1}
    assert result['routes']['1']['unlimited_coarse_vias']==[(0,0,0,1),(3,0,0,1)]


def test_components_without_selected_terminals_are_removed_only_as_irrelevant():
    s,t,_=fixture()
    for edge,(cap,use,red,real) in list(s.edges.items()):
        if edge[0]=='V' and edge[3]==0:s.edges[edge]=(0,use,red,real)
    m=c.build(s,t,slots=[0])
    assert len(m['graph']['nodes'])==4 and len(m['graph']['edges'])==3
    assert c.allocate_and_check(s,t,m,witness())['proposed_raw_overflow']==0


def test_isolated_selected_pins_are_retained_instead_of_silently_dropped():
    s,t,_=fixture()
    for edge,(_,use,red,real) in list(s.edges.items()):s.edges[edge]=(0,use,red,real)
    m=c.build(s,t,slots=[0])
    assert len(m['graph']['nodes'])==2 and not m['graph']['edges']
    with pytest.raises(ValueError,match='disconnected'):c.allocate_and_check(s,t,m,{'0':[]})


def test_nonunit_demand_requires_a_different_model():
    s,t,_=fixture();s.nets[0]['demands']=[2,2]
    for edge,(cap,use,red,real) in list(s.edges.items()):s.edges[edge]=(cap,use*2,red,real)
    with pytest.raises(c.ModelError,match='unit demand'):c.build(s,t,slots=[0])


def test_layer_restrictions_cannot_silently_disappear():
    s,t,_=fixture();s.nets[0]['minimum_layer']=t.nets[0]['minimum_layer']=1
    with pytest.raises(c.ModelError,match='every native planar layer'):c.build(s,t,slots=[0])


def test_unsupported_selected_membership_blocks_build(monkeypatch):
    s,t,_=fixture()
    monkeypatch.setattr(c.terminals,'audit_selection',lambda *a:{'selected_membership_and_access_verified':False})
    with pytest.raises(c.ModelError,match='unsupported'):c.build(s,t,slots=[0])


def test_hard_model_limits_are_not_raised_to_fit(monkeypatch):
    s,t,_=fixture();monkeypatch.setattr(solver,'MAX_NODES',11)
    with pytest.raises(c.ModelError,match='model bounds'):c.build(s,t,slots=[0])


def test_modified_graph_cannot_be_used_for_original_layer_allocation():
    s,t,_=fixture();m=c.build(s,t,slots=[0]);m['graph']['edges'][0]['capacity']+=1
    with pytest.raises(c.ModelError,match='reconstructed'):c.allocate_and_check(s,t,m,witness())


def test_disconnected_witness_is_rejected_before_allocation():
    s,t,_=fixture();m=c.build(s,t,slots=[0])
    with pytest.raises(ValueError,match='disconnected'):c.allocate_and_check(s,t,m,{'0':['H_0_0']})


def test_no_solver_invocation_in_build_or_verifier(monkeypatch):
    s,t,_=fixture();monkeypatch.setattr(solver,'solve',lambda *a,**k:pytest.fail('No solver permitted'))
    m=c.build(s,t,slots=[0]);assert c.allocate_and_check(s,t,m,witness())['original_layer_capacity_allocation_checked']
