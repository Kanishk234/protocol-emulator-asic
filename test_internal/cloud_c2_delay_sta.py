"""Fresh extracted, conditional internal timing of the actual loaded delay tile.

Authenticates its own physical views and real-loaded results; never reuses the
old tile SPEF. Stationary configuration, boundary clock and unconstrained I/O
remain explicit limitations. No full-chip or all-configuration timing claim.
"""
import argparse
import json
from pathlib import Path
import re

import cloud_configured_c2_sta as sta
from cloud_configured_c2_timing import WORDS_SHA, decode_image, audit_configuration_and_clocks
from cloud_c2_delay_loaded import audit_physical, PHYSICAL_RUN
from cloud_native_final_tile import semantic_evidence
from cloud_native_stage import C2, sha, xml_status

LOADED_RUN = 38163199372
# Independently inspected actual XML, configuration/stress logs and source.
LOADED_RESULT_SHA = "97bcb3cec7bbb006bd99c94250618980fa1f5493e6338d5502411dc44cb6abb8"
VIEWS = {
    "odb/LUT4x8_ha_C2.odb": "924f8d4251bbbc07ebdd688122b551896731b28e8f01d7e1b25012653b283748",
    "lef/LUT4x8_ha_C2.lef": "0ea0f1b0edc040cccdb13b2eb4874a17c264eb75ed6c3e7fad7e7fa9d45c6452",
    "gds/LUT4x8_ha_C2.gds": "5c1368d4c083e5c00dbc2de900f0b33a5b3f56b5a93ac43fb661970e701c7569",
    "nl/LUT4x8_ha_C2.nl.v": "a986a0864ab51f09f6157422ba7dff935585b6456e6accc7b64ac8228725e882",
    "spef/nom/LUT4x8_ha_C2.nom.spef": "7343e224529b757b74824836b5491af24f656a1d0bee7a92b1e396ce5b42fcfb",
    "sdc/LUT4x8_ha_C2.sdc": "998ef55d4735237bfc170f8c80893aee388840da835199d95253f5baf9d1b32e",
}


def prepare(native, physical, words, out):
    if not re.fullmatch(r"[0-9a-f]{64}", LOADED_RESULT_SHA):
        raise ValueError("Actual successful loaded result has not been authenticated")
    evidence = audit_physical(physical)
    for name, digest in VIEWS.items():
        if sha(physical / "last_completed" / name) != digest:
            raise ValueError("New physical view differs: " + name)
    result = json.loads((native / "result.json").read_text())
    if (sha(native / "result.json") != LOADED_RESULT_SHA or result["passed"] is not True
            or result["source_final_c2_sha256"] != VIEWS["nl/LUT4x8_ha_C2.nl.v"]
            or result["source_hardening_run"] != str(PHYSICAL_RUN)
            or result["control_run"] != str(LOADED_RUN)
            or result["configuration_tied_to_constants"] is not False
            or result["physical_or_timing_qualified"] is not False
            or sha(native / "source_final_c2.nl.v") != VIEWS["nl/LUT4x8_ha_C2.nl.v"]):
        raise ValueError("Actual loaded candidate provenance differs")
    if sha(words) != WORDS_SHA or WORDS_SHA not in result["simulation_sources"].values():
        raise ValueError("Exact actually loaded image differs")
    for stage in ("passing_original_control", "hardened_final_c2"):
        for case in ("native_loaded", "native_user_reset"):
            directory = native / stage / case
            if not xml_status(directory / "results.xml")["passed"] or not all(
                    semantic_evidence((directory / "test.log").read_text(), case == "native_user_reset").values()):
                raise ValueError("Actual loaded/reset/configuration evidence missing")
    cone = native / "hardened_final_c2/matched_native_cone.json"
    if sha(cone) != result["stages"]["hardened_final_c2"]["matched_cone_sha256"]:
        raise ValueError("Actual candidate graph differs")
    graph = json.loads(cone.read_text())
    if graph["warp_native_input_provenance"][C2]["sha256"] != VIEWS["nl/LUT4x8_ha_C2.nl.v"]:
        raise ValueError("Candidate graph uses different mapped source")
    modules = graph["modules"]
    macros = [module for module in modules.values() if "Tile_X2Y3_" + C2 in module.get("cells", {})]
    if len(macros) != 1:
        raise ValueError("Actual hierarchy is missing/nonunique")
    rows = 1 + max(int(re.match(r"Tile_X\d+Y(\d+)_", name)[1])
                   for name in macros[0]["cells"] if name.startswith("Tile_X"))
    image = decode_image([int(word, 16) for word in words.read_text().split()], rows)
    audits = [audit_configuration_and_clocks(modules[C2], image, 2, y) for y in (1, 3)]
    config = json.loads((physical / "source/original_resolved.json").read_text())
    margins = {"CLOCK_PERIOD": 20, "CLOCK_UNCERTAINTY_CONSTRAINT": 0.25,
               "CLOCK_TRANSITION_CONSTRAINT": 0.15, "TIME_DERATING_CONSTRAINT": 5}
    if any(config[key] != value for key, value in margins.items()) or set(config["STA_CORNERS"]) != set(sta.CORNERS):
        raise ValueError("Original clock margins/corners differ")
    out.mkdir(parents=True, exist_ok=False)
    audit = {"tile_instance_audits": audits, "source_runs": {"physical": PHYSICAL_RUN, "loaded": LOADED_RUN},
             "physical_view_sha256": VIEWS, "loaded_result_sha256": LOADED_RESULT_SHA,
             "image_sha256": WORDS_SHA, "matched_cone_sha256": sha(cone), "physical_input": evidence}
    (out / "authenticated_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    cases = []
    for tile in audits:
        sta.validate_inventory(tile)
        position = "X%dY%d" % tuple(tile["tile_position"])
        directory = out / position
        directory.mkdir()
        sdc = directory / "conditional_run.sdc"
        sdc.write_text(sta.constraints(tile))
        for corner in sta.CORNERS:
            sub = directory / corner
            sub.mkdir()
            (sub / "reports.tcl").write_text(sta.REPORTS)
            cases.append({"tile_position": position, "corner": corner,
                          "liberty_source_paths": config["LIB"][corner], "sdc_sha256": sha(sdc),
                          "reports_sha256": sha(sub / "reports.tcl")})
    preparation = {"condition": "Actual UART image loaded into routed delay candidate; configuration Q assumed stationary",
                   "physical_view_sha256": VIEWS, "cases": cases, "source_runs": audit["source_runs"],
                   "runner_image": sta.IMAGE, "original_clock_margins": margins,
                   "new_candidate_extracted_spef": True, "io_delays_added": False,
                   "false_paths_added": False, "loop_cuts_requested": False,
                   "user_state_case_analyzed": False, "universal_RUN_stability_proven": False,
                   "physical_or_timing_acceptance": False,
                   "excluded": ["loading mode", "I/O timing", "upstream/intertile/shell clock skew", "other tile types", "other programs"]}
    (out / "preparation.json").write_text(json.dumps(preparation, indent=2) + "\n")
    return preparation


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("native", "physical", "words", "out", "pdk-root"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--execute-cloud", action="store_true")
    args = parser.parse_args()
    prepare(args.native, args.physical, args.words, args.out)
    if args.execute_cloud:
        # The existing engine authenticates each exact candidate view before
        # execution. This process-local explicit provenance is not an old-view
        # pass: VIEWS are independently pinned to the new physical experiment.
        sta.PHYSICAL = VIEWS
        if not sta.execute_cloud(args.out, args.physical, args.pdk_root):
            raise SystemExit("One or more actual internal timing diagnostics failed")
