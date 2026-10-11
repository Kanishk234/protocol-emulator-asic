"""Prepare conditional internal C2 timing constraints and a complete review bundle.

Preparation runs no EDA. Explicit --execute-cloud runs STA only on GitHub.
The stationary loaded-image premise is a diagnostic condition, not a proved
universal hardware property or timing qualification.
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile

from cloud_configured_c2_timing import prepare as audit_inputs
from cloud_native_stage import sha

PHYSICAL = {
    "odb/LUT4x8_ha_C2.odb": "ed22fd1da8caa0fc3386c85183110c3bcecca641192c80171f91f96a183720c9",
    "lef/LUT4x8_ha_C2.lef": "441d0cf09999fc829376edd8454d6b4a6cb818508c9de273f3b8a3e3e7e510ce",
    "gds/LUT4x8_ha_C2.gds": "7423dd5050b904871f6c5ad2950c4b2a9e808b943062f7880342eea699e189e0",
    "nl/LUT4x8_ha_C2.nl.v": "13cac0eabdbdcaf000b1e57c521fc9d417aac957be18a68c5808f8c920529e7c",
    "spef/nom/LUT4x8_ha_C2.nom.spef": "5609f144dcaea549cf581625fe2683fb658ae2f0ad37f23b7e1157a79bf6ab96",
    "sdc/LUT4x8_ha_C2.sdc": "998ef55d4735237bfc170f8c80893aee388840da835199d95253f5baf9d1b32e",
}
CORNERS = ("nom_fast_1p32V_m40C", "nom_slow_1p08V_125C", "nom_typ_1p20V_25C")
OPENROAD_COMMIT = "dcf36133a369abc8f3c5e5738cd4d82e4903c0e0"
OPENSTA_COMMIT = "857316ff001b2a8dbbdc5996944d08a6d38c87ab"
COMMAND_SOURCE = {
    "search/Search.tcl": "d4304a4b6b71a407b055145487df8276a565b82810dad59833e86602127c2bc7",
    "sdc/Sdc.tcl": "c7d0e8f56a9953a48d05ac0c5bd559b6711fd0d5314836f38414641015af616a",
    "tcl/Sta.tcl": "63a4351e9715f1f5d849dd48d80de5fa391c22dcd02a247d56b50bf120e0157e",
    "parasitics/Parasitics.tcl": "954ea72d7ad5b227a4ff2afd0b35ec1999fce0ff81010271e8d75f77b0fa5fe6",
    "graph/Graph.tcl": "e606a3188c56f03f04f93cda3ff8ad1424636e404f400b625dca3a16520d5229",
}
IMAGE = "ghcr.io/librelane/librelane@sha256:d109140b8f17fc54f4fca998beb8124f4949404ec52e339eebd2250854a18b5a"


def validate_inventory(tile):
    cfg, ff = tile["configuration"], tile["user_clock_endpoints"]
    if (len(cfg) != 529 or len({p["q_pin"] for p in cfg}) != 529
            or len(ff) != 8 or len({p["instance"] for p in ff}) != 8):
        raise ValueError("Require exactly 529 unique configuration Q and eight user registers")
    for p in cfg:
        if p["q_pin"] != p["instance"] + "/Q" or p["image_value"] not in (0, 1):
            raise ValueError("Invalid actual configuration binding")
    for p in ff:
        if (p["clock_boundary_port"] != "N_GBUF_END[3]"
                or p["selector_values_s0_s1"] != [1, 1]
                or p["reset_b_tie_high"] is not True
                or p["data_reset_paths_must_remain_dynamic"] is not True):
            raise ValueError("Unexpected real clock/reset control")
        for field, port in (("clock_pin", "CLK"), ("d_pin", "D"), ("q_pin", "Q"), ("reset_b_pin", "RESET_B")):
            if p[field] != p["instance"] + "/" + port:
                raise ValueError("User pin inventory differs")
    if {p["q_pin"] for p in cfg} & {p["q_pin"] for p in ff}:
        raise ValueError("Configuration case analysis includes user state")


def constraints(tile):
    validate_inventory(tile)
    lines = ["# Conditional stationary loaded image; diagnostic only; no I/O budgets.",
             "proc exact_pin {name} {",
             "    set pins [get_pins $name]",
             '    if {[llength $pins] != 1} {error "Missing/nonunique pin $name"}',
             "    return $pins", "}"]
    for p in tile["configuration"]:
        lines.append(f"set_case_analysis {p['image_value']} [exact_pin {{{p['q_pin']}}}]")
    lines += ["set root {}", "foreach port [get_ports *] {",
              "    if {[get_full_name $port] eq {N_GBUF_END[3]}} {lappend root $port}", "}",
              'if {[llength $root] != 1} {error "Actual selected clock root absent/nonunique"}',
              "create_clock -name WARP_C2_BOUNDARY_CLK -period 20.0 $root",
              "set_clock_uncertainty 0.25 [get_clocks WARP_C2_BOUNDARY_CLK]",
              "set_clock_transition 0.15 [get_clocks WARP_C2_BOUNDARY_CLK]",
              "set_timing_derate -early 0.95", "set_timing_derate -late 1.05",
              "set_propagated_clock [get_clocks WARP_C2_BOUNDARY_CLK]",
              "set user_q {}; set user_d {}; set user_clk {}; set user_reset {}"]
    for p in tile["user_clock_endpoints"]:
        for variable, field in (("user_q", "q_pin"), ("user_d", "d_pin"),
                                ("user_clk", "clock_pin"), ("user_reset", "reset_b_pin")):
            lines.append(f"lappend {variable} {{*}}[exact_pin {{{p[field]}}}]")
    lines += ['if {[llength $user_clk] != 8} {error "Eight user clock pins required"}']
    return "\n".join(lines) + "\n"


REPORTS = r'''
# Commands verified against the exact pinned OpenSTA source; runtime availability checked too.
# Do not source the original virtual-clock SDC or impose I/O timing budgets.
source $::env(WARP_CONDITIONAL_SDC)
read_spef $::env(WARP_NOMINAL_SPEF)
report_parasitic_annotation -report_unannotated > annotation.rpt
check_setup -verbose -unconstrained_endpoints -multiple_clock -no_clock -no_input_delay -loops -generated_clocks > coverage.rpt
report_clock_properties > clocks.rpt
report_clock_latency > clock_latency.rpt
report_checks -from $user_q -to $user_d -path_delay max -format full_clock_expanded -group_path_count 64 -endpoint_path_count 8 > r2r_max.rpt
report_checks -from $user_q -to $user_d -path_delay min -format full_clock_expanded -group_path_count 64 -endpoint_path_count 8 > r2r_min.rpt
report_checks -unconstrained -group_path_count 10000 > unconstrained.rpt
foreach pin $user_clk {
    # Preserve actual propagated arrival evidence for each individual CLK.
    puts "WARP_USER_CLOCK_BEGIN [get_full_name $pin]"
    report_arrival $pin
    puts "WARP_USER_CLOCK_END [get_full_name $pin]"
}
# No exit-pass decision: missing coverage, unannotated clock/data nets, loops,
# automatically disabled arcs, or absent constrained R2R paths forbid qualification.
'''


def prepare(native, physical, words, out):
    for relative, expected in PHYSICAL.items():
        if sha(physical / "last_completed" / relative) != expected:
            raise ValueError("Pinned physical view differs: " + relative)
    config_path = physical / "source/original_resolved.json"
    config = json.loads(config_path.read_text())
    expected_settings = {"CLOCK_PERIOD": 20, "CLOCK_UNCERTAINTY_CONSTRAINT": 0.25,
                         "CLOCK_TRANSITION_CONSTRAINT": 0.15, "TIME_DERATING_CONSTRAINT": 5}
    if any(config[key] != value for key, value in expected_settings.items()):
        raise ValueError("Original internal-clock assumptions differ")
    if set(config["STA_CORNERS"]) != set(CORNERS):
        raise ValueError("Original three PVT corners differ")
    with tempfile.TemporaryDirectory(prefix="warp-c2-sta-audit-") as temporary:
        audit_path = Path(temporary) / "audit"
        audit_inputs(native, physical, words, audit_path)
        audit = json.loads((audit_path / "audit.json").read_text())
    out.mkdir(parents=True, exist_ok=False)
    (out / "authenticated_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    bundles = []
    for tile in audit["tile_instance_audits"]:
        validate_inventory(tile)
        position = "X%dY%d" % tuple(tile["tile_position"])
        directory = out / position
        directory.mkdir()
        sdc = directory / "conditional_run.sdc"
        sdc.write_text(constraints(tile))
        for corner in CORNERS:
            corner_dir = directory / corner
            corner_dir.mkdir()
            # Library selection is retained as explicit source paths, never a glob
            # silently collapsing fast/slow/typ into the first matched library.
            libraries = config["LIB"][corner]
            (corner_dir / "reports.tcl").write_text(REPORTS)
            bundles.append({"tile_position": position, "corner": corner,
                            "liberty_source_paths": libraries, "sdc_sha256": sha(sdc),
                            "reports_sha256": sha(corner_dir / "reports.tcl"),
                            "rc_corner": "nominal extracted SPEF shared across three PVT libraries",
                            "user_clock_pin_count_required": 8, "configuration_cases": 529})
    metadata = {"prepared": True, "sta_executed": False, "acceptance": False,
                "condition": "Exact UART image already loaded; configuration Q stationary for the diagnostic interval",
                "universal_RUN_stability_proven": False, "physical_view_sha256": PHYSICAL,
                "image_sha256": audit["image_sha256"], "loaded_result_sha256": audit["loaded_result_sha256"],
                "original_config_sha256": sha(config_path), "original_clock_settings": expected_settings,
                "runner_image": IMAGE, "expected_openroad_commit": OPENROAD_COMMIT, "cases": bundles,
                "expected_opensta_commit": OPENSTA_COMMIT, "verified_command_sources": COMMAND_SOURCE,
                "boundary": "C2 N_GBUF_END[3]; upstream fabric/shell clock latency and skew excluded",
                "io_delays_added": False, "false_paths_added": False, "user_state_case_analysis": False,
                "original_sdc_modified_or_sourced": False, "configuration_gate_pins_case_analyzed": False,
                "loop_cuts_requested": False,
                "before_execution": ["Check runtime command availability and actual report_arrival clock coverage",
                                     "Read each exact PVT Liberty, final NL, link C2, then source generated report bundle",
                                     "Record Liberty hashes and actual tool version in cloud evidence"],
                "qualification_blockers": ["Unproved universal full-load/RUN stability",
                    "Any configured loops or automatically disabled loop arcs", "Any unclocked/multiply-clocked user FF",
                    "Missing eight per-pin clock arrivals or missing full-clock min/max R2R paths",
                    "Unannotated active clock/data SPEF nets", "All I/O remain deliberately unconstrained",
                    "Source hardening still failed virtual-clock timing and electrical fanout gate",
                    "Missing intertile/shell physical clock paths; no full-chip timing claim"]}
    (out / "preparation.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


def clock_coverage(text, expected):
    """Read actual pinned report_arrival rows, never infer clocks from pin existence."""
    starts = list(re.finditer(r"^WARP_USER_CLOCK_BEGIN (\S+)\s*$", text, re.M))
    if len(starts) != 8 or {m[1] for m in starts} != set(expected):
        raise ValueError("Missing/duplicate actual user-clock report")
    coverage = {}
    for match in starts:
        end = re.search(r"^WARP_USER_CLOCK_END " + re.escape(match[1]) + r"\s*$",
                        text[match.end():], re.M)
        if end is None:
            raise ValueError("Truncated user-clock report")
        block = text[match.end():match.end() + end.start()]
        rows = []
        finite_edges = [False, False]
        for line in block.splitlines():
            # Search.tcl uses rf_short_name: '^' or 'v'. Graph.tcl's
            # format_delays joins exact native delay tokens with colons.
            found = re.fullmatch(r"\s*\(WARP_C2_BOUNDARY_CLK\s+[\^v]\)\s+r\s+(\S+)\s+f\s+(\S+)\s*", line)
            if found:
                finite = []
                for side in found.groups():
                    tokens = side.split(":")
                    values = []
                    for token in tokens:
                        if token in ("INF", "-INF"):
                            values.append(False)
                        elif re.fullmatch(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?", token):
                            if not math.isfinite(float(token)):
                                raise ValueError("Nonfinite numeric clock delay")
                            values.append(True)
                        else:
                            raise ValueError("Malformed native clock delay token: " + token)
                    finite.append(all(values))
                # A rise-referenced clock row legitimately has an INF fall
                # arrival, and vice versa. Require both pin edges across rows.
                finite_edges = [old or new for old, new in zip(finite_edges, finite)]
                if any(finite):
                    rows.append(line.strip())
            elif "(WARP_C2_BOUNDARY_CLK" in line:
                raise ValueError("Malformed native clock-arrival row")
        if not rows or not all(finite_edges):
            raise ValueError("No finite actual selected-clock arrival at " + match[1])
        other = re.findall(r"\(([^\s()]+)\s+[^)]+\)\s+r\s", block)
        if any(clock != "WARP_C2_BOUNDARY_CLK" for clock in other):
            raise ValueError("Unexpected additional clock at " + match[1])
        coverage[match[1]] = rows
    return coverage


def test_clock_coverage_parser():
    """Lightweight boundary fixtures for pinned native report serialization."""
    pins = [f"user{i}/CLK" for i in range(8)]
    good = "\n".join(f"WARP_USER_CLOCK_BEGIN {pin}\n"
        " (WARP_C2_BOUNDARY_CLK ^) r 0.123:0.245 f INF:INF\n"
        " (WARP_C2_BOUNDARY_CLK v) r -INF:INF f 10.334:10.446\n"
        f"WARP_USER_CLOCK_END {pin}" for pin in pins)
    assert len(clock_coverage(good, pins)) == 8
    bad_cases = [good.replace("0.123:0.245", token) for token in
                 ("INF123", "0.123junk", "0.123::0.245", "0.123 0.245", "NaN", "1e999", "INF:INF")]
    bad_cases += [good.replace("10.334:10.446", "INF:INF"),
                  good.replace("WARP_C2_BOUNDARY_CLK ^", "WARP_C2_BOUNDARY_CLK R"),
                  good.replace("WARP_C2_BOUNDARY_CLK", "wrong_clock"),
                  good.replace(pins[0], pins[1]), good[:good.rfind("WARP_USER_CLOCK_END")]]
    for bad in bad_cases:
        try:
            clock_coverage(bad, pins)
        except ValueError:
            pass
        else:
            raise AssertionError("Malformed/missing actual clock coverage accepted")


def execute_cloud(bundle, physical, pdk_root):
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise ValueError("STA execution is allowed only on the GitHub runner")
    metadata = json.loads((bundle / "preparation.json").read_text())
    audits = json.loads((bundle / "authenticated_audit.json").read_text())["tile_instance_audits"]
    result = {"diagnostic_completed": False, "acceptance": False, "timing_pass_claimed": False,
              "condition": metadata["condition"], "cases": {}, "expected_opensta_commit": OPENSTA_COMMIT,
              "runner_image": IMAGE, "configured_loops_or_disabled_arcs_forbid_qualification": True}
    for case in metadata["cases"]:
        position, corner = case["tile_position"], case["corner"]
        directory = bundle / position / corner
        evidence = {"completed": False, "corner": corner, "acceptance": False}
        result["cases"][position + "/" + corner] = evidence
        try:
            libraries = []
            for source in case["liberty_source_paths"]:
                marker = "/ihp-sg13cmos5l/"
                if source.count(marker) != 1:
                    raise ValueError("Unrecognized original Liberty source path")
                path = pdk_root / "ihp-sg13cmos5l" / source.split(marker, 1)[1]
                libraries.append(path)
            evidence["liberty_sha256"] = {str(p): sha(p) for p in libraries}
            top = physical / "last_completed/nl/LUT4x8_ha_C2.nl.v"
            spef = physical / "last_completed/spef/nom/LUT4x8_ha_C2.nom.spef"
            for relative, expected in PHYSICAL.items():
                if sha(physical / "last_completed" / relative) != expected:
                    raise ValueError("Physical view changed before execution")
            commands = ["read_liberty", "read_verilog", "link_design", "read_spef", "get_pins",
                        "get_ports", "get_full_name", "set_case_analysis", "create_clock", "set_propagated_clock",
                        "report_arrival", "report_clock_properties", "report_clock_latency", "report_checks",
                        "report_parasitic_annotation", "check_setup"]
            lines = ["foreach command {" + " ".join(commands) + "} {",
                     ' if {![llength [info commands $command]]} {error "Missing native command $command"}',
                     ' puts "WARP_COMMAND_PRESENT $command"', "}"]
            lines += ["read_liberty {%s}" % p for p in libraries]
            lines += ["read_verilog {%s}" % top, "link_design LUT4x8_ha_C2",
                      "set ::env(WARP_CONDITIONAL_SDC) {%s}" % (directory.parent / "conditional_run.sdc"),
                      "set ::env(WARP_NOMINAL_SPEF) {%s}" % spef,
                      "source {%s}" % (directory / "reports.tcl"), 'puts "WARP_REPORTS_COMPLETE"']
            script = directory / "runner.tcl"
            script.write_text("\n".join(lines) + "\n")
            root = Path(__file__).resolve().parents[1]
            with (directory / "sta.log").open("w") as log:
                process = subprocess.run(["docker", "run", "--rm", "-v", f"{root}:{root}",
                    "-w", str(directory), "--entrypoint", "sta", IMAGE, "-exit", str(script)],
                    stdout=log, stderr=subprocess.STDOUT, timeout=180)
            evidence["returncode"] = process.returncode
            text = (directory / "sta.log").read_text()
            if (process.returncode or "WARP_REPORTS_COMPLETE" not in text
                    or re.search(r"^Error:", text, re.M)):
                raise ValueError("Native STA command/setup failure")
            tile = next(t for t in audits if "X%dY%d" % tuple(t["tile_position"]) == position)
            evidence["actual_user_clock_arrivals"] = clock_coverage(text, [p["clock_pin"] for p in tile["user_clock_endpoints"]])
            reports = {}
            for name in ("annotation.rpt", "coverage.rpt", "clocks.rpt", "clock_latency.rpt",
                         "r2r_min.rpt", "r2r_max.rpt", "unconstrained.rpt"):
                path = directory / name
                if not path.is_file() or not path.read_text().strip():
                    raise ValueError("Missing native report " + name)
                reports[name] = {"sha256": sha(path), "bytes": path.stat().st_size}
            evidence["reports"] = reports
            evidence["r2r_path_counts"] = {mode: (directory / ("r2r_" + mode + ".rpt")).read_text().count("Startpoint:")
                                           for mode in ("min", "max")}
            evidence["completed"] = True
        except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
            evidence["error"] = str(exc)
        (bundle / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    result["diagnostic_completed"] = all(case["completed"] for case in result["cases"].values())
    (bundle / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result["diagnostic_completed"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-evidence", type=Path, required=True)
    parser.add_argument("--physical-evidence", type=Path, required=True)
    parser.add_argument("--words", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--execute-cloud", action="store_true")
    parser.add_argument("--pdk-root", type=Path)
    args = parser.parse_args()
    result = prepare(args.native_evidence, args.physical_evidence, args.words, args.out)
    print(json.dumps({"prepared": True, "sta_executed": False, "acceptance": False,
                      "cases": len(result["cases"])}))
    if args.execute_cloud:
        if args.pdk_root is None:
            parser.error("--execute-cloud requires --pdk-root")
        raise SystemExit(0 if execute_cloud(args.out.resolve(), args.physical_evidence.resolve(), args.pdk_root.resolve()) else 1)
