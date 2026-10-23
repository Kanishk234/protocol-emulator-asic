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
