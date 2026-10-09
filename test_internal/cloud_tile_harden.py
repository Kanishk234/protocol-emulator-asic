"""Cloud hardening of the exact passing mapped C2; no full-chip promotion.

Replays original tile physical policy with pinned portable I/O/buffer adapters,
bypasses synthesis, and retains strict routing/signoff and extracted STA. The
original CLOCK_PORT=null contract cannot establish configured-fabric timing.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

import cloud_tile_preflight as preflight

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/tile_harden"
INPUT = ROOT / "build/tile_harden_input"
SOURCE = ROOT / "build/arch_explore/tiles_5x3_phase/fabulous-tiles/tiles/tiny/LUT4x8_ha_C2/runs/RUN_2026-09-29_17-38-37"
PLUGIN = Path("/nix/store/d1l0dv6k4hn42rf4czqyvqlaiam4xchm-python3-3.13.9-env/lib/python3.13/site-packages/librelane_plugin_fabulous")
IMAGE = preflight.IMAGE
PHYSICAL_GATES = ("route__drc_errors", "design__critical_disconnected_pin__count",
    "antenna__violating__nets", "antenna__violating__pins", "magic__drc_error__count",
    "klayout__drc_error__count", "design__lvs_error__count")
RETAINED_ODB_SHA = "ed22fd1da8caa0fc3386c85183110c3bcecca641192c80171f91f96a183720c9"
RETAINED_METRICS_SHA = "25c02e6f64ca6a336cfd5f802428996e164b15cfa36d2e7c6a0462ed9f59fab9"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def retain_physical(odb, metrics):
    """Read-only cloud census; geometry evidence does not override flow failure."""
    observer = OUT / "observe_pins.tcl"
    # Original post-PDN ODB carries the exact external power rectangles too.
    # Include them in the same native census rather than trusting policy alone.
    observer.write_text(preflight.PIN_OBSERVER.replace(
        '    if {[$term getSigType] in {POWER GROUND}} {continue}',
        '    if {[$term getSigType] in {POWER GROUND}} {puts "WARP_POWER\\t[$term getName]\\t[$term getSigType]"}'))
    def census(label, path):
        log = OUT / f"{label}_signal_pins.log"
        with log.open("w") as stream:
            subprocess.run(["openroad", "-exit", str(observer)],
                env=dict(os.environ, WARP_TILE_PIN_INPUT=str(path)), stdout=stream,
                stderr=subprocess.STDOUT, timeout=60, check=True)
        text = log.read_text()
        inventory = preflight.parse_pin_inventory(text)
        inventory["power_types"] = {fields[1]: fields[2] for line in text.splitlines()
            if (fields := line.split("\t"))[0] == "WARP_POWER"}
        return inventory
    reference = census("reference", INPUT / "original_pins.odb")
    final = census("final", odb)
    signal_count = len(final["pins"]) - len(final["power_types"])
    interfaces_match = final == reference and signal_count == 306 and bool(final["power_types"])
    for label, inventory in (("reference", reference), ("final", final)):
        (OUT / f"{label}_pin_inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
    gates = {key: metrics.get(key) for key in PHYSICAL_GATES}
    summary = {"physical_gate_metrics": gates,
        "physical_gate_metrics_zero": all(value == 0 for value in gates.values()),
        "original_signal_power_interfaces_match": interfaces_match,
        "signal_ports": signal_count, "power_port_types": final["power_types"],
        "final_odb_sha256": sha(Path(odb)), "metrics": metrics,
        "configured_fabric_timing_acceptance": False, "no_fullchip_promotion": True}
    (OUT / "physical_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def prepare():
    bundle = ROOT / "build/tile_harden_source"
    bundle.mkdir(exist_ok=False)
    config = json.loads((SOURCE / "resolved.json").read_text())
    sources = {"tile-preflight-c2.tar.gz": ROOT / "build/tile-preflight-c2.tar.gz",
        "original_resolved.json": SOURCE / "resolved.json",
        "add_buffers.tcl": PLUGIN / "scripts/add_buffers.tcl",
        "base.sdc": Path(config["FALLBACK_SDC"]), "LICENSE": ROOT / "LICENSE"}
    if sha(sources["tile-preflight-c2.tar.gz"]) != preflight.ARCHIVE_SHA:
        raise RuntimeError("Original authenticated tile preflight archive differs")
    files = {}
    for name, path in sources.items():
        shutil.copyfile(path, bundle / name)
        files[name] = sha(bundle / name)
    (bundle / "ATTRIBUTION.md").write_text(
        "WARP generated source/config: project contributors, Apache-2.0. "
        "Pinned FABulous plugin dcc038217472822330b33f61fadbc06e0c3cc96d "
        "add_buffers.tcl: Efabless Corporation, Apache-2.0; original notice retained. "
        "LibreLane3.0.0 base.sdc: LibreLane/OpenLane contributors, Apache-2.0. "
        "See included LICENSE and nested original preflight attribution. "
        "No PDK is redistributed. Experimental exact C2 hardening, not submission.\n")
    files["ATTRIBUTION.md"] = sha(bundle / "ATTRIBUTION.md")
    (bundle / "manifest.json").write_text(json.dumps({"files": files,
        "original_run": str(SOURCE.relative_to(ROOT)), "passing_nl_sha256": preflight.PASSING_SHA,
        "plugin_commit": "dcc038217472822330b33f61fadbc06e0c3cc96d",
        "preflight_run": 37811985092}, indent=2) + "\n")
    archive = ROOT / "build/tile-harden-c2.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(bundle, arcname="source")
    print(json.dumps({"archive": str(archive), "sha256": sha(archive)}, indent=2))


def inner(config_only=False):
    from librelane.common import Path as LLPath
    from librelane.flows.classic import Classic
    from librelane.state import State, DesignFormat
    from librelane.steps import OpenROAD, Odb

    class TileIO(Odb.CustomIOPlacement):
        id = "Odb.WarpMatchedTileIO"

        def get_script_path(self):
            return str(INPUT / "io_place.py")

    class OutputBuffers(OpenROAD.RepairDesignPostGPL):
        id = "OpenROAD.WarpTileOutputBuffers"

        def get_script_path(self):
            return str(OUT / "source/add_buffers.tcl")

    # Preserve original plugin's physical sequence and output-only buffering.
    # Retain postroute STA and every standard geometry/LVS checker as additional
    # evidence; do not introduce synthesis or timing-driven resizing.
    steps = []
    started = False
    for step in Classic.Steps:
        if step is OpenROAD.Floorplan:
            started = True
        if not started or step.id.startswith(("OpenROAD.Resizer", "OpenROAD.RepairDesign")):
            continue
        if step.id in ("OpenROAD.STAPrePNR", "OpenROAD.STAMidPNR") or step.id.startswith("Yosys."):
            continue
        if step is Odb.CustomIOPlacement:
            step = TileIO
        if step is OpenROAD.GlobalPlacement:
            steps.append(OutputBuffers)
        steps.append(step)

    class MatchedTile(Classic):
        Steps = steps

    original = json.loads((OUT / "source/original_resolved.json").read_text())
    # Replay physical policy, resolving tool/PDK views freshly in 3.1 rather
    # than importing unrelated 3.0 null selectors or workstation paths.
    exact = {key: value for key, value in original.items()
        if key.startswith(("PDN_", "GRT_", "DRT_", "PL_", "IO_PIN_", "DESIGN_REPAIR_", "RUN_", "FP_"))
        and key != "FP_TRACKS_INFO"}
    exact["ROUTING_OBSTRUCTIONS"] = original["ROUTING_OBSTRUCTIONS"]
    for key in ("DESIGN_NAME", "CLOCK_PERIOD", "CLOCK_PORT", "CLOCK_NET", "FP_SIZING",
            "DIE_AREA", "CORE_AREA", "BOTTOM_MARGIN_MULT", "TOP_MARGIN_MULT",
            "LEFT_MARGIN_MULT", "RIGHT_MARGIN_MULT", "VDD_NETS", "GND_NETS",
            "RT_MIN_LAYER", "RT_MAX_LAYER", "PRIMARY_GDSII_STREAMOUT_TOOL",
            "MAX_FANOUT_CONSTRAINT", "CLOCK_UNCERTAINTY_CONSTRAINT", "CLOCK_TRANSITION_CONSTRAINT"):
        exact[key] = original[key]
    exact.update(VERILOG_FILES=[str(INPUT / "passing.nl.v")],
        IO_PIN_ORDER_CFG=str(INPUT / "pins.yaml"), ERRORS_ON_UNMATCHED_IO="both",
        FALLBACK_SDC=str(OUT / "source/base.sdc"), MAGIC_EXT_USE_GDS=True)
    if exact["DIE_AREA"] != [0, 0, 190.08, 196.56] or exact["CLOCK_PORT"] is not None:
        raise RuntimeError("Original tile footprint/clock contract differs")
    if (exact["PDN_VWIDTH"], exact["PDN_VPITCH"], exact["PDN_VOFFSET"],
            exact["PDN_MULTILAYER"], exact["RT_MIN_LAYER"], exact["RT_MAX_LAYER"]) != (
            2.1, 109.92, 80.16, False, "Metal2", "Metal4"):
        raise RuntimeError("Original tile PG/routing policy differs")
    flow = MatchedTile(exact, design_dir=str(INPUT), pdk="ihp-sg13cmos5l", pdk_root=os.environ["PDK_ROOT"])
    required = {"OpenROAD.DetailedRouting", "Checker.TrDRC", "Checker.DisconnectedPins",
        "OpenROAD.RCX", "OpenROAD.STAPostPNR", "Magic.DRC", "Checker.MagicDRC",
        "KLayout.DRC", "Checker.KLayoutDRC", "Netgen.LVS", "Checker.LVS"}
    if not required.issubset({step.id for step in flow.Steps}):
        raise RuntimeError("Pinned flow/PDK lacks required strict tile checks")
    (OUT / "policy.json").write_text(json.dumps({"config": exact,
        "steps": [step.id for step in flow.Steps], "synthesis_executed": False,
        "clock_port_null": True, "configured_fabric_timing_acceptance": False}, indent=2) + "\n")
    if config_only:
        return
    header = OUT / "passing.h.json"
    liberty = Path(os.environ["PDK_ROOT"]) / "ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_slow_1p08V_125C.lib"
    with (OUT / "header.log").open("w") as log:
        subprocess.run(["yosys", "-Q", "-T", "-p",
            f"read_liberty -lib {liberty}; read_verilog {INPUT / 'passing.nl.v'}; hierarchy -check -top {preflight.TOP}; write_json {header}"],
            stdout=log, stderr=subprocess.STDOUT, timeout=120, check=True)
    graph = json.loads(header.read_text())
    graph["modules"] = {preflight.TOP: graph["modules"][preflight.TOP]}
    header.write_text(json.dumps(graph) + "\n")
    provisional = {"physical_checks_pass": False, "passing_nl_sha256": preflight.PASSING_SHA,
        "configured_fabric_timing_acceptance": False, "no_fullchip_promotion": True}
    (OUT / "result.json").write_text(json.dumps(provisional, indent=2) + "\n")
    try:
        state = flow.start(with_initial_state=State({DesignFormat.NETLIST: LLPath(str(INPUT / "passing.nl.v")),
            DesignFormat.JSON_HEADER: LLPath(str(header)), DesignFormat.SDC: LLPath(str(INPUT / "original.sdc"))}),
            _force_run_dir=str(OUT / "run"), tag="matched_c2")
    except Exception as exc:
        provisional["error"] = str(exc)
        # Keep a usable latest checkpoint even if strict downstream geometry
        # fails; each completed stage's original artifacts also remain intact.
        completed_states = sorted((OUT / "run").glob("*/state_out.json"),
            key=lambda path: int(path.parent.name.split("-", 1)[0]))
        if completed_states:
            checkpoint = completed_states[-1]
            retained = State.loads(checkpoint.read_text())
            retained.save_snapshot(OUT / "last_completed")
            provisional["last_completed_state"] = str(checkpoint.relative_to(OUT))
            try:
                provisional["retained_physical_evidence"] = retain_physical(
                    retained[DesignFormat.ODB], retained.metrics.to_raw_dict())
            except Exception as audit_error:
                provisional["physical_retention_error"] = str(audit_error)
        (OUT / "result.json").write_text(json.dumps(provisional, indent=2) + "\n")
        raise
    completed = {step.id for step in flow.step_objects or [] if step.state_out is not None}
    if not required.issubset(completed):
        raise RuntimeError("Required strict physical stages did not complete")
    evidence = retain_physical(state[DesignFormat.ODB], state.metrics.to_raw_dict())
    if not evidence["original_signal_power_interfaces_match"]:
        raise RuntimeError("Hardened signal/power geometry differs from authenticated original")
    for key, value in evidence["physical_gate_metrics"].items():
        if value != 0:
            raise RuntimeError(f"Missing/nonzero strict final tile gate: {key}")
    final_dir = OUT / "final"
    state.save_snapshot(str(final_dir))
    (OUT / "result.json").write_text(json.dumps({**evidence, "physical_checks_pass": True,
        "passing_nl_sha256": preflight.PASSING_SHA, "original_signal_pins_match": True,
        "power_interfaces_match": True}, indent=2) + "\n")


def audit_retained(checkpoint):
    """Cloud-only read of the authenticated failed run; never routes again."""
    odb = checkpoint / "odb" / (preflight.TOP + ".odb")
    metrics = checkpoint / "metrics.json"
    if sha(odb) != RETAINED_ODB_SHA or sha(metrics) != RETAINED_METRICS_SHA:
        raise RuntimeError("Retained C2 checkpoint is not authenticated run37814078650")
    evidence = retain_physical(odb, json.loads(metrics.read_text()))
    (OUT / "result.json").write_text(json.dumps({**evidence,
        "source_run": 37814078650, "audit_only_no_hardening": True,
        "physical_checks_pass": False, "original_strict_flow_failure_retained": True,
        "original_error": "Deferred typical-corner setup gate failed",
        "passing_nl_sha256": preflight.PASSING_SHA}, indent=2) + "\n")
    if not evidence["original_signal_power_interfaces_match"]:
        raise RuntimeError("Retained native interfaces differ from original")


def run(archive, digest, checkpoint=None):
    if sha(archive) != digest:
        raise RuntimeError("Hardening archive authentication failed")
    OUT.mkdir(exist_ok=False)
    with tarfile.open(archive) as tar:
        tar.extractall(OUT, filter="data")
    source = OUT / "source"
    manifest = json.loads((source / "manifest.json").read_text())
    for name, expected in manifest["files"].items():
        path = (source / name).resolve()
        if not path.is_relative_to(source.resolve()) or sha(path) != expected:
            raise RuntimeError(f"Changed/outside authenticated source: {name}")
    preflight.INPUT = INPUT
    preflight.unpack(source / "tile-preflight-c2.tar.gz")
    command = ["docker", "run", "--rm", "-v", f"{ROOT}:{ROOT}", "-w", str(ROOT),
        "-e", "PDK_ROOT=" + os.environ["PDK_ROOT"], IMAGE, "python3",
        "test_internal/cloud_tile_harden.py"]
    command += ["--inside-container"] if checkpoint is None else ["--inside-container-audit", str(checkpoint.resolve())]
    with (OUT / "harden.log").open("w") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
            timeout=6600 if checkpoint is None else 240, check=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["--inside-container"]:
        inner()
    elif len(sys.argv) == 3 and sys.argv[1] == "--inside-container-audit":
        audit_retained(Path(sys.argv[2]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("mode", choices=("prepare", "run", "audit"))
        parser.add_argument("--archive", type=Path)
        parser.add_argument("--sha256")
        parser.add_argument("--checkpoint", type=Path)
        args = parser.parse_args()
        if args.mode == "prepare":
            prepare()
        elif args.archive is None or len(args.sha256 or "") != 64:
            parser.error("run requires --archive and full SHA256")
        elif args.mode == "audit" and args.checkpoint is None:
            parser.error("audit requires --checkpoint (retained last_completed directory)")
        else:
            run(args.archive, args.sha256, args.checkpoint if args.mode == "audit" else None)
