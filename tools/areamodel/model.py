"""Area model for the WARP fabric on TT 6x4, IHP CMOS5L.

Every constant below comes from a measurement; the source is next to it. The model answers:
which grids of FABulous tiles fit the die next to the shell, and how many LUT4s and primitive
instances each gives. It is deliberately simple (tile counting); place-and-route of the full
fabric replaces it when available.

The primitive tile is measured: D-026 reports 35,094 µm² standard-cell area versus 36,047 µm²
for a LUT tile, in the same 219.84 × 185.22 µm footprint. Grid capacity is still modeled by
tile count; the measured cell-area ratio is reported separately.
"""

from dataclasses import dataclass
from typing import Dict, List

# --- measured (sources in docs/reports/tile_cmos5l.md, PHYSICAL_DESIGN_AND_CI.md, profiling.md)
DIE_W, DIE_H = 1289.28, 710.64          # µm, TT 6x4 CMOS5L template DEF (gds run 36170807513)
CORE_AREA = 902_417.0                   # µm², same run
LUT_TILE = (219.84, 185.22)             # µm, LUT4x8_ha routed on CMOS5L, Metal2-Metal4 (run 2/3)
LUTS_PER_TILE = 8
EDGE_NS_H = 56.70                       # µm, N/S terminator tile height (IHP tile library sizes)
EDGE_EW_W = 68.64                       # µm, E/W IO tile width
# Measured tile standard-cell area (D-026, CMOS5L, same physical footprint).
LUT_TILE_STD_CELL_UM2 = 36_047.0
PRIM_TILE_STD_CELL_UM2 = 35_094.0

SHELL_W_MIN = 200.0                     # µm, width left for the shell column (estimate; the shell
                                        # is ~30-50K µm² of cells at normal density)


def prim_tile_um2(timers: int = 2, shifts: int = 2) -> float:
    """Measured standard-cell area for the 2-timer/2-shift primitive tile (D-026).

    The parameters remain for compatibility with the original model API; D-026's physical
    result only measures the 2+2 tile, so alternate primitive counts are not extrapolated.
    """
    if (timers, shifts) != (2, 2):
        raise ValueError("measured area is available only for the 2-timer/2-shift tile")
    return PRIM_TILE_STD_CELL_UM2


@dataclass
class Grid:
    cols: int
    rows: int
    prim_tiles: int = 0

    @property
    def width(self) -> float:
        return self.cols * LUT_TILE[0] + 2 * EDGE_EW_W

    @property
    def height(self) -> float:
        return self.rows * LUT_TILE[1] + 2 * EDGE_NS_H

    @property
    def shell_width(self) -> float:
        return DIE_W - self.width

    def fits(self) -> bool:
        return self.height <= DIE_H and self.shell_width >= SHELL_W_MIN

    @property
    def lut4(self) -> int:
        return (self.cols * self.rows - self.prim_tiles) * LUTS_PER_TILE

    @property
    def timers(self) -> int:
        return 2 * self.prim_tiles

    @property
    def shifts(self) -> int:
        return 2 * self.prim_tiles


def scenarios() -> List[Dict]:
    out = []
    for cols in range(3, 6):
        for rows in range(2, 4):
            for prim in (0, 1, 2):
                g = Grid(cols, rows, prim)
                out.append({"grid": f"{cols}x{rows}", "prim_tiles": prim, "fits": g.fits(),
                            "width_um": round(g.width, 1), "height_um": round(g.height, 1),
                            "shell_col_um": round(g.shell_width, 1), "lut4": g.lut4,
                            "timers": g.timers, "shifts": g.shifts})
    return out


def main() -> None:
    lt = LUT_TILE[0] * LUT_TILE[1]
    print(f"Tile footprint {lt:,.0f} µm² ({lt / LUTS_PER_TILE:,.0f} per LUT4); "
          f"LUT tile standard cells {LUT_TILE_STD_CELL_UM2:,.0f} µm²; "
          f"primitive tile standard cells {prim_tile_um2():,.0f} µm² "
          f"({prim_tile_um2() / LUT_TILE_STD_CELL_UM2:.2f}x a LUT tile); "
          "both tiles use the same physical footprint")
    print("| grid | primitive tiles | fits | fabric W x H (µm) | shell column (µm) | LUT4 | timers | shift regs |")
    print("|---|---|---|---|---|---|---|---|")
    for s in scenarios():
        print(f"| {s['grid']} | {s['prim_tiles']} | {'yes' if s['fits'] else 'no'} | {s['width_um']} x {s['height_um']} "
              f"| {s['shell_col_um']} | {s['lut4']} | {s['timers']} | {s['shifts']} |")


if __name__ == "__main__":
    main()
