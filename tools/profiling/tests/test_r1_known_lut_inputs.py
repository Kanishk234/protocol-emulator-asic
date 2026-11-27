from copy import deepcopy
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from known_lut_inputs import fill_inputs


def design(width,truth,connections=None):
    return {'modules':{'warp_top':{'netnames':{'u_user.rst_n':{'bits':[43]}},'cells':{
        'reset':{'type':'IOBUF','port_directions':{'OUT':'output'},
                 'connections':{'OUT':[43],'IN':['0'],'EN':['0']}},
        'lut':{'type':'LUT'+str(width),'parameters':{'INIT':format(truth,'0'+str(1<<width)+'b')},
               'port_directions':{**{'I'+str(i):'input' for i in range(width)},'O':'output'},
               'connections':connections or {**{'I'+str(i):[10+i] for i in range(width)},'O':[99]}},
        'ff':{'type':'LUTFF_SR','parameters':{},'connections':{'D':[99],'O':[100],'CLK':[101],'R':[102]}}
    }}}}


def value(cell,signals):
    width=int(cell['type'][-1]);index=0
    for i in range(width):
        bit=cell['connections']['I'+str(i)][0]
        index|=(int(bit) if bit in ('0','1') else signals[bit])<<i
    return int(cell['parameters']['INIT'],2)>>index&1


@pytest.mark.parametrize('width',[1,2,3])
def test_every_small_lut_truth_and_input_is_preserved(width):
    for truth in range(1<<(1<<width)):
        original=design(width,truth);before=deepcopy(original)
        filled,proof=fill_inputs(original)
        assert original==before and proof['changed_cells']==1
        assert filled['modules']['warp_top']['cells']['ff']==original['modules']['warp_top']['cells']['ff']
        old=original['modules']['warp_top']['cells']['lut'];new=filled['modules']['warp_top']['cells']['lut']
        for inputs in range(1<<width):
            for reset in (0,1):
                signals={**{10+i:inputs>>i&1 for i in range(width)},43:reset}
                assert value(old,signals)==value(new,signals)


def test_constant_input_is_cofactored_before_adding_live_reset_and_bad_source_rejects():
    original=design(2,0b0110,{'I0':['1'],'I1':[11],'O':[99]})
    filled,_=fill_inputs(original)
    for bit in (0,1):
        for reset in (0,1):
            signals={11:bit,43:reset}
            assert value(original['modules']['warp_top']['cells']['lut'],signals)==value(filled['modules']['warp_top']['cells']['lut'],signals)
    original['modules']['warp_top']['cells']['reset']['connections']['EN']=['1']
    with pytest.raises(ValueError,match='input-only'):fill_inputs(original)


def test_unknown_input_is_only_replaced_when_provably_irrelevant():
    original=design(1,0b10,{'I0':[],'O':[99]})
    with pytest.raises(ValueError,match='affects'):fill_inputs(original)
    original=design(1,0b11,{'I0':[],'O':[99]})
    filled,_=fill_inputs(original)
    assert filled['modules']['warp_top']['cells']['lut']['parameters']['INIT']=='1'*16


def test_ha_preserves_carry_pins_and_mode():
    original=design(4,0x9696,{'I0':[],'I1':[11],'I2':[12],'I3':[],'Ci':[13],'Co':[14],'O':[99]})
    cell=original['modules']['warp_top']['cells']['lut'];cell['type']='LUT4_HA';cell['parameters']['I0MUX']='1'
    filled,_=fill_inputs(original);new=filled['modules']['warp_top']['cells']['lut']
    for p in ('Ci','Co','I0','I1','I2'):assert new['connections'][p]==cell['connections'][p]
    assert new['parameters']['I0MUX']=='1' and new['parameters']['INIT']==cell['parameters']['INIT']
