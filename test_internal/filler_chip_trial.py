"""D-052 whole-layout scratch overlay; source route still has three markers."""
import hashlib
import json
import os
from pathlib import Path
import sys

import pya

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "patches"))
from ihp_filler_psd_trial import clone_trial

source = Path(os.environ["WARP_CHIP_GDS"])
expected = os.environ.get("WARP_CHIP_EXPECTED_SHA256",
                          "befeaf6c9ff440400108034bbc6eca90de8a96a0c8dd65239aa0cd745aa41786")
if "WARP_CHIP_EXPECTED_SHA256" in os.environ:
    for required in ("WARP_CHIP_SOURCE_RUN", "WARP_CHIP_NATIVE_MARKERS"):
        if required not in os.environ:
            raise RuntimeError("Fresh source needs explicit provenance and native scope")
if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
    raise RuntimeError("Not authenticated no-decap GDS from37648945387")
layout = pya.Layout()
layout.read(str(source))
top = layout.cell("tt_um_warp")
if top is None:
    raise RuntimeError("Missing chip top")
psd = layout.layer(14, 0)
before = {layer: pya.Region(top.begin_shapes_rec(layer)).merged()
          for layer in layout.layer_indexes() if layer != psd}
replacements = {}
manifest = []
for width_id, width in ((1, 0.48), (2, 0.96)):
    original = layout.cell(f"sg13cmos5l_fill_{width_id}")
    if original is None:
        raise RuntimeError("Missing expected filler master")
    clone, record = clone_trial(layout, original, width)
    replacements[original.cell_index()] = clone.cell_index()
    manifest.append(record)
counts = dict.fromkeys(replacements, 0)
for cell in list(layout.each_cell()):
    # Changing a master can reorder the live instance iterator.
    for inst in list(cell.each_inst()):
        old = inst.cell_index
        if old in replacements:
            if inst.is_regular_array():
                raise RuntimeError("Unexpected array: inventory requires explicit instances")
            counts[old] += 1
            inst.cell_index = replacements[old]
expected_counts = json.loads(os.environ.get("WARP_CHIP_FILLER_COUNTS",
    '{"sg13cmos5l_fill_1":464,"sg13cmos5l_fill_2":20250}'))
if set(expected_counts) != {"sg13cmos5l_fill_1", "sg13cmos5l_fill_2"} or any(
        type(value) is not int or value <= 0 for value in expected_counts.values()):
    raise RuntimeError("Invalid expected filler inventory")
actual_counts = {layout.cell(index).name: count for index, count in counts.items()}
if actual_counts != expected_counts:
    raise RuntimeError(f"Unexpected source filler inventory: {actual_counts}; expected {expected_counts}")
out = Path(os.environ["WARP_FILLER_OUT"])
differences = []
for layer, region in before.items():
    after = pya.Region(top.begin_shapes_rec(layer)).merged()
    delta = region ^ after
    if not delta.is_empty():
        differences.append({"layer": str(layout.get_info(layer)),
                            "before_area_dbu2": region.area(), "after_area_dbu2": after.area(),
                            "delta_area_dbu2": delta.area(), "delta_bbox": str(delta.bbox()),
                            "sample_polygons": [str(polygon) for polygon in list(delta.each())[:4]]})
(out / "non_psd_xor.json").write_text(json.dumps(differences, indent=2) + "\n")
if differences:
    raise RuntimeError("Whole chip changed on a non-pSD layer; see non_psd_xor.json")
layout.write(str(out / "chip_trial.gds"))
(out / "chip_trial_manifest.json").write_text(json.dumps({
    "source_run": int(os.environ.get("WARP_CHIP_SOURCE_RUN", "37648945387")), "source_sha256": expected,
    "source_native_markers": int(os.environ.get("WARP_CHIP_NATIVE_MARKERS", "3")), "replaced_instances": sum(counts.values()),
    "other_layers_xor_empty": True, "trials": manifest,
    "actual_filler_counts": actual_counts, "expected_filler_counts": expected_counts,
    "physical_or_timing_acceptance": False}, indent=2) + "\n")
