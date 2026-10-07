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
expected = "befeaf6c9ff440400108034bbc6eca90de8a96a0c8dd65239aa0cd745aa41786"
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
    for inst in cell.each_inst():
        old = inst.cell_index
        if old in replacements:
            if inst.is_regular_array():
                raise RuntimeError("Unexpected array: inventory requires explicit instances")
            counts[old] += 1
            inst.cell_index = replacements[old]
if sorted(counts.values()) != [464, 20250]:
    raise RuntimeError(f"Unexpected source filler inventory: {counts}")
for layer, region in before.items():
    if not (region ^ pya.Region(top.begin_shapes_rec(layer))).is_empty():
        raise RuntimeError("Whole chip changed on a non-pSD layer")
out = Path(os.environ["WARP_FILLER_OUT"])
layout.write(str(out / "chip_trial.gds"))
(out / "chip_trial_manifest.json").write_text(json.dumps({
    "source_run": 37648945387, "source_sha256": expected,
    "source_native_markers": 3, "replaced_instances": sum(counts.values()),
    "other_layers_xor_empty": True, "trials": manifest,
    "physical_or_timing_acceptance": False}, indent=2) + "\n")
