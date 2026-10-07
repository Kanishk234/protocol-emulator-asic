"""Untouched library controls and separately named D-052 scratch overlays."""
import os
import json
from pathlib import Path
import sys
import hashlib

import pya

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "patches"))
from ihp_filler_psd_trial import clone_trial

layout = pya.Layout()
layout.read(os.environ["WARP_FILLER_GDS"])
source_hash = hashlib.sha256(Path(os.environ["WARP_FILLER_GDS"]).read_bytes()).hexdigest()
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
trial_manifest = []
for width_id, width in ((1, 0.48), (2, 0.96)):
    source = layout.cell(f"sg13cmos5l_fill_{width_id}")
    clone, record = clone_trial(layout, source, width)
    trial_manifest.append(record)
    for fixture, rows in (("horizontal", 1), ("rows_mirrored", 2), ("rows_ground", 2)):
        cases[f"warp_trial{width_id}_{fixture}"] = (clone.name, width, rows, rows == 2)
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
# A geometry-identical flattened control isolates hierarchy/import effects.
original = layout.cell("warp_fill2_rows_ground")
flat = layout.create_cell("warp_fill2_ground_flat")
flat.copy_tree(original)
flat.flatten(False)
for layer in layout.layer_indexes():
    if not (pya.Region(original.begin_shapes_rec(layer)) ^
            pya.Region(flat.begin_shapes_rec(layer))).is_empty():
        raise RuntimeError("Flattened control changed geometry")
if hashlib.sha256(Path(os.environ["WARP_FILLER_GDS"]).read_bytes()).hexdigest() != source_hash:
    raise RuntimeError("Pinned source GDS changed")
layout.write(str(Path(os.environ["WARP_FILLER_OUT"]) / "filler_arrays.gds"))
(Path(os.environ["WARP_FILLER_OUT"]) / "trial_manifest.json").write_text(
    json.dumps({"source_sha256": source_hash, "flatten_xor_empty": True,
                "trials": trial_manifest, "qualified_for_chip": False}, indent=2) + "\n")

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
