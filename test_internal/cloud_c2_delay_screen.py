"""Liberty-only baseline/delay screen; no physical ECO or extracted timing claim.

Add one identity delay cell at each of eight user D pins in a copied mapped
netlist. Both variants omit parasitics. Frozen RTL, views and bitstream stay
unchanged. Preparation executes no EDA; execution is GitHub-only.
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess

from cloud_native_stage import sha

MASTER = "sg13cmos5l_dlygate4sd1_1"
PREFIX = "wp_diag_hold_delay_"
REFERENCE_SHA = "c60dd4177a3fe5891d35bac1146aec31a70f733c4b75cf71c36c26d4bb9ca7a6"


def delay_copy(source, expected_instances):
    if PREFIX in source or source.count("endmodule") != 1:
        raise ValueError("Unexpected source module or diagnostic identifier collision")
    pattern = re.compile(r"sg13cmos5l_dfrbpq_1\s+(\w+)\s*\((.*?)\);", re.S)
    cells = list(pattern.finditer(source))
    if len(cells) != 8 or {m[1] for m in cells} != set(expected_instances):
        raise ValueError("Exactly eight authenticated user registers required")
    substitutions, additions, inventory = [], [], []
    for index, cell in enumerate(cells):
        data = re.findall(r"\.D\s*\(\s*(\w+)\s*\)", cell[2])
        if len(data) != 1:
            raise ValueError("Unexpected original D connection")
        wire = PREFIX + "d" + str(index)
        changed = re.sub(r"\.D\s*\(\s*\w+\s*\)", ".D(" + wire + ")", cell[0], count=1)
        substitutions.append((cell[0], changed))
        additions += [" wire " + wire + ";", f" {MASTER} {PREFIX}{index} (.A({data[0]}), .X({wire}));"]
        inventory.append({"register": cell[1], "original_d_net": data[0], "new_d_net": wire,
                          "delay_instance": PREFIX + str(index), "master": MASTER})
    candidate = source
    for old, new in substitutions:
        if candidate.count(old) != 1:
            raise ValueError("Nonunique register replacement")
        candidate = candidate.replace(old, new, 1)
    block = "\n".join(additions) + "\n"
    candidate = candidate.replace("endmodule", block + "endmodule", 1)
    restored = candidate.replace(block + "endmodule", "endmodule", 1)
    for old, new in substitutions:
        restored = restored.replace(new, old, 1)
    if restored != source:
        raise ValueError("Identity contraction changes original mapped netlist")
    return candidate, inventory


def timing_summary(text, expected_instances, mode):
    blocks = text.split("Startpoint: ")[1:]
    if not blocks:
        raise ValueError("No native internal paths")
    slacks, violations = [], 0
    for block in blocks:
        endpoint = re.findall(r"^Endpoint: (\S+)\s*$", block, re.M)
        if block.splitlines()[0].strip() not in expected_instances or len(endpoint) != 1 or endpoint[0] not in expected_instances:
            raise ValueError("Unexpected internal path boundary")
        if len(re.findall(r"^Path Type: " + mode + r"\s*$", block, re.M)) != 1:
            raise ValueError("Wrong native path type")
        rows = re.findall(r"^\s*([-+]?\d+\.\d+)\s+slack \((VIOLATED|MET)\)\s*$", block, re.M)
        if len(rows) != 1 or not math.isfinite(float(rows[0][0])):
            raise ValueError("Missing/duplicate/nonfinite native slack")
        value, status = float(rows[0][0]), rows[0][1]
        if (status == "MET" and value < 0) or (status == "VIOLATED" and value > 0):
            raise ValueError("Native slack and status disagree")
        slacks.append(value)
        violations += status == "VIOLATED"
    return {"paths": len(blocks), "worst_slack_ns": min(slacks), "violated_paths": violations}


def execute(bundle, physical, pdk_root, reference):
    import cloud_configured_c2_sta as original
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise ValueError("STA execution is GitHub-only")
    meta = json.loads((bundle / "conditional/preparation.json").read_text())
    audits = json.loads((bundle / "conditional/authenticated_audit.json").read_text())["tile_instance_audits"]
    root = Path(__file__).resolve().parents[1]
    if sha(reference) != REFERENCE_SHA:
        raise ValueError("Wrong actual extracted timing reference")
    native_reference = json.loads(reference.read_text())
    if not native_reference.get("diagnostic_completed") or native_reference.get("acceptance") is not False:
        raise ValueError("Missing authentic conditional timing reference")
    result = {"diagnostic_completed": False, "physical_acceptance": False,
              "configured_timing_acceptance": False, "condition": meta["condition"],
              "parasitics": "omitted for BOTH baseline and candidate; intrinsic Liberty screening only",
              "loop_cuts_added": False, "io_delays_added": False, "cases": {}}
    def save():
        (bundle / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    save()
    reports = original.REPORTS
    spef_line = 'read_spef $::env(WARP_NOMINAL_SPEF)\n'
    if reports.count(spef_line) != 1:
        raise ValueError("Original report SPEF anchor differs")
    reports = reports.replace(spef_line, "# Both variants deliberately omit parasitics.\n", 1)
    original_nl = physical / "last_completed/nl/LUT4x8_ha_C2.nl.v"
    if sha(original_nl) != original.PHYSICAL["nl/LUT4x8_ha_C2.nl.v"]:
        raise ValueError("Original mapped source changed")
    expected_instances = {p["instance"] for p in audits[0]["user_clock_endpoints"]}
    regenerated, _ = delay_copy(original_nl.read_text(), expected_instances)
    if (bundle / "delay_copy.nl.v").read_text() != regenerated:
        raise ValueError("Generated identity delay netlist changed")
    result["baseline_nl_sha256"] = sha(original_nl)
    result["candidate_nl_sha256"] = sha(bundle / "delay_copy.nl.v")
    for variant, netlist in (("baseline", original_nl), ("delay", bundle / "delay_copy.nl.v")):
        for case in meta["cases"]:
            position, corner = case["tile_position"], case["corner"]
            directory = bundle / variant / position / corner
            directory.mkdir(parents=True, exist_ok=False)
            name = variant + "/" + position + "/" + corner
            entry = {"completed": False, "physical_acceptance": False}
            result["cases"][name] = entry
            try:
                libraries = []
                expected = {Path(p).name: digest for p, digest in native_reference["cases"][position + "/" + corner]["liberty_sha256"].items()}
                for source in case["liberty_source_paths"]:
                    marker = "/ihp-sg13cmos5l/"
                    if source.count(marker) != 1:
                        raise ValueError("Unexpected original library source")
                    path = pdk_root / "ihp-sg13cmos5l" / source.split(marker, 1)[1]
                    if sha(path) != expected[path.name]:
                        raise ValueError("Liberty differs from actual extracted timing reference")
                    libraries.append(path)
                entry["liberty_sha256"] = {str(p): sha(p) for p in libraries}
                standard = [p for p in libraries if "stdcell" in p.name]
                if len(standard) != 1:
                    raise ValueError("Missing unique standard-cell library")
                library = standard[0].read_text()
                marker = re.search(r"cell\s*\(\s*" + MASTER + r"\s*\)\s*\{", library)
                if marker is None:
                    raise ValueError("Selected native delay cell absent")
                end, depth = marker.end(), 1
                while depth and end < len(library):
                    depth += (library[end] == "{") - (library[end] == "}")
                    end += 1
                body = library[marker.end():end]
                if depth or not re.match(r'.*?pin\s*\(X\)\s*\{\s*direction\s*:\s*"output";\s*function\s*:\s*"A";', body, re.S):
                    raise ValueError("Selected delay cell lacks native identity output X=A")
                area = re.search(r"\barea\s*:\s*([0-9.]+)\s*;", body)
                if area is None or not math.isfinite(float(area[1])) or float(area[1]) <= 0:
                    raise ValueError("Missing native delay-cell catalogue area")
                entry["delay_cell_library_area_um2"] = float(area[1])
                entry["library_area_is_not_routed_chip_area"] = True
                sdc = bundle / "conditional" / position / "conditional_run.sdc"
                if sha(sdc) != case["sdc_sha256"]:
                    raise ValueError("Prepared loaded-image constraints changed")
                (directory / "reports.tcl").write_text(reports)
                lines = ["read_liberty {%s}" % p for p in libraries]
                lines += ["read_verilog {%s}" % netlist, "link_design LUT4x8_ha_C2",
                    "set ::env(WARP_CONDITIONAL_SDC) {%s}" % sdc,
                    "source {%s}" % (directory / "reports.tcl"), 'puts "WARP_REPORTS_COMPLETE"']
                script = directory / "runner.tcl"
                script.write_text("\n".join(lines) + "\n")
                with (directory / "sta.log").open("w") as log:
                    process = subprocess.run(["docker", "run", "--rm", "-v", f"{root}:{root}",
                        "-w", str(directory), "--entrypoint", "sta", original.IMAGE, "-exit", str(script)],
                        stdout=log, stderr=subprocess.STDOUT, timeout=120)
                text = (directory / "sta.log").read_text()
                entry["returncode"] = process.returncode
                if process.returncode or "WARP_REPORTS_COMPLETE" not in text or re.search(r"^Error:", text, re.M):
                    raise ValueError("Native intrinsic STA command failure")
                tile = next(t for t in audits if "X%dY%d" % tuple(t["tile_position"]) == position)
                entry["actual_clock_arrivals"] = original.clock_coverage(text, [p["clock_pin"] for p in tile["user_clock_endpoints"]])
                instances = {p["instance"] for p in tile["user_clock_endpoints"]}
                entry["internal_paths"] = {mode: timing_summary((directory / ("r2r_" + mode + ".rpt")).read_text(), instances, mode) for mode in ("min", "max")}
                entry["report_sha256"] = {}
                for filename in ("annotation.rpt", "coverage.rpt", "clocks.rpt", "clock_latency.rpt", "r2r_min.rpt", "r2r_max.rpt", "unconstrained.rpt"):
                    path = directory / filename
                    if not path.read_text().strip():
                        raise ValueError("Missing native intrinsic report")
                    entry["report_sha256"][filename] = sha(path)
                entry["completed"] = True
            except (ValueError, OSError, KeyError, subprocess.TimeoutExpired) as exc:
                entry["error"] = str(exc)
            save()
    result["diagnostic_completed"] = len(result["cases"]) == 12 and all(c["completed"] for c in result["cases"].values())
    save()
    return result["diagnostic_completed"]


if __name__ == "__main__":
    import cloud_configured_c2_sta as original
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("native-evidence", "physical-evidence", "words", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--pdk-root", type=Path)
    parser.add_argument("--timing-reference", type=Path)
    parser.add_argument("--execute-cloud", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    original.prepare(args.native_evidence, args.physical_evidence, args.words, args.out / "conditional")
    audits = json.loads((args.out / "conditional/authenticated_audit.json").read_text())["tile_instance_audits"]
    expected = {p["instance"] for p in audits[0]["user_clock_endpoints"]}
    if any({p["instance"] for p in t["user_clock_endpoints"]} != expected for t in audits):
        raise ValueError("Tile user-register inventories differ")
    source = args.physical_evidence / "last_completed/nl/LUT4x8_ha_C2.nl.v"
    candidate, inventory = delay_copy(source.read_text(), expected)
    (args.out / "delay_copy.nl.v").write_text(candidate)
    (args.out / "delay_inventory.json").write_text(json.dumps({"added_cells": inventory, "identity_contraction_exact": True, "source_nl_sha256": sha(source), "candidate_nl_sha256": sha(args.out / "delay_copy.nl.v"), "original_physical_views_modified": False}, indent=2) + "\n")
    print(json.dumps({"prepared": True, "added_identity_delay_cells": 8, "sta_executed": False, "acceptance": False}))
    if args.execute_cloud:
        if args.pdk_root is None or args.timing_reference is None:
            parser.error("Cloud execution needs --pdk-root and --timing-reference")
        raise SystemExit(0 if execute(args.out.resolve(), args.physical_evidence.resolve(), args.pdk_root.resolve(), args.timing_reference.resolve()) else 1)
