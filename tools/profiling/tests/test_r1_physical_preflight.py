from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from physical_preflight import check_pins


def inventory(boxes):
    return dict(die=[0,0,100,100],pins={name:dict(boxes=value) for name,value in boxes.items()})


def test_disjoint_signal_pins_and_cross_layer_overlap_are_accepted():
    check_pins(inventory({'a':[['M2',0,0,5,10]],'b':[['M2',5,0,10,10]],
                          'c':[['M3',0,0,5,10]]}),{'a','b','c'})


@pytest.mark.parametrize('boxes,expected',[
    ({'a':[]},{'a'}),
    ({'a':[['M2',0,0,5,10]]},{'a','missing'}),
    ({'a':[['M2',-1,0,5,10]]},{'a'}),
    ({'a':[['M2',0,0,0,10]]},{'a'}),
    ({'a':[['M2',0,0,5,10]],'b':[['M2',4,0,10,10]]},{'a','b'})])
def test_invalid_native_pin_evidence_rejected(boxes,expected):
    with pytest.raises(ValueError):check_pins(inventory(boxes),expected)
