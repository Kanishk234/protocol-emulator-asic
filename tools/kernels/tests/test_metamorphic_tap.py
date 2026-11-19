"""L4-TAP: paired, cycle-exact whole-model checks and blocking counterexamples."""
import json
import pytest
from kernels.metamorphic_tap import compare_model


@pytest.mark.parametrize('baud',[115200,460800])
@pytest.mark.parametrize('bad',[False,True])
def test_uart_tap_never_changes_blocking_path(baud,bad):
    print('L4_TAP '+json.dumps(compare_model('uart',baud,bad=bad),sort_keys=True))


@pytest.mark.parametrize('period',[50,10,6])
def test_spi_tap_never_changes_blocking_path(period):
    print('L4_TAP '+json.dumps(compare_model('spi',period),sort_keys=True))


@pytest.mark.parametrize('period',[500,124,50])
@pytest.mark.parametrize('stretch',[0,40,107])
def test_i2c_tap_never_changes_blocking_path(period,stretch):
    print('L4_TAP '+json.dumps(compare_model('i2c',period,stretch),sort_keys=True))


@pytest.mark.parametrize('protocol,rate',[('uart',460800),('spi',10),('i2c',124)])
def test_blocking_subscriber_negative_changes_active_path(protocol,rate):
    with pytest.raises(AssertionError,match='blocking path difference|pad difference|delivery time difference'):
        compare_model(protocol,rate,mode='blocking')
