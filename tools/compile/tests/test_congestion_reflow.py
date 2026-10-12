"""Power-phase coverage must follow actual fragmented rows after relocation."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'test_internal'))
from cloud_congestion_reflow import check_rows, EDIT

G='META\t1000\t480\nBOX\tcell\tCORE\t480\t3780\t2880\t7560\n'
R='ROW row site 0 3780 FS DO 10 BY 1 STEP 480 0 ;\n'


@pytest.mark.parametrize('orient',['MX','R180'])
def test_legal_vertical_phase_allows_horizontal_mirroring(orient):
    assert check_rows(R,G,{'cell':['buffer','480 3780',orient,'PLACED']})==1


@pytest.mark.parametrize('mutation',['wrong_phase','missing_rows','outside_fragment','wrong_site','wrong_vertical_position'])
def test_missing_or_inconsistent_native_row_rejected(mutation):
    row=R;geom=G;orient='MX'
    if mutation=='wrong_phase':orient='MY'
    elif mutation=='missing_rows':row=''
    elif mutation=='outside_fragment':row=row.replace('DO 10','DO 2')
    elif mutation=='wrong_site':row=row.replace('STEP 480','STEP 960')
    elif mutation=='wrong_vertical_position':geom=geom.replace('480\t3780','480\t7560')
    with pytest.raises(ValueError):check_rows(row,geom,{'cell':['buffer','480 3780',orient,'PLACED']})


def test_reflow_does_not_enable_sizing_or_move_io_pins():
    assert '-routability_driven' in EDIT
    assert '-timing_driven' not in EDIT and '-place_ios' not in EDIT
    assert 'swapMaster' not in EDIT and 'repair_timing' not in EDIT
    assert EDIT.index('read_liberty') < EDIT.index('global_placement -') < EDIT.index('check_placement')


def test_geometry_export_has_database_handle():
    assert EDIT.index('set block [ord::get_db_block]') < EDIT.index('[$block getRows]')
