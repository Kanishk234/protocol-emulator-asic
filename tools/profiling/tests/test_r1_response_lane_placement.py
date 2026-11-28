from copy import deepcopy
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from response_lane_placement import pin_response_lane,BEL
from spi_tick_pipeline_compile import prepare


def design():
    return {'modules':{'warp_top':{'netnames':{'u_user.r_lane':{'bits':[20]}},'cells':{
        'ff':{'type':'LUTFF_SR','parameters':{},'attributes':{},
              'port_directions':{'CLK':'input','D':'input','O':'output','R':'input'},
              'connections':{'CLK':[1],'D':[10],'O':[20],'R':[2]}},
        'lut':{'type':'LUT4','parameters':{'INIT':'1000111110001000'},'attributes':{},
               'port_directions':{'I0':'input','I1':'input','I2':'input','I3':'input','O':'output'},
               'connections':{'I0':[3],'I1':[4],'I2':[5],'I3':[20],'O':[10]}}}}}}


def test_constraint_is_on_retained_lut_and_ff_is_unchanged():
    d=design();original=deepcopy(d);derived,p=pin_response_lane(d)
    assert d==original and derived['modules']['warp_top']['cells']['ff']==original['modules']['warp_top']['cells']['ff']
    assert p['retained_lut']=='lut' and p['required_bel']==BEL and p['logical_graph_preserved']
    assert derived['modules']['warp_top']['cells']['lut']['attributes']['NEXTPNR_BEL']==BEL


@pytest.mark.parametrize('mutation',['ff','constraint','driver'])
def test_unsupported_mapping_cannot_be_constrained(mutation):
    d=design();cells=d['modules']['warp_top']['cells']
    if mutation=='ff':cells['ff']['type']='LUTFF_ESR'
    if mutation=='constraint':cells['lut']['attributes']['NEXTPNR_BEL']='X1Y1/A'
    if mutation=='driver':del cells['lut']
    with pytest.raises(ValueError):pin_response_lane(d)


@pytest.mark.parametrize('mode',[True,1,'true'])
def test_response_placement_requires_explicit_buffer_mode(tmp_path,mode):
    with pytest.raises(ValueError,match='Response-lane'):
        prepare(tmp_path,tmp_path,tmp_path/'out',response_lane=mode)
    assert not (tmp_path/'out').exists()
