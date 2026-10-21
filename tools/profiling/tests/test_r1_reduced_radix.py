import copy
from itertools import product
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools'))
from reduced_radix import cover_outputs, reduce


def test_matching_covers_sources_when_greedy_first_choice_would_fail():
    result=cover_outputs({'d0':['a','b'],'d1':['a']},1)
    assert result=={'d0':['b'],'d1':['a']}
    with pytest.raises(ValueError):cover_outputs({'d0':['a','b']},1)


def test_matching_agrees_with_exhaustive_small_graph_feasibility():
    pools=[['a'],['b'],['a','b'],['a','c'],['b','c'],['a','b','c']]
    for values in product(pools,repeat=3):
        choices=dict(zip(('d0','d1','d2'),values))
        sources=set().union(*map(set,values))
        feasible=any(set(selection)==sources for selection in product(*values))
        if feasible:
            result=cover_outputs(choices,1)
            assert set().union(*map(set,result.values()))==sources
        else:
            with pytest.raises(ValueError):cover_outputs(choices,1)


def test_clock_reset_carry_and_primitive_inputs_preserved():
    graph={name:['s0','s1','s2','s3'] for name in
           ('GCLK_BEG0','GSR_BEG0','GEN_BEG0','J_SR_BEG0','J_EN_BEG0','N_GBUF_BEG0','CO0','TA_load')}
    result,_=reduce(graph)
    assert result==graph


def test_data_selectors_narrow_without_inventing_edges_or_mutating_inputs():
    graph={'J2MID_ABa_BEG0':['JN2END3','N2MID2','S2MID2','W2MID2'],
           'J2MID_ABb_BEG1':['N2MID3','E2MID3','S2MID3','W2MID3'],
           'LA_I0':['a','b','c','d'],'LB_I0':['a','b','c','d']}
    before=copy.deepcopy(graph)
    result,meta=reduce(graph)
    assert graph==before
    assert all(len(v)==2 and set(v)<=set(graph[k]) for k,v in result.items())
    assert 'JN2END3' in result['J2MID_ABa_BEG0']
    assert result['LA_I0'] != result['LB_I0']
    assert set(result['LA_I0']) | set(result['LB_I0']) == {'a','b','c','d'}
    assert meta['select_bits']==4


def test_escape_banks_cover_every_cell_output_with_at_most_eight_choices():
    graph={f'J{direction}2BEG{i}':[f'L{letter}_O' for letter in 'ABCDEFGH']+
           [f'{d}1END{j}' for d in 'NESW' for j in range(4)]
           for direction in 'NESW' for i in range(8)}
    result,meta=reduce(graph)
    assert all(len(v)==8 for v in result.values())
    assert all(v==[f'L{letter}_O' for letter in 'ABCDEFGH'] for v in meta['cell_output_coverage_per_direction'].values())
    assert not meta['physical_acceptance']


def test_bad_gather_shape_or_empty_selector_rejected():
    with pytest.raises(ValueError):reduce({'J2MID_ABa_BEG0':['local0','local1','N2MID0']})
    with pytest.raises(ValueError):reduce({'LA_I0':[]})
