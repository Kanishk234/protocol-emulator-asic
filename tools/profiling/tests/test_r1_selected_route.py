from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from selected_route import selected_predecessors,trace_route
from unused_lut_probe import registered_h_source


def test_selected_route_decodes_the_actual_frame_word_and_bit():
    spec=dict(ArchSpecs=dict(FrameBitsPerRow=32,MaxFramesPerCol=20),
              TileSpecs={'X2Y3':{'old.IN':{183:'0'},'new.IN':{183:'1'}}})
    pips='X2Y3,old,X2Y3,IN,8,old.IN\nX2Y3,new,X2Y3,IN,8,new.IN\n'
    words=[0]*962
    assert trace_route(selected_predecessors(spec,words,pips),('X2Y3','IN'))[-1]==('X2Y3','old')
    words[273]=1<<23
    assert trace_route(selected_predecessors(spec,words,pips),('X2Y3','IN'))[-1]==('X2Y3','new')
    with pytest.raises(ValueError):selected_predecessors(spec,words[:-1],pips)


def test_ambiguous_or_cyclic_routes_cannot_be_reported_as_register_sources():
    with pytest.raises(ValueError,match='Ambiguous'):
        trace_route({'a':['b','c']},'a')
    with pytest.raises(ValueError,match='Cyclic'):
        trace_route({'a':['b'],'b':['a']},'a')


def h_module():
    def cell(kind,connections,output):
        return dict(type='sg13cmos5l_'+kind+'_1',connections={p:[b] for p,b in connections.items()},
                    port_directions={p:'output' if p==output else 'input' for p in connections})
    return dict(netnames={'LH_O':dict(bits=[272])},cells={
        'out':cell('a21oi',dict(A1=243,A2=574,B1=575,Y=272),'Y'),
        'masked':cell('nor3',dict(A=574,B=559,C=573,Y=575),'Y'),
        'inv':cell('inv',dict(A=242,Y=243),'Y'),
        'user':cell('dfrbpq',dict(D=240,CLK=1,RESET_B=2,Q=242),'Q')})


def test_registered_h_proof_requires_masked_comb_arm_and_actual_flip_flop():
    module=h_module();assert registered_h_source(module,574)=='user'
    module['cells']['masked']['connections']['A']=[999]
    with pytest.raises(ValueError,match='masked'):
        registered_h_source(module,574)
    module=h_module();module['cells']['user']['type']='sg13cmos5l_buf_1'
    with pytest.raises(ValueError,match='flip-flop'):
        registered_h_source(module,574)
