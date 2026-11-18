"""Cross-tile expansion must preserve aliases, configuration and free boundaries."""
from copy import deepcopy
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from global_support import flatten


def example():
    module = dict(ports={'I':dict(bits=[2],direction='input'), 'O':dict(bits=[3],direction='output')},
                  cells={'gate':dict(type='sg13cmos5l_inv_1',port_directions={'A':'input','Y':'output'},
                                     connections={'A':[2],'Y':[3]})},
                  netnames={'I':dict(bits=[2]),'O':dict(bits=[3])})
    top = dict(cells={'a':dict(type='INV',connections={'I':[2],'O':[3]}),
                     'b':dict(type='INV',connections={'I':[3],'O':[2]})},
               ports={'IN':dict(bits=[2],direction='input')})
    state = {n:dict(tile_type='INV',q={}) for n in top['cells']}
    return top, {'INV':module}, state


def test_two_tile_cycle_retains_actual_intertile_nets():
    top, modules, state = example()
    m,q = flatten(top,modules,state)
    assert not q
    assert m['cells']['a/gate']['connections']['Y'] == m['cells']['b/gate']['connections']['A']
    assert m['cells']['b/gate']['connections']['Y'] == m['cells']['a/gate']['connections']['A']


def test_wire_only_corner_unifies_distinct_outer_net_aliases():
    top, modules, state = example()
    modules['NE_term'] = dict(cells={}, netnames={}, ports={
        'I':dict(bits=[2],direction='input'), 'O':dict(bits=[2],direction='output'),
        'VPWR':dict(bits=[3],direction='inout'), 'VGND':dict(bits=[4],direction='inout')})
    top['cells']['wire'] = dict(type='NE_term',connections={'I':[3],'O':[7]})
    top['cells']['b']['connections']['I'] = [7]
    state['wire'] = dict(tile_type='NE_term',q={})
    m,_ = flatten(top,modules,state)
    assert m['cells']['a/gate']['connections']['Y'] == m['cells']['b/gate']['connections']['A']


def test_alias_cannot_short_zero_to_one():
    top, modules, state = example()
    modules['INV']['ports']['O']['bits'] = [2]
    top['cells']['a']['connections'] = {'I':['0'],'O':['1']}
    with pytest.raises(ValueError,match='Conflicting constant'):
        flatten(top,modules,state)


def test_configuration_latch_state_and_actual_q_net_are_preserved():
    top,modules,state = example()
    modules['INV']['cells']['cfg'] = dict(type='sg13cmos5l_dlhq_1',
        port_directions={'D':'input','GATE':'input','Q':'output'},connections={'D':[4],'GATE':[5],'Q':[6]})
    for row in state.values():row['q']={'cfg':'1'}
    m,q = flatten(top,modules,state)
    assert q == {'a/cfg':'1','b/cfg':'1'}
    assert m['cells']['a/cfg']['connections']['Q'] != m['cells']['b/cfg']['connections']['Q']
    bad = deepcopy(state);bad['b']['q'] = {}
    with pytest.raises(ValueError,match='latch population'):
        flatten(top,modules,bad)


def test_missing_tile_unknown_literal_and_port_mismatch_fail_closed():
    top,modules,state = example()
    bad = deepcopy(state);del bad['b']
    with pytest.raises(ValueError,match='tile population'):
        flatten(top,modules,bad)
    top['cells']['a']['connections']['I']=['x']
    with pytest.raises(ValueError,match='Unknown literal'):
        flatten(top,modules,state)
    top,modules,state = example();modules['INV']['ports']['extra']=dict(bits=[9],direction='input')
    with pytest.raises(ValueError,match='port mismatch'):
        flatten(top,modules,state)
