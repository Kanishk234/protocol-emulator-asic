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


def test_only_known_disabled_clock_entries_removed():
    from physical_preflight import physical_pin_order
    generated={'X0Y0':{'NORTH':[dict(pins=['UserCLKo'],min_distance=None),
                                dict(pins=['real'],min_distance=None)],
                       'SOUTH':[dict(pins=['UserCLK'],min_distance=None)]}}
    order,removed=physical_pin_order(generated,{'real'},True)
    assert removed==['UserCLK','UserCLKo'] and order['N'][0]['pins']==['real']
    with pytest.raises(ValueError):physical_pin_order(generated,{'real'},False)
    generated['X0Y0']['NORTH'].append(dict(pins=['other_missing']))
    with pytest.raises(ValueError):physical_pin_order(generated,{'real'},True)


def test_missing_or_duplicate_actual_pins_never_filtered_out():
    from physical_preflight import physical_pin_order
    with pytest.raises(ValueError):physical_pin_order({'X0Y0':{'NORTH':[dict(pins=['a'])]}},{'a','b'},True)
    with pytest.raises(ValueError):physical_pin_order({'X0Y0':{'NORTH':[dict(pins=['a','a'])]}},{'a'},True)


def test_legacy_side_groups_preserve_bus_order_without_equal_segment_starvation():
    from physical_preflight import physical_pin_order
    generated={'X0Y0':{'EAST':[dict(pins=['data'],min_distance=None,sort_mode='bus_major'),
                               dict(pins=['frame'],min_distance=None,sort_mode='bus_major')]}}
    order,_=physical_pin_order(generated,{'data','frame'},True)
    assert len(order['E'])==1 and order['E'][0]['pins']==['data','frame']
    generated['X0Y0']['EAST'][1]['min_distance']=3
    with pytest.raises(ValueError):physical_pin_order(generated,{'data','frame'},True)


def test_native_import_accepts_only_two_physical_constant_drivers():
    from physical_preflight import check_import_counts
    original={'sg13cmos5l_dlhq_1':438,'sg13cmos5l_mux2_1':8}
    actual={**original,'sg13cmos5l_tiehi':1,'sg13cmos5l_tielo':1}
    check_import_counts(actual,original)
    for changed in ({**actual,'sg13cmos5l_dlhq_1':437},
                    {**actual,'sg13cmos5l_tiehi':2},
                    {**actual,'sg13cmos5l_buf_1':1},original):
        with pytest.raises(ValueError):check_import_counts(changed,original)
