"""KLayout fixture generation only; use untouched pinned library geometry."""
import os
import json
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
    "warp_fill2_ground_gap005": ("sg13cmos5l_fill_2", 0.96, 2, True),
    "warp_fill2_ground_gap030": ("sg13cmos5l_fill_2", 0.96, 2, True),
    "warp_fill2_ground_gap300": ("sg13cmos5l_fill_2", 0.96, 2, True),
}
for name, (master, width, rows, mirrored) in cases.items():
    source = layout.cell(master)
    if source is None:
        raise RuntimeError(f"Missing pinned cell {master}")
    cell = layout.create_cell(name)
    pitch = round(width / unit)
    gap = round(int(name.rsplit("_gap", 1)[1]) / 1000 / unit) if "_gap" in name else 0
    for row in range(rows):
        flip = mirrored and (row + int("_ground" in name)) % 2 == 1
        for column in range(8):
            transform = pya.Trans(pya.Trans.M0 if flip else pya.Trans.R0,
                                  column * pitch, row * (height + gap) + int(flip) * height)
            cell.insert(pya.CellInstArray(source.cell_index(), transform))
layout.write(str(Path(os.environ["WARP_FILLER_OUT"]) / "filler_arrays.gds"))

# Retain actual ground-boundary polygons for geometric diagnosis, not signoff.
cell = layout.cell("warp_fill2_rows_ground")
window = pya.Box(0, round(3.25 / unit), round(1.92 / unit), round(4.31 / unit))
layers = {"Activ": 1, "Cont": 6, "Metal1": 8, "pSD": 14, "NWell": 31}
geometry = {"units": "um", "window": [0, 3.25, 1.92, 4.31], "layers": {}}
for name, number in layers.items():
    region = pya.Region(cell.begin_shapes_rec(layout.layer(number, 0))) & pya.Region(window)
    geometry["layers"][name] = [
        [[round(point.x * unit, 6), round(point.y * unit, 6)] for point in polygon.each_point_hull()]
        for polygon in region.each()]
(Path(os.environ["WARP_FILLER_OUT"]) / "ground_boundary_polygons.json").write_text(
    json.dumps(geometry, indent=2) + "\n")
