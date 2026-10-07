"""D-049 same-wire diagnostic; never save or qualify a modified physical DB."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
source_run = int(os.environ.get("WARP_SLEW_SOURCE_RUN", "37552604692"))
if source_run == 37674839060:
    evidence = ROOT / "build/slew_source"
    accepted = json.loads((evidence / "result.json").read_text())
    for key in ("verified_native_markers", "fresh_magic_errors",
                "klayout__drc_error__count", "design__lvs_error__count", "flow_returncode"):
        if accepted.get(key) != 0:
            raise RuntimeError(f"Fresh source missing physical acceptance: {key}")
    if accepted.get("native_checked_odb_sha256") != "9cac79d86dd15707efdd385c32d3990347cb4695874bc802d0bfe20a5e90e9ba":
        raise RuntimeError("Unexpected recovered native source identity")
    source = evidence / "fresh_streamout"
    source_markers = 0
elif source_run == 37552604692:
    source = ROOT / "build/slew_source/run"
    source_markers = 3
else:
    raise RuntimeError("Unqualified slew source")
out = ROOT / "build/slew_screen"
out.mkdir(exist_ok=False)


def unique(pattern):
    found = list(source.glob(pattern))
    if len(found) != 1:
        raise RuntimeError(f"Expected unique input {pattern}: {found}")
    return found[0]


inputs = {
    "ODB": unique("*-odb-cellfrequencytables/tt_um_warp.odb"),
    "SDC": unique("*-openroad-fillinsertion/tt_um_warp.sdc"),
    "SPEF": unique("*-openroad-rcx/nom/tt_um_warp.nom.spef"),
}
if source_run == 37674839060 and hashlib.sha256(inputs["ODB"].read_bytes()).hexdigest() != "02b8bd30f3fb12e4a66e2322b5f3906c236dd93eed8b8cd1eeeff95f6e796a61":
    raise RuntimeError("Fresh extracted ODB identity mismatch")
pdk = Path(os.environ["PDK_ROOT"]) / "ihp-sg13cmos5l/libs.ref"
inputs["STD_LIB"] = pdk / "sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_slow_1p08V_125C.lib"
inputs["IO_LIB"] = pdk / "sg13cmos5l_io/lib/sg13cmos5l_io_slow_1p08V_3p0V_125C.lib"
manifest = {key: {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for key, path in inputs.items()}
(out / "inputs.json").write_text(json.dumps(manifest, indent=2) + "\n")
command = ["docker", "run", "--rm", "-v", f"{ROOT}:{ROOT}", "-w", str(ROOT)]
for key, path in inputs.items():
    command += ["-e", f"WARP_SCREEN_{key}={path}"]
command += ["-e", f"WARP_SCREEN_OUT={out}",
    "ghcr.io/librelane/librelane@sha256:d109140b8f17fc54f4fca998beb8124f4949404ec52e339eebd2250854a18b5a",
    "openroad", "-exit", "test_internal/slew_screen.tcl"]
with (out / "openroad.log").open("w") as log:
    subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=300)


def violations(path):
    groups = {}
    group = None
    for line in path.read_text().splitlines():
        if line.strip() in ("max slew", "max fanout", "max capacitance"):
            group = line.strip()
            groups.setdefault(group, [])
        if group and "(VIOLATED)" in line:
            fields = line.split()
            groups[group].append({"pin": fields[0], "limit": float(fields[1]),
                "actual": float(fields[2]), "slack": float(fields[3])})
    return groups


baseline = violations(out / "baseline_checks.rpt")
candidate = violations(out / "candidate_checks.rpt")
expected = {"u_cfg._54_/Y", "ANTENNA_29/A"} | {
    f"u_cfg.g_col[{column}].u_col.WARP_CFG_BRANCH_0/A" for column in range(7)}
if {item["pin"] for item in baseline.get("max slew", [])} != expected:
    raise RuntimeError("Baseline did not reproduce the measured nine-pin hotspot")
(out / "result.json").write_text(json.dumps({
    "source_run": source_run, "source_routing_markers": source_markers,
    "scope": "same_old_wire_parasitics_slow_corner_shell_diagnostic_only",
    "macro_black_boxed": True, "physical_views_modified_or_saved": False,
    "configuration_forced": False, "baseline": baseline, "candidate": candidate,
    "candidate_fewer_slew_violations": len(candidate.get("max slew", [])) < len(expected),
}, indent=2) + "\n")
