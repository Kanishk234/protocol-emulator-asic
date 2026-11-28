from copy import deepcopy
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from local_capture_controls import absorb_capture,vendor_semantics


def design():
    cells={}
    for i in range(8):
        cells['ff'+str(i)]={'type':'LUTFF_ESR','parameters':{},'attributes':{'src':'original'},
            'port_directions':{'CLK':'input','D':'input','E':'input','R':'input','O':'output'},
            'connections':{'CLK':[2],'D':[30+i],'E':[20],'R':[21],'O':[10+i]}}
    cells['other']={'type':'wp_timer','connections':{'load':[50]},'parameters':{}}
    return {'modules':{'warp_top':{'netnames':{'u_user.srdata':{'bits':list(range(10,18))}},'cells':cells}}}


def test_every_capture_transition_preserves_enable_before_reset_priority():
    original=design();before=deepcopy(original);derived,proof=absorb_capture(original)
    assert original==before and proof['changed_flip_flops']==8
    assert derived['modules']['warp_top']['cells']['other']==original['modules']['warp_top']['cells']['other']
    for row in proof['changes']:
        old=row['before'];new=row['after'];lut=row['lut']
        assert old['type']==new['type'] and old['attributes']==new['attributes']
        assert old['connections']['CLK']==new['connections']['CLK'] and old['connections']['O']==new['connections']['O']
        assert new['connections']['E']==['1'] and new['connections']['R']==['0']
        for d in (0,1):
            for e in (0,1):
                for r in (0,1):
                    for q in (0,1):
                        old_next=(0 if r else d) if e else q
                        address=d|(e<<1)|(r<<2)|(q<<3)
                        assert (int(lut['parameters']['INIT'],2)>>address)&1==old_next


def test_wrong_ff_family_or_control_group_is_rejected():
    source=design();source['modules']['warp_top']['cells']['ff0']['type']='LUTFF_SRE'
    with pytest.raises(ValueError,match='Unsupported'):absorb_capture(source)
    source=design();source['modules']['warp_top']['cells']['ff0']['connections']['E']=[99]
    with pytest.raises(ValueError,match='controls differ'):absorb_capture(source)
    source=design();derived,_=absorb_capture(source)
    with pytest.raises(ValueError,match='already transformed'):absorb_capture(derived)
    with pytest.raises(ValueError,match='vendor'):vendor_semantics('module LUTFF_ESR; endmodule')
