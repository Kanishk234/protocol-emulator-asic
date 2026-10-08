"""Authenticated pre-CTS baseline/cluster8 diagnostic; never detailed routing.

prepare packages ignored source inputs without EDA. run uses pinned hosted
LibreLane only. Neither successful report generation nor estimated STA is
physical/configured-timing acceptance. The original driver/macro stay in use.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "build/arch_explore/compact_edges_tighter/chip_shared_crc_cfgbranches/runs/compact_local_grt/07-openroad-cts"
EXPECTED = {
    "odb": "13edf934051de947fddb8b10aac70ccec2561bd77f06b986185af3e9594a0a1f",
    "sdc": "f8b57e241234f929be55231dc3e51702a1ecd66dca0874b5ea4cfff62a3c8ac9",
    "nl": "e414cc33bdad564547dc2176610bf99027d7b33d10a32bd383d46497720a9326",
}
OUT = ROOT / "build/fanout_preflight"
IMAGE = "ghcr.io/librelane/librelane@sha256:d109140b8f17fc54f4fca998beb8124f4949404ec52e339eebd2250854a18b5a"
OBSERVER = r"""
read_db $::env(WARP_OBSERVE_ODB)
puts "BEGIN_NATIVE_PLACEMENT_CHECK"
check_placement -verbose
puts "END_NATIVE_PLACEMENT_CHECK"
set block [ord::get_db_block]
puts "NET\tname\tsignal_type\tdrivers\tsink_count\tsinks"
foreach net [$block getNets] {
    if {[$net getSigType] in {POWER GROUND}} {continue}
    set drivers {}; set sinks {}
    foreach term [$net getITerms] {
        set pin "[[$term getInst] getName]/[[$term getMTerm] getName]"
        set direction [[$term getMTerm] getIoType]
        if {$direction in {OUTPUT INOUT}} {lappend drivers $pin}
        if {$direction in {INPUT INOUT}} {lappend sinks $pin}
    }
    foreach term [$net getBTerms] {
        set direction [$term getIoType]
        if {$direction in {INPUT INOUT}} {lappend drivers "PORT/[$term getName]"}
        if {$direction in {OUTPUT INOUT}} {lappend sinks "PORT/[$term getName]"}
    }
    puts "NET\t[$net getName]\t[$net getSigType]\t[join $drivers ,]\t[llength $sinks]\t[join $sinks ,]"
}
set fabric [$block findInst u_fabric]
if {$fabric == "NULL"} {error "Missing original fixed fabric"}
puts "MACRO\tu_fabric\t[[$fabric getMaster] getName]\t[$fabric getOrigin]\t[$fabric getOrient]\t[$fabric getPlacementStatus]"
"""


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transform(value, function):
    if isinstance(value, dict):
        return {key: transform(item, function) for key, item in value.items()}
    if isinstance(value, list):
        return [transform(item, function) for item in value]
    return function(value) if isinstance(value, str) else value


def prepare():
    import shutil
    bundle = ROOT / "build/fanout_preflight_source"
    bundle.mkdir(exist_ok=False)
    config = json.loads((SOURCE / "config.json").read_text())
    source_state = json.loads((SOURCE / "state_in.json").read_text())
    files = {}

    def package(value):
        path = Path(value)
        if not path.is_absolute():
            return value
        if value.endswith("/pdk-full"):
            return "@PDK@"
        if "/pdk-full/" in value:
            return "@PDK@/" + value.split("/pdk-full/", 1)[1]
        if path.is_dir() and path.is_relative_to(ROOT):
            target = bundle / "payload" / path.relative_to(ROOT)
            target.mkdir(parents=True, exist_ok=True)
            return "@BUNDLE@/payload/" + str(path.relative_to(ROOT))
        if not path.is_file():
            # Unused source directories and missing optional inputs are left
            # explicit; the cloud config validator must reject required ones.
            return value
        if path.is_relative_to(ROOT):
            relative = path.relative_to(ROOT)
        else:
            # Keep an exact script such as the old base SDC, without requiring
            # a local Nix store to exist on the hosted runner.
            relative = Path("external") / (sha(path) + "_" + path.name)
        target = bundle / "payload" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        files[str(Path("payload") / relative)] = sha(target)
        return "@BUNDLE@/payload/" + str(relative)

    state = {key: source_state[key] for key in EXPECTED}
    for key, expected in EXPECTED.items():
        if sha(Path(state[key])) != expected:
            raise RuntimeError(f"Unexpected original pre-CTS source {key}")
    state["metrics"] = {}
    state = transform(state, package)
    config = transform(config, package)
    # The old per-step meta is not a registered physical flow declaration.
    config["meta"] = {"version": 2, "flow": ["OpenROAD.CTS",
        "OpenROAD.ResizerTimingPostCTS", "OpenROAD.STAMidPNR"]}
    for name, value in (("state.json", state), ("config.json", config)):
        (bundle / name).write_text(json.dumps(value, indent=2) + "\n")
        files[name] = sha(bundle / name)
    shutil.copyfile(ROOT / "LICENSE", bundle / "LICENSE")
    (bundle / "ATTRIBUTION.md").write_text(
        "# Diagnostic source attribution\n\n"
        "WARP generated netlists, macro GDS/LEF and states: protocol-emulator-asic "
        "contributors, Apache-2.0 (included LICENSE). These are experimental "
        "physical diagnostics, not accepted submission views.\n\n"
        "The exact external base.sdc is from LibreLane 3.0.0, adapted from "
        "OpenLane, Apache-2.0 (included LICENSE). Source: "
        "https://github.com/librelane/librelane/tree/3.0.0/librelane/scripts "
        "Its SHA256 is cc63d204b0edfb975b62f9b70066e3b19b322b18c539ce339f28f064ce30229b.\n"
        "No PDK library is bundled; hosted validation fetches IHP-Open-PDK "
        "2bbec755dc67ca3db0261c3d6163e15735d66710 under its upstream licenses.\n")
    for name in ("LICENSE", "ATTRIBUTION.md"):
        files[name] = sha(bundle / name)
    manifest = {"source_stage": str(SOURCE.relative_to(ROOT)),
        "source_odb_sdc_nl": EXPECTED, "files": files,
        "source_state_sha256": sha(SOURCE / "state_in.json"),
        "source_config_sha256": sha(SOURCE / "config.json"),
        "scope": "original_preCTS_not_driver_ECO_no_postroute_acceptance"}
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    archive = ROOT / "build/fanout-preflight-source.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(bundle, arcname="fanout_source")
    print(json.dumps({"archive": str(archive), "sha256": sha(archive),
        "manifest": str(bundle / "manifest.json"), "files": len(files)}, indent=2))


def parse_fanout(path):
    text = path.read_text()
    section = text.split("max fanout", 1)
    if len(section) != 2:
        # Empty violator sections are omitted by STA. Keep raw reports.
        return []
    rows = []
    for line in section[1].splitlines():
        match = re.match(r"^(\S+)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+\(VIOLATED\)", line)
        if match:
            rows.append({"pin": match[1], "limit": float(match[2]),
                "fanout": float(match[3]), "slack": float(match[4])})
    return rows


def run(archive, expected):
    if sha(archive) != expected:
        raise RuntimeError("Source archive hash mismatch")
    OUT.mkdir(exist_ok=False)
    with tarfile.open(archive) as tar:
        tar.extractall(OUT, filter="data")
    bundle = OUT / "fanout_source"
    manifest = json.loads((bundle / "manifest.json").read_text())
    if manifest["source_odb_sdc_nl"] != EXPECTED:
        raise RuntimeError("Bundle is not the audited original pre-CTS source")
    for path, expected_hash in manifest["files"].items():
        resolved = (bundle / path).resolve()
        if not resolved.is_relative_to(bundle.resolve()) or sha(resolved) != expected_hash:
            raise RuntimeError(f"Changed/missing/outside-bundle input {path}")
    replace = lambda text: text.replace("@BUNDLE@", str(bundle)).replace("@PDK@", os.environ["PDK_ROOT"])
    source_state = transform(json.loads((bundle / "state.json").read_text()), replace)
    source_config = transform(json.loads((bundle / "config.json").read_text()), replace)
    # LibreLane 3.0 resolved this unused selector to null. In pinned 3.1.0.dev3
    # PAD_LIBS defaults to {}, and OpenROAD.prepare_env iterates it without a
    # null guard. All original stdcell AND IO timing files are already in LIB;
    # preserve them exactly instead of letting a new PDK resolution replace it.
    protected = {key: value for key, value in source_config.items()
        if "LIB" in key or "CLOCK" in key or "SDC" in key or key == "MACROS"}
    compatibility = []
    if source_config.get("PAD_LIBS") is None:
        source_config["PAD_LIBS"] = {}
        compatibility.append({"key": "PAD_LIBS", "before": None, "after": {},
            "reason": "Match pinned3.1 default empty corner-selector; original LIB unchanged"})
    protected_after = {key: value for key, value in source_config.items()
        if "LIB" in key or "CLOCK" in key or "SDC" in key or key == "MACROS"}
    if any(protected_after[key] != value for key, value in protected.items()
            if key != "PAD_LIBS"):
        raise RuntimeError("Compatibility normalization changed real timing inputs")
    timing_inputs = []
    for corner, paths in source_config["LIB"].items():
        for path in paths:
            timing_inputs.append({"corner": corner, "path": path, "sha256": sha(Path(path))})
    (OUT / "compatibility.json").write_text(json.dumps({"normalizations": compatibility,
        "original_liberty_files": timing_inputs, "protected_input_keys": sorted(protected),
        "other_library_macro_clock_sdc_values_unchanged": True}, indent=2) + "\n")
    if source_config["CLOCK_PERIOD"] != 20 or source_config["CLOCK_PORT"] != "clk":
        raise RuntimeError("Clock contract differs")
    if source_config["CTS_SINK_CLUSTERING_SIZE"] is not None:
        raise RuntimeError("Baseline unexpectedly has an explicit cluster size")
    input_state = OUT / "initial_state.json"
    input_state.write_text(json.dumps(source_state) + "\n")
    results = {}
    observer = OUT / "observe.tcl"
    observer.write_text(OBSERVER)
    def observe(label, odb):
        command = ["docker", "run", "--rm", "-v", f"{ROOT}:{ROOT}",
            "-w", str(ROOT), "-e", f"WARP_OBSERVE_ODB={odb}",
            "--entrypoint", "openroad", IMAGE, "-exit", str(observer)]
        with (OUT / f"{label}_placement_loads.log").open("w") as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                timeout=120, check=True)
        evidence = (OUT / f"{label}_placement_loads.log").read_text()
        macros = [line for line in evidence.splitlines() if line.startswith("MACRO\t")]
        if len(macros) != 1:
            raise RuntimeError("Missing unique fabric placement census")
        if label != "source" and macros != source_macro:
            raise RuntimeError("Preflight moved or replaced the fixed macro")
        return macros
    source_macro = observe("source", source_state["odb"])
    for label, size in (("baseline", None), ("cluster8", 8)):
        config = dict(source_config, CTS_SINK_CLUSTERING_SIZE=size)
        if {key for key in source_config if source_config[key] != config[key]} != (
                {"CTS_SINK_CLUSTERING_SIZE"} if size is not None else set()):
            raise RuntimeError("Unexpected experiment config difference")
        config_path = OUT / f"{label}.json"
        config_path.write_text(json.dumps(config, indent=2) + "\n")
        run_dir = OUT / label
        run_dir.mkdir()
        command = [sys.executable, "-m", "librelane", "--docker-no-tty", "--dockerized",
            "--pdk", "ihp-sg13cmos5l", "--pdk-root", os.environ["PDK_ROOT"], "--manual-pdk",
            "--hide-progress-bar", "--force-run-dir", str(run_dir),
            "--with-initial-state", str(input_state), str(config_path)]
        with (OUT / f"{label}.log").open("w") as log:
            try:
                code = subprocess.run(command, cwd=ROOT, stdout=log,
                    stderr=subprocess.STDOUT, timeout=900).returncode
            except subprocess.TimeoutExpired:
                code = "timeout"
        final_states = sorted(run_dir.glob("*-openroad-stamidpnr/state_out.json"))
        if code == 0:
            resolved_configs = list(run_dir.glob("*-openroad-cts/config.json"))
            if len(resolved_configs) != 1:
                raise RuntimeError("Missing unique resolved CTS configuration")
            resolved = json.loads(resolved_configs[0].read_text())
            # LIB is the documented deprecated name of 3.1 CELL_LIBS. Check
            # the actual step configuration, not only our input JSON.
            if resolved.get("CELL_LIBS") != source_config["LIB"]:
                raise RuntimeError("Resolved CTS changed original Liberty corner maps")
            for key in ("MACROS", "CLOCK_PORT", "CLOCK_PERIOD",
                    "CLOCK_UNCERTAINTY_CONSTRAINT", "CLOCK_TRANSITION_CONSTRAINT",
                    "FALLBACK_SDC", "PNR_SDC_FILE", "MAX_FANOUT_CONSTRAINT"):
                if resolved.get(key) != source_config.get(key):
                    raise RuntimeError(f"Resolved CTS changed protected input {key}")
        reports = list(run_dir.rglob("checks.rpt"))
        result = {"returncode": code, "cluster_size": size,
            "reports": [{"path": str(path.relative_to(OUT)), "fanout": parse_fanout(path)}
                for path in reports], "physical_or_configured_timing_acceptance": False}
        if code == 0 and len(final_states) != 1:
            raise RuntimeError("Missing unique completed post-CTS estimated STA state")
        if final_states:
            final_state = json.loads(final_states[0].read_text())
            result["metrics"] = final_state["metrics"]
            if code == 0:
                observe(label, final_state["odb"])
            # STA uses actual connected loads, including CTS dummy loads, and
            # placement-estimated RC. Retain its corner counts rather than
            # interpreting an omitted report section as proof of no errors.
            metric = result["metrics"]
            needed = ("design__max_fanout_violation__count__corner:",
                "design__max_slew_violation__count__corner:",
                "design__max_cap_violation__count__corner:",
                "clock__skew__worst_hold__corner:",
                "clock__skew__worst_setup__corner:")
            if code == 0 and (not reports or any(not any(key.startswith(prefix)
                    for key in metric) for prefix in needed)):
                raise RuntimeError("Missing fanout/load/skew evidence from estimated STA")
            result["fanout_corner_counts"] = {key: value for key, value in metric.items()
                if key.startswith(needed[0])}
            result["actual_fanout_includes_dummy_loads"] = True
        results[label] = result
        (OUT / "result.json").write_text(json.dumps(results, indent=2) + "\n")
        if code != 0:
            raise RuntimeError(f"{label} preflight did not complete: {code}")
    for key, expected_hash in EXPECTED.items():
        if sha(Path(source_state[key])) != expected_hash:
            raise RuntimeError("Source mutated during preflight")
    (OUT / "scope.json").write_text(json.dumps({"source_archive_sha256": expected,
        "only_comparison_change": "CTS_SINK_CLUSTERING_SIZE None to8",
        "original_inputs_unchanged": True, "no_detailed_route": True,
        "no_configured_timing_acceptance": True, "fanout_not_waived": True}) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "run"])
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--sha256")
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    elif args.archive is None or not re.fullmatch(r"[0-9a-f]{64}", args.sha256 or ""):
        parser.error("run requires --archive and full SHA256")
    else:
        run(args.archive, args.sha256)
