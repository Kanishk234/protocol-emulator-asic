from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from configured_smoke import drive_auxiliary_inputs


def test_every_external_input_is_driven_and_aux_reset_has_correct_polarity():
    text='input Tile_X0Y4_SYS_RESET_RESET_top; input Tile_X1Y4_A_OUT_top; input wire Tile_unused; output Tile_result;'
    connections={'Tile_X1Y4_A_OUT_top':'clk'}
    ports=drive_auxiliary_inputs(text,connections)
    assert set(ports)=={'Tile_X0Y4_SYS_RESET_RESET_top','Tile_X1Y4_A_OUT_top','Tile_unused'}
    assert connections['Tile_X0Y4_SYS_RESET_RESET_top']=='~rst_n'
    assert connections['Tile_X1Y4_A_OUT_top']=='clk'
    assert connections['Tile_unused']=="1'b0" and 'Tile_result' not in connections
    with pytest.raises(ValueError):drive_auxiliary_inputs('input Tile_other;',{})
    with pytest.raises(ValueError):drive_auxiliary_inputs(text,{'Tile_unused':''})
