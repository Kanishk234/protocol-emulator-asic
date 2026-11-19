"""L4-LOOP on two real lanes; IDLE compares the same decoded stream."""
import json
import pytest
from kernels.metamorphic_loop import PAYLOAD,run_model,audit

PROFILES=[('uart',115200),('uart',460800),('spi',50),('spi',10),('spi',6),
          ('i2c',500),('i2c',124),('i2c',50)]


@pytest.mark.parametrize('protocol,rate',PROFILES)
def test_two_lane_loop_and_random_idle(protocol,rate,tmp_path):
    results=[];markers=[]
    for seed in [None,7129,19317]:
        trace,received,loop=run_model(protocol,rate,seed=seed)
        observation=audit(protocol,rate,PAYLOAD,trace,tmp_path/f'{protocol}_{rate}_{seed}.vcd')
        results.append(received);markers.append(observation["frame_start_clocks"])
        print('L4_LOOP_IDLE '+json.dumps({'protocol':protocol,'rate':rate,'seed':seed,'bytes':len(PAYLOAD),
              'clocks':loop.clock,'idle_clocks':sum(loop.extra_idle),**observation},sort_keys=True))
    assert results[0]==results[1]==results[2]
    assert markers[0][0]==markers[1][0]==markers[2][0]
    assert markers[0][1:]!=markers[1][1:] and markers[0][1:]!=markers[2][1:]


@pytest.mark.parametrize('protocol,rate',[('uart',460800),('spi',10),('i2c',124)])
def test_disconnected_loop_negative_is_detected(protocol,rate):
    with pytest.raises(AssertionError,match='timeout|loop|i2c|spi|uart'):
        run_model(protocol,rate,payload=b'\x55',disconnected=True)
