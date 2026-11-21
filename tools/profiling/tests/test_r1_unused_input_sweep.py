from pathlib import Path
import os
import subprocess
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from unused_input_sweep import carry_cone,independent,ff_mode


def test_registered_input_proof_requires_explicit_opt_in_and_matching_actual_mode():
    module=dict(ports={'FrameData':{'bits':list(range(32))},
                       'FrameStrobe':{'bits':list(range(100,120))}},
                cells={'cfg':{'type':'sg13cmos5l_dlhq_1',
                              'connections':{'D':[0],'GATE':[100],'Q':[200]}}})
    spec={'TileSpecs':{'X1Y1':{'A.FF':{0:'1'}}}}
    state={'tiles':{'Tile_X1Y1_LUT4x8_ha':{'q':{'cfg':'1'}}}}
    words=[0]*962;words[125]=1
    features={'X1Y1.A.FF'}
    with pytest.raises(ValueError):ff_mode('X1Y1','A',spec,module,state,features,words)
    assert ff_mode('X1Y1','A',spec,module,state,features,words,True)=='1'
    with pytest.raises(ValueError):ff_mode('X1Y1','A',spec,module,state,set(),words,True)
    words[125]=0
    with pytest.raises(ValueError):ff_mode('X1Y1','A',spec,module,state,features,words,True)
    state['tiles']['Tile_X1Y1_LUT4x8_ha']['q']['cfg']='0'
    assert ff_mode('X1Y1','A',spec,module,state,set(),words,True)=='0'


def test_cofactor_proof_rejects_any_actual_dependence_on_the_changed_input():
    assert independent(0x1111,2) and independent(0x1111,3)
    assert not independent(0x1111,0) and not independent(0x1111,1)
    assert independent(0xEFEF,3) and not independent(0xEFEF,2)
    for truth,index in [(0x10000,2),(-1,2),(0x1111,4)]:
        with pytest.raises(ValueError):independent(truth,index)


def test_native_sweep_runner_does_not_import_compiler_packages():
    env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[3]/'spikes/r1'))
    subprocess.run([sys.executable,'-S','-c','import unused_input_sweep'],check=True,env=env)


def test_unused_lut_truth_does_not_waive_carry_side_effects():
    graph={('X1Y1','LG_Ci'):[('X1Y1','LF_Co')],('X1Y1','LH_Ci'):[('X1Y1','LG_Co')]}
    modes={('X1Y1','LG_Ci'):False,('X1Y1','LH_Ci'):False,('X2Y1','LA_Ci'):True}
    assert carry_cone(graph,'X1Y1','F',modes)['enabled_consumers']==0
    modes[('X1Y1','LH_Ci')]=True
    with pytest.raises(ValueError):carry_cone(graph,'X1Y1','F',modes)
    modes.pop(('X1Y1','LH_Ci'))
    with pytest.raises(ValueError):carry_cone(graph,'X1Y1','F',modes)
    graph={('X1Y1','LA_I0'):[('X1Y1','LF_Co')]}
    with pytest.raises(ValueError):carry_cone(graph,'X1Y1','F',{})
