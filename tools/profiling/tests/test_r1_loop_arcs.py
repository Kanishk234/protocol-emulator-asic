from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from loop_arcs import loop_cells,render_trace


def test_loop_coverage_requires_original_marker_and_complete_cell_set():
    text='Warning: There are 8 combinational loops in the design.\n'+''.join(f'  Tile_X2Y3_LUT4x8_ha/_{i}_/X\n' for i in range(23))
    assert len(loop_cells(text))==23
    with pytest.raises(ValueError):loop_cells(text.replace('8 combinational','7 combinational'))
    with pytest.raises(ValueError):loop_cells(text+'  Tile_X2Y3_LUT4x8_ha/_99_/X\n')


def fixture(kind='sg13cmos5l_mux2_1'):
    cell=dict(type=kind,port_directions={'A0':'input','A1':'input','S':'input','X':'output'},
              connections={'A0':[1],'A1':[2],'S':[3],'X':[4]})
    return {'LUT4x8_ha':{'cells':{'_1_':cell}}},{'cells':{'Tile_X2Y3_LUT4x8_ha':{'type':'LUT4x8_ha'}}}


def test_trace_reports_every_input_edge_without_timing_mutations():
    modules,top=fixture()
    text,pairs=render_trace(['Tile_X2Y3_LUT4x8_ha/_1_'],modules,top)
    assert len(pairs)==3 and text.count('sta::report_edges')==3
    assert 'sta::report_constant' in text
    assert all(command not in text for command in ('set_case_analysis','set_disable_timing','set_false_path','-digits'))


def test_sequential_and_bus_cells_cannot_silently_enter_arc_collection():
    modules,top=fixture('sg13cmos5l_dfrbpq_1')
    with pytest.raises(ValueError):render_trace(['Tile_X2Y3_LUT4x8_ha/_1_'],modules,top)
    modules,top=fixture();modules['LUT4x8_ha']['cells']['_1_']['connections']['S']=[3,4]
    with pytest.raises(ValueError):render_trace(['Tile_X2Y3_LUT4x8_ha/_1_'],modules,top)
