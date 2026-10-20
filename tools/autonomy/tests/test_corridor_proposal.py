from copy import deepcopy
import pytest
from autonomy import corridor_extract,corridor_proposal
from autonomy.tests.test_corridor_extract import fixture


def repeated_input(window=(1,0,2,1)):
    s,t,text=fixture([(0,0),(1,0),(2,0),(1,0),(2,0),(3,0)])
    key=('H',0,1,0);_,used,red,real=s.edges[key];s.edges[key]=(1,used,red,real)
    m=corridor_extract.extract(s,t,text,slots=[0],window=list(window))
    return s,t,text,m


def test_local_proposal_connects_original_pins_and_counts_full_raw_improvement():
    s,t,text,m=repeated_input();w={'0':['H_0_1_0']}
    r=corridor_proposal.verify(s,t,text,m,w,max_window_overflow=0)
    assert r['original_full_raw_overflow']==2 and r['proposed_full_raw_overflow']==0
    assert r['delta']==-2 and r['original_capacities_preserved'] and r['outside_routes_frozen']
    assert r['changed_resources']==[dict(edge=['H',0,1,0],before=3,after=1,capacity=1)]
    assert r['selected_native_pin_connectivity']['0']['all_pins_connected']
    assert r['proposal_only'] and not r['native_route_installed'] and not r['physical_acceptance']


def test_full_window_route_replacement_has_same_original_pin_result():
    s,t,text,m=repeated_input((0,0,3,1));w={'0':['H_0_0_0','H_0_1_0','H_0_2_0']}
    assert corridor_proposal.verify(s,t,text,m,w,max_window_overflow=0)['delta']==-2


def test_equal_raw_overflow_is_not_retained_as_improvement():
    s,t,text=fixture();m=corridor_extract.extract(s,t,text,slots=[0],window=[1,0,2,1])
    with pytest.raises(ValueError,match='No strict'):corridor_proposal.verify(s,t,text,m,{'0':['H_0_1_0']},max_window_overflow=0)


def test_proposal_cannot_hide_frozen_outside_overflow():
    s,t,text,m=repeated_input((2,0,3,1))
    with pytest.raises(ValueError,match='No strict'):corridor_proposal.verify(s,t,text,m,{'0':['H_0_2_0']},max_window_overflow=0)


@pytest.mark.parametrize('field',['capacity','fixed_usage'])
def test_changed_resource_contract_is_rejected(field):
    s,t,text,m=repeated_input();next(e for e in m['graph']['edges'] if e['id']=='H_0_1_0')[field]+=1
    with pytest.raises(ValueError,match='reconstructed'):corridor_proposal.verify(s,t,text,m,{'0':['H_0_1_0']},max_window_overflow=0)


def test_model_and_native_inputs_are_not_mutated():
    s,t,text,m=repeated_input();before=deepcopy(m);raw_before=deepcopy(s.edges)
    corridor_proposal.verify(s,t,text,m,{'0':['H_0_1_0']},max_window_overflow=0)
    assert m==before and s.edges==raw_before


def test_native_old_zero_resource_permission_keeps_capacity_zero_and_charges_usage():
    s,t,text,_=repeated_input();key=('H',0,1,0);_,used,red,real=s.edges[key];s.edges[key]=(0,used,red,real)
    m=corridor_extract.extract(s,t,text,slots=[0],window=[1,0,2,1])
    assert corridor_proposal.original_zero_permissions(s,m)=={'0':['H_0_1_0']}
    r=corridor_proposal.verify(s,t,text,m,{'0':['H_0_1_0']},max_window_overflow=1)
    assert r['original_full_raw_overflow']==3 and r['proposed_full_raw_overflow']==1
    assert r['changed_resources']==[dict(edge=['H',0,1,0],before=3,after=1,capacity=0)]


def test_unused_zero_capacity_shortcut_cannot_be_imported_as_old_native_permission():
    s,t,text,_=repeated_input();key=('H',0,1,1);_,used,red,real=s.edges[key];s.edges[key]=(0,used,red,real)
    m=corridor_extract.extract(s,t,text,slots=[0],window=[1,0,2,1])
    assert corridor_proposal.original_zero_permissions(s,m)=={'0':[]}
    with pytest.raises(ValueError,match='Zero-capacity'):
        corridor_proposal.verify(s,t,text,m,{'0':['V_0_1_0','H_0_1_1','V_0_2_0']},max_window_overflow=1)
