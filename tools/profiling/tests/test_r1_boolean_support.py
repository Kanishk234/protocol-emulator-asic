"""Admission and conservative-boundary guards for binary support diagnostics."""
from copy import deepcopy
import pytest
from spikes.r1.boolean_support import cone


def cell(kind, inputs, output):
    return dict(type='sg13cmos5l_'+kind+'_1', port_directions={**{p:'input' for p in inputs},'X':'output'},
                connections={**{p:[b] for p,b in inputs.items()},'X':[output]})


def feedback():
    return dict(cells={'gate':cell('xor2',{'A':2,'B':2},2)}, netnames={'root':{'bits':[2]}})


def test_feedback_cofactor_changes_only_target_and_shares_cuts():
    m=feedback();m['cells']['gate']=cell('and2',{'A':2,'B':3},2)
    text,row=cone(m,{},'root')
    assert ".i0(1'b0),.i1(i1)" in text and ".i0(1'b1),.i1(i1)" in text
    assert row['cuts']['2']['reason']=='feedback' and row['cuts']['3']['reason']=='undriven_or_module_input'


def test_unknown_sequential_state_is_free_not_assumed_zero():
    m=feedback();m['cells']['gate']=cell('and2',{'A':2,'B':3},2)
    m['cells']['reg']=cell('dfrbp',{'D':4,'CLK':5,'RESET_B':6},3)
    text,row=cone(m,{},'root')
    assert row['cuts']['3']['reason']=='sequential_output'
    assert 'sg13cmos5l_dfrbp' not in text


def test_observed_configuration_is_bound_to_the_actual_q_bit():
    m=feedback();m['cells']['gate']=cell('and2',{'A':2,'B':3},2)
    m['cells']['cfg']=dict(type='sg13cmos5l_dlhq_1',port_directions={'D':'input','GATE':'input','Q':'output'},
                           connections={'D':[4],'GATE':[5],'Q':[3]})
    text,_=cone(m,{'cfg':'1'},'root')
    assert ".B(1'b1)" in text
    with pytest.raises(ValueError,match='configuration state'):
        cone(m,{'cfg':'X'},'root')


def test_depth_bound_introduces_a_free_variable():
    m=feedback();m['cells']['gate']=cell('and2',{'A':2,'B':3},2)
    m['cells']['other']=cell('buf',{'A':4},3)
    _,row=cone(m,{},'root',depth=1)
    assert row['cuts']['3']['reason']=='bound'


def test_multidriver_and_unknown_literals_fail_closed():
    m=feedback();m['cells']['another']=deepcopy(m['cells']['gate'])
    with pytest.raises(ValueError,match='Multiple output'):
        cone(m,{},'root')
    m=feedback();m['cells']['gate']['connections']['B']=['x']
    with pytest.raises(ValueError,match='Nonbinary'):
        cone(m,{},'root')


def test_unexposed_feedback_is_not_claimed_proven():
    m=feedback();m['cells']['gate']=cell('buf',{'A':3},2)
    with pytest.raises(ValueError,match='Root feedback was not exposed'):
        cone(m,{},'root')


def test_all_feedback_varies_each_recursion_cut_independently():
    m=feedback();m['cells']['gate']=cell('xor2',{'A':2,'B':3},2)
    m['cells']['other']=cell('buf',{'A':3},3)
    _,own=cone(m,{},'root')
    text,all_cuts=cone(m,{},'root',all_feedback=True)
    assert len(own['varying_ports'])==1 and len(all_cuts['varying_ports'])==2
    assert ".i0(1'b0),.i1(1'b0)" in text
    assert '.i0(i0),.i1(i1)' in text
