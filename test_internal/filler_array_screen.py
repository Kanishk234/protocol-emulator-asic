"""KLayout fixture generation only; use untouched pinned library geometry."""
import os
from pathlib import Path

import pya

layout = pya.Layout()
layout.read(os.environ["WARP_FILLER_GDS"])
unit = layout.dbu
height = round(3.78 / unit)
cases = {
    "warp_fill1_horizontal": ("sg13cmos5l_fill_1", 0.48, 1, False),
    "warp_fill2_horizontal": ("sg13cmos5l_fill_2", 0.96, 1, False),
    "warp_fill1_rows_same": ("sg13cmos5l_fill_1", 0.48, 2, False),
    "warp_fill2_rows_same": ("sg13cmos5l_fill_2", 0.96, 2, False),
    "warp_fill1_rows_mirrored": ("sg13cmos5l_fill_1", 0.48, 2, True),
    "warp_fill2_rows_mirrored": ("sg13cmos5l_fill_2", 0.96, 2, True),
    "warp_fill1_rows_ground": ("sg13cmos5l_fill_1", 0.48, 2, True),
    "warp_fill2_rows_ground": ("sg13cmos5l_fill_2", 0.96, 2, True),
    "warp_fill4_horizontal": ("sg13cmos5l_fill_4", 1.92, 1, False),
    "warp_fill8_horizontal": ("sg13cmos5l_fill_8", 3.84, 1, False),
    "warp_fill4_rows_mirrored": ("sg13cmos5l_fill_4", 1.92, 2, True),
    "warp_fill8_rows_mirrored": ("sg13cmos5l_fill_8", 3.84, 2, True),
    "warp_fill4_rows_ground": ("sg13cmos5l_fill_4", 1.92, 2, True),
    "warp_fill8_rows_ground": ("sg13cmos5l_fill_8", 3.84, 2, True),
}
for name, (master, width, rows, mirrored) in cases.items():
    source = layout.cell(master)
    if source is None:
        raise RuntimeError(f"Missing pinned cell {master}")
    cell = layout.create_cell(name)
    pitch = round(width / unit)
    for row in range(rows):
        flip = mirrored and (row + int(name.endswith("_ground"))) % 2 == 1
        for column in range(8):
            transform = pya.Trans(pya.Trans.M0 if flip else pya.Trans.R0,
                                  column * pitch, (row + int(flip)) * height)
            cell.insert(pya.CellInstArray(source.cell_index(), transform))
layout.write(str(Path(os.environ["WARP_FILLER_OUT"]) / "filler_arrays.gds"))
