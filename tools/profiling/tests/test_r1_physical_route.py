from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from physical_route import power_phase,routing_policy,check_power_boxes


def test_first_column_power_phase_preserves_existing_fabric_grid():
    for width in (219.84,154.08):
        assert float(power_phase(width)['center_um'])==53.28
        assert routing_policy(width)['PDN_VOFFSET']==50.4
    assert float(power_phase(154.08,1)['center_um'])==9.12


def test_only_footprint_and_boundary_obstructions_change_between_cases():
    a=routing_policy(219.84);b=routing_policy(154.08)
    assert {k for k in a if a[k]!=b[k]}=={'DIE_AREA','ROUTING_OBSTRUCTIONS'}
    assert a['RT_MAX_LAYER']=='Metal4' and a['GRT_OVERFLOW_ITERS']==50
    with pytest.raises(ValueError):routing_policy(160)


def test_global_power_phase_and_full_height_are_required():
    boxes=[dict(net='VPWR',layer='Metal4',rect=[52230,0,54330,185220]),
           dict(net='VGND',layer='Metal4',rect=[56330,0,58430,185220])]
    check_power_boxes(boxes,154.08)
    patches=[dict(net='VPWR',layer='Metal4',rect=[52230,0,54330,200]),
             dict(net='VPWR',layer='Metal4',rect=[52230,185020,54330,185220])]
    check_power_boxes(boxes+patches,154.08)
    with pytest.raises(ValueError):check_power_boxes(boxes[1:]+patches,154.08)
    with pytest.raises(ValueError):check_power_boxes(boxes[:1],154.08)
    boxes[0]['rect'][0]+=1
    with pytest.raises(ValueError):check_power_boxes(boxes,154.08)


def test_actual_primitive_columns_use_global_grid_phase_without_other_policy_changes():
    base=routing_policy(154.08)
    for column,center,offset in [(1,9.12,6.24),(4,96.48,93.60)]:
        policy=routing_policy(154.08,column)
        assert policy['PDN_VOFFSET']==offset
        assert {k for k in base if base[k]!=policy[k]}=={'PDN_VOFFSET'}
        c=round(center*1000)
        boxes=[dict(net='VPWR',layer='Metal4',rect=[c-1050,0,c+1050,185220]),
               dict(net='VGND',layer='Metal4',rect=[c+3050,0,c+5150,185220])]
        check_power_boxes(boxes,154.08,column)
        with pytest.raises(ValueError):check_power_boxes(boxes,154.08)
    with pytest.raises(ValueError):routing_policy(154.08,6)


def test_measured_reserve_width_keeps_actual_prefix_phase_and_chip_channel_pair():
    from physical_route import reserve_geometry,RESERVE_COLUMNS
    from decimal import Decimal
    report=reserve_geometry()
    assert Decimal(report['width_um'])==Decimal('164.64')
    assert Decimal(report['required_width_um'])<=Decimal('164.64')
    assert Decimal(report['required_width_um'])>Decimal('164.16')
    assert power_phase(164.64,1,RESERVE_COLUMNS)['center_um']=='9.12'
    assert power_phase(164.64,4,RESERVE_COLUMNS)['center_um']=='85.92'
    assert Decimal(report['macro_width_um'])==Decimal('1082.88')
    # Fixed G1-phase macro origin and core edge; a full east stripe pair remains.
    end=Decimal('121.44')+Decimal(report['macro_width_um'])
    assert end<Decimal('1232.64')-Decimal('1.05')
    assert Decimal('1232.64')+Decimal('4.1')+Decimal('1.05')<Decimal('1286.4')
    policy=routing_policy(164.64,4,RESERVE_COLUMNS)
    assert policy['PL_TARGET_DENSITY_PCT']==96 and policy['PL_ROUTABILITY_DRIVEN']
    assert policy['PDN_VOFFSET']==83.04
    with pytest.raises(ValueError):routing_policy(164.64,4)
    with pytest.raises(ValueError):power_phase(164.64,4,(164.64,)*6)
