"""D-191 declared intervals only; raw fixed overhead and gaps remain visible."""
import copy
import json
import pytest
from kernels.metamorphic_scale import run_model,compare,audit,metrics

PROFILES=[('uart',500000,250000),('uart',625000,312500),
          ('spi',10,20),('spi',20,40),('spi',50,100),
          ('i2c',50,100),('i2c',100,200),('i2c',124,248)]


@pytest.mark.parametrize('protocol,fast,slow',PROFILES)
def test_programmed_intervals_double_with_identical_payload(protocol,fast,slow,tmp_path):
    observations=[]
    for rate in [fast,slow]:
        trace,result=run_model(protocol,rate)
        result['capture_sha256']=audit(protocol,rate,trace,tmp_path/f'{protocol}_{rate}.vcd')
        observations.append(result)
    compare(protocol,*observations)
    print('L4_SCALE '+json.dumps({'protocol':protocol,'rates':[fast,slow],'observations':observations},sort_keys=True))


@pytest.mark.parametrize('protocol,rate',[('uart',500000),('spi',20),('i2c',100)])
def test_one_edge_shift_is_not_hidden_as_a_gap_or_latency(protocol,rate):
    trace,_=run_model(protocol,rate)
    name={'uart':'tx','spi':'clk','i2c':'scl'}[protocol]
    line=trace[name]
    changes=[i for i in range(1,len(line)) if line[i]!=line[i-1]]
    changed=copy.deepcopy(trace)
    point=changes[3]
    changed[name][point]=changed[name][point-1]
    with pytest.raises(AssertionError):metrics(protocol,rate,changed)
