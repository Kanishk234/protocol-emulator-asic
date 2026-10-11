"""Prepare conditional internal C2 timing constraints and a complete review bundle.

Never runs an EDA tool. The stationary loaded-image premise is a diagnostic
condition, not a proved universal hardware property or timing qualification.
"""
import argparse
import json
from pathlib import Path
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
# Candidate command bundle. Verify exact pinned command/help coverage before use.
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
    # report_arrival availability/signature must be verified in the pinned runner.
    puts "WARP_EXPECTED_USER_CLOCK [get_full_name $pin]"
    report_arrival $pin
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
                "boundary": "C2 N_GBUF_END[3]; upstream fabric/shell clock latency and skew excluded",
                "io_delays_added": False, "false_paths_added": False, "user_state_case_analysis": False,
                "original_sdc_modified_or_sourced": False, "configuration_gate_pins_case_analyzed": False,
                "loop_cuts_requested": False,
                "before_execution": ["Verify exact pinned OpenSTA command signatures and report_arrival clock coverage",
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-evidence", type=Path, required=True)
    parser.add_argument("--physical-evidence", type=Path, required=True)
    parser.add_argument("--words", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.native_evidence, args.physical_evidence, args.words, args.out)
    print(json.dumps({"prepared": True, "sta_executed": False, "acceptance": False,
                      "cases": len(result["cases"])}))
