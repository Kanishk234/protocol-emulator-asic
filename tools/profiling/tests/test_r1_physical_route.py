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
