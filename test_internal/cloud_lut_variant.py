"""Regenerate scratch native LUT tile netlists; real SPI UART test, no routing.

The copied macro physical views are deliberately not qualified for these new
netlists. This is a functional mapping experiment only, never a chip promotion.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
details = json.loads((ROOT / "build/cloud_input/materialized.json").read_text())
original = Path(details["native_work"])
variant = ROOT / "build/lut_mux_variant"
shutil.copytree(original, variant)
# Relocate copied experiment paths; original authenticated inputs remain intact.
for path in variant.rglob("*"):
    if path.is_file() and path.suffix in (".v", ".json", ".tcl", ".ys", ".csv", ".yaml", ".lef", ".sdc"):
        text = path.read_text()
        if str(original) in text:
            path.write_text(text.replace(str(original), str(variant)))
out = ROOT / "build/lut_variant_evidence"
out.mkdir(exist_ok=False)
library = variant / "fabulous-tiles"
gold = library / "primitives/FABULOUS_LC/fabulous/FABULOUS_LC.v"
text, count = re.subn(r"LUTK\s*#\(\s*\.K\s*\(4\)\s*\)\s*LUT4\s*\(",
                     "wp_lut4_mux_tree LUT4 (", gold.read_text())
if count != 1:
    raise ValueError("Pinned primitive does not have exactly one expected LUT4 instance")
patched = out / "FABULOUS_LC_mux_tree.v"
patched.write_text(text)
latch_map = out / "latch_map.v"
latch_map.write_text(r'''module \$_DLATCH_P_ (input E, D, output Q);
sg13cmos5l_dlhq_1 impl (.D(D), .GATE(E), .Q(Q));
endmodule
module \$_DLATCH_N_ (input E, D, output Q);
sg13cmos5l_dlhq_1 impl (.D(D), .GATE(~E), .Q(Q));
endmodule
''')
lib = Path(os.environ["PDK_ROOT"]) / "ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_slow_1p08V_125C.lib"
candidate = ROOT / "spikes/lut_mapping/wp_lut4_mux_tree.v"
common = [library / "models_pack.v", patched, candidate]
for primitive in ("GBUF", "SYS_RESET"):
    common.append(library / f"primitives/{primitive}/fabulous/{primitive}.v")
records = []
for tile in sorted((library / "tiles/tiny").glob("LUT4x8_ha*")):
    native = tile / f"macro/ihp-sg13cmos5l/nl/{tile.name}.nl.v"
    if not native.is_file():
        continue
    previous = hashlib.sha256(native.read_bytes()).hexdigest()
    sources = common + sorted(tile.glob("*.v"))
    script = "\n".join([
        f"read_liberty -lib -ignore_miss_func {lib}",
        "read_verilog " + " ".join(map(str, sources)),
        f"hierarchy -check -top {tile.name}",
        f"synth -top {tile.name} -flatten -noabc",
        f"techmap -map {latch_map}", f"dfflibmap -liberty {lib}",
        f"abc -liberty {lib}", "clean", "check -assert",
        f"stat -liberty {lib}", f"write_verilog -noattr -noexpr {native}",
    ]) + "\n"
    path = out / f"{tile.name}.ys"
    path.write_text(script)
    with (out / f"{tile.name}.log").open("w") as log:
        subprocess.run(["yosys", "-Q", "-T", "-s", str(path)],
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
    records.append({"tile": tile.name, "original_sha256": previous,
                    "variant_sha256": hashlib.sha256(native.read_bytes()).hexdigest()})
if not records:
    raise RuntimeError("No native LUT tiles regenerated")
(out / "manifest.json").write_text(json.dumps({
    "scope": "regenerated_native_netlist_functional_only_no_physical_or_timing_qualification",
    "configuration_tied_to_constants": False, "original_inputs_edited": False,
    "tiles": records,
}, indent=2) + "\n")
base = [sys.executable, str(ROOT / "spikes/compact_edges/simulate.py"), "--work", str(variant),
        "--words", details["words"], "--chip-dir", "chip_shared_crc_cfgbranches"]
results = {}
for name, extra in (("rtl_control", []), ("native_candidate", ["--mapped-fabric"])):
    with (out / f"{name}.log").open("w") as log:
        result = subprocess.run(base + extra, stdout=log, stderr=subprocess.STDOUT, timeout=300)
    results[name] = result.returncode
    if result.returncode:
        break
(out / "result.json").write_text(json.dumps(results) + "\n")
for sim in variant.glob("simulation_chip_*"):
    dest = out / sim.name
    dest.mkdir()
    for name in ("results.xml", "test.log", "build.log"):
        if (sim / name).is_file():
            shutil.copyfile(sim / name, dest / name)
raise SystemExit(next((code for code in results.values() if code), 0))
