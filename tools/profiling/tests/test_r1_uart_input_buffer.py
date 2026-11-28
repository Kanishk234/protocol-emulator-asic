from copy import deepcopy
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from uart_input_buffer import buffer_uart_rx


def design():
    return {'modules':{'warp_top':{'netnames':{'u_user.u_uart.g_prims.u_rx.sync':{'bits':[20,21]},
        'u_user.rst_n':{'bits':[5]}},'cells':{'rx':{'type':'LUTFF_SS','parameters':{},'attributes':{'src':'original'},
        'port_directions':{'CLK':'input','D':'input','S':'input','O':'output'},
        'connections':{'CLK':[2],'D':[10],'S':[11],'O':[20]}},
        'other':{'type':'LUTFF_SS','parameters':{},'attributes':{},'connections':{'D':[20],'O':[21]}}}}}}


def test_buffer_preserves_binary_data_and_synchronizer_controls():
    source=design();original=deepcopy(source);derived,proof=buffer_uart_rx(source)
    assert source==original and proof['logical_buffer_luts']==4
    old=proof['before'];new=proof['after'];assert old['type']==new['type']
    for pin in ('CLK','S','O'):assert old['connections'][pin]==new['connections'][pin]
    assert new['attributes']['NEXTPNR_BEL']=='X6Y1/C'
    for value in (0,1):
        for reset in (0,1):
            signal=value
            for row in proof['chain']:
                address=signal|(reset<<1)|(reset<<2)|(reset<<3)
                signal=(int(row['cell']['parameters']['INIT'],2)>>address)&1
            assert signal==value
    assert derived['modules']['warp_top']['cells']['other']==original['modules']['warp_top']['cells']['other']


def test_existing_constraint_or_wrong_ff_cannot_be_overridden():
    source=design();source['modules']['warp_top']['cells']['rx']['attributes']['NEXTPNR_BEL']='X1Y1/A'
    with pytest.raises(ValueError,match='already exists'):buffer_uart_rx(source)
    source=design();source['modules']['warp_top']['cells']['rx']['type']='LUTFF_SR'
    with pytest.raises(ValueError,match='Unsupported'):buffer_uart_rx(source)
