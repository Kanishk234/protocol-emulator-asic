"""Cover the candidate adapter's user I/O and reset ownership boundaries."""
from profiling.r1_shell_adapter import shell_wrapper
import pytest


def test_shell_adapter_maps_bidirectional_pads_and_shell_reset(tmp_path):
    (tmp_path/'pins.csv').write_text('pin,bel,direction\nclk,X1Y4/A,clock\nrst_n,X1Y4/B,in\nFAB_IO7,X0Y2/D,inout\nFAB_IN4,X7Y2/A,in\nFAB_OUT5,X7Y3/C,out\nh_status[7],X4Y0/A,out_en\n')
    (tmp_path/'fabric.v').write_text('input Tile_X0Y4_SYS_RESET_RESET_top; input Tile_unused; input Tile_X1Y4_A_OUT_top; input Tile_X1Y4_B_OUT_top; input Tile_X0Y2_D_OUT_top; input Tile_X7Y2_A_OUT_top;')
    source,ports=shell_wrapper(tmp_path)
    for text in ('.Tile_X0Y2_D_OUT_top(io_in[7])', '.Tile_X0Y2_D_IN_top(io_out[7])',
                 '.Tile_X0Y2_D_EN_top(io_oe[7])', '.Tile_X1Y4_B_OUT_top(user_rst_n)',
                 '.Tile_X0Y4_SYS_RESET_RESET_top(user_reset)', '.Tile_X7Y2_A_OUT_top(fab_in[4])',
                 '.Tile_X7Y3_C_IN_top(fab_out[5])', '.Tile_X4Y0_A_EN_top(h_status[7])',
                 ".Tile_unused(1'b0)", '.ARCH_VERSION(16\'h00fe)'):
        assert text in source
    assert len(ports)==6
    (tmp_path/'fabric.v').write_text('input Tile_unused;')
    with pytest.raises(ValueError,match='auxiliary reset'):shell_wrapper(tmp_path)
