from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from layout_budget import describe,layouts


def test_external_chip_pair_does_not_mask_unpowered_border_tile():
    result=layouts()['primitive_leaf_growth']
    assert result['geometric_chip_fit'] and result['chip_east_full_power_pairs_um']
    assert result['unpowered_columns']==[7]
    assert not result['static_power_gate']


def test_reallocation_preserves_outer_footprint_and_powers_every_column():
    all_layouts=layouts();result=all_layouts['reallocated_west']
    assert result['column_widths_um'][0]=='47.52'
    assert result['macro_width_um']==all_layouts['original_uniform']['macro_width_um']=='1061.76'
    assert result['static_power_gate'] and not result['unpowered_columns']
    assert result['column_power'][2]['full_core_power_pairs_um'][0][0]=='30.24'
    assert result['column_power'][5]['full_core_power_pairs_um'][0][0]=='107.04'
    assert not result['physical_acceptance'] and not result['timing_acceptance']


def test_bad_site_alignment_and_nonplaceable_border_are_rejected():
    with pytest.raises(ValueError):describe(47.51,(154.08,)*6)
    with pytest.raises(ValueError):describe(4.8,(154.08,)*6)


def test_balanced_case_uses_correct_row_height_and_actual_column_prefix():
    from layout_budget import balanced_case
    assert balanced_case('northwest')['height']==56.70
    assert balanced_case('west_io')['height']==185.22
    assert balanced_case('northwest')['width']==47.52
    assert balanced_case('primitive1')['center_um']=='30.24'
    assert balanced_case('primitive4')['center_um']=='107.04'
    with pytest.raises(ValueError):balanced_case('another_width')


def test_balanced_physical_policy_changes_only_dimensions_and_power_phase():
    from physical_route import balanced_policy,routing_policy
    base=routing_policy(154.08)
    for name in ('west_io','northwest','southwest','primitive1','primitive4'):
        p=balanced_policy(name)
        assert {k for k in p if p[k]!=base[k]}=={'DIE_AREA','PDN_VOFFSET','ROUTING_OBSTRUCTIONS'}
        assert p['PL_TARGET_DENSITY_PCT']==96 and p['GRT_OVERFLOW_ITERS']==50
        assert p['CLOCK_PORT'] is None


def test_short_corner_power_pins_need_full_corner_height_and_in_die_width():
    from physical_route import check_power_boxes
    boxes=[dict(net='VPWR',layer='Metal4',rect=[10950,0,13050,56700]),
           dict(net='VGND',layer='Metal4',rect=[15050,0,17150,56700])]
    check_power_boxes(boxes,47.52,height=56.70,expected_center='12')
    with pytest.raises(ValueError):check_power_boxes(boxes,47.52,expected_center='12')
    boxes[0]['rect'][0]=-1
    with pytest.raises(ValueError):check_power_boxes(boxes,47.52,height=56.70,expected_center='12')
