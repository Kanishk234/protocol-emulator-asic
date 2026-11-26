from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from upstream_input import isolated_chain
from unused_input_sweep import prove_lut_independent,prove_input


def test_isolation_accepts_only_single_input_chain():
    a,b,c=[('X1Y1',n) for n in ('jump','end','LD_I2')]
    graph={b:[a],c:[b]}
    assert isolated_chain(graph,a,c)==[a,b,c]
    with pytest.raises(ValueError):isolated_chain({**graph,('X1Y1','LE_I0'):[b]},a,c)
    with pytest.raises(ValueError):isolated_chain({**graph,a:[c]},a,c)


def test_isolation_rejects_cycles_and_missing_target():
    a,b,c=[('X1Y1',n) for n in ('jump','end','LD_I2')]
    with pytest.raises(ValueError):isolated_chain({a:[b],b:[a]},a,c)
    with pytest.raises(ValueError):isolated_chain({b:[a]},a,c)


def test_function_proof_preserves_an_existing_input_route_but_rejects_truth_mismatch():
    entries={'A.INIT'+('['+str(i)+']' if i else ''):{i:'1'} for i in range(16)}
    entries['A.FF']={16:'1'}
    module=dict(ports={'FrameData':{'bits':list(range(32))},
                       'FrameStrobe':{'bits':list(range(100,120))}},
                cells={'cfg'+str(i):{'type':'sg13cmos5l_dlhq_1',
                      'connections':{'D':[i],'GATE':[100],'Q':[200+i]}} for i in range(17)})
    truth=0xcccc;words=[0]*962;words[125]=truth|(1<<16)
    q={'cfg'+str(i):str(truth>>i&1) for i in range(16)};q['cfg16']='1'
    state={'tiles':{'Tile_X1Y1_LUT4x8_ha':{'q':q}}};spec={'TileSpecs':{'X1Y1':entries}}
    features={'X1Y1.'+key for key in entries if key!='A.FF' and truth>>next(iter(entries[key]))&1}
    features|={'X1Y1.A.FF','X1Y1.EXISTING.LA_I0'}
    assert prove_lut_independent('X1Y1','A',0,spec,module,state,features,words,True)==(truth,'1')
    # The original local-selector operation still forbids changing this route.
    with pytest.raises(ValueError,match='actively routed'):
        prove_input('X1Y1','A',0,spec,module,state,features,words,'',{},True)
    with pytest.raises(ValueError,match='depends'):
        prove_lut_independent('X1Y1','A',1,spec,module,state,features,words,True)
    q['cfg0']='1'
    with pytest.raises(ValueError,match='truth differs'):
        prove_lut_independent('X1Y1','A',0,spec,module,state,features,words,True)
