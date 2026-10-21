from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from mapped_cost import validate_cells


def test_live_configuration_and_metadata_are_accepted():
    validate_cells({'sg13cmos5l_dlhq_1':566,'sg13cmos5l_mux2_1':5,'$scopeinfo':3},566)
    validate_cells({},0)


@pytest.mark.parametrize('cells',[
    {'$_DLATCH_P_':566},
    {'sg13cmos5l_dlhq_1':565},
    {'sg13cmos5l_dlhq_1':567},
    {'sg13cmos5l_dlhq_1':566,'unmapped_mux':1}])
def test_unmapped_or_changed_configuration_rejected(cells):
    with pytest.raises(ValueError):validate_cells(cells,566)
