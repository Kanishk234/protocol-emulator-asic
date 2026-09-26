from areamodel.model import Grid, LUT_TILE, prim_tile_um2, scenarios


def test_measured_tile_gives_5090_um2_per_lut():
    assert round(LUT_TILE[0] * LUT_TILE[1] / 8) == 5090


def test_4x3_fits_with_a_shell_column_and_5x3_does_not():
    assert Grid(4, 3).fits()
    assert not Grid(5, 3).fits()          # leaves no room for the shell
    assert not Grid(4, 4).fits()          # taller than the die


def test_primitive_tiles_trade_luts_for_primitives():
    g = Grid(4, 3, prim_tiles=2)
    assert (g.lut4, g.timers, g.shifts) == (80, 4, 4)


def test_primitive_tile_is_close_to_a_lut_tile():
    assert 0.9 < prim_tile_um2() / (LUT_TILE[0] * LUT_TILE[1]) < 1.2


def test_largest_fitting_generic_grid_is_96_lut4():
    assert max(s["lut4"] for s in scenarios() if s["fits"] and s["prim_tiles"] == 0) == 96
