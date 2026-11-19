"""The pinned independent decoder must finish a real eleven-clock capture."""
import hashlib
import re

import pytest
from sigrok_support import decode


def capture(path,byte,parity_bad=False,stop_bad=False):
    parity=1-(byte.bit_count()&1)
    bits=[0,*[(byte>>i)&1 for i in range(8)],parity^parity_bad,int(not stop_bad)]
    lines=['$timescale 20 ns $end','$scope module fixture $end',
           '$var wire 1 ! clk $end','$var wire 1 " data $end',
           '$upscope $end','$enddefinitions $end','#0','1!','1"']
    clock=3000
    for bit in bits:
        lines += [f'#{clock}',f'{int(bit)}"'];clock+=750
        lines += [f'#{clock}','0!'];clock+=1500
        lines += [f'#{clock}','1!'];clock+=750
    lines += [f'#{clock}','1"',f'#{clock+3000}']
    path.write_text('\n'.join(lines)+'\n')
    return bits


@pytest.mark.parametrize('byte',[0x00,0xFF,0x5A,0xC3])
@pytest.mark.parametrize('parity_bad,stop_bad',[(False,False),(True,False),(False,True),(True,True)])
def test_real_stop_rise_completes_frame_without_extra_clock(tmp_path,byte,parity_bad,stop_bad):
    path=tmp_path/'eleven_clocks.vcd'
    expected=capture(path,byte,parity_bad,stop_bad)
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    text=decode(path,'ps2:clk=clk:data=data','ps2',required=True)
    assert re.findall(r'Data: ([0-9a-fA-F]{2})\b',text)==[f'{byte:02x}'],text
    assert text.count('Parity error')==int(parity_bad),text
    bit_text=decode(path,'ps2:clk=clk:data=data','ps2=bit',required=True)
    actual=[int(x) for x in re.findall(r': ([01])$',bit_text,re.M)]
    assert actual==expected,(actual,expected)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before
