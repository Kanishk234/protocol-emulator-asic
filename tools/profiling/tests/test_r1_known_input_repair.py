"""A timeout alone must never admit a routing repair."""
from copy import deepcopy
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from known_input_repair import validate_trace


def observation():
    return ({'time_ns':115921,'events_at_same_time':4096,'signals':[
        ['Tile_X1Y1_LUT4x8_ha/LF_O',2049],['Tile_X1Y1_LUT4x8_ha/LC_O',2046],
        ['Tile_X1Y1_LUT4x8_ha/LB_O',1]]},
        {'time_ns':115921,'pins':{'h_wvalid':'1','h_wready':'1'}})


@pytest.mark.parametrize('mutation',['time','budget','other_net','duplicate','unknown_ready','idle'])
def test_repair_requires_observed_target_activity(mutation):
    trace,runtime=observation();validate_trace(deepcopy(trace),deepcopy(runtime))
    if mutation=='time':trace['time_ns']+=20
    elif mutation=='budget':trace['events_at_same_time']=0
    elif mutation=='other_net':trace['signals'][0][0]='Tile_X2Y1_LUT4x8_ha/LF_O'
    elif mutation=='duplicate':trace['signals'].append(deepcopy(trace['signals'][0]))
    elif mutation=='unknown_ready':runtime['pins']['h_wready']='X'
    elif mutation=='idle':runtime['pins']['h_wvalid']='0'
    with pytest.raises(ValueError,match='raw native traffic-start'):
        validate_trace(trace,runtime)
