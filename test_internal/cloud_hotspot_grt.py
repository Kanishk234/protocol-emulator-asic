"""Authenticated paired native routing of fixed-original and five-move padding.

Diagnostic collection can succeed while native routing fails. No physical or
configured timing acceptance follows. Runs only on standard GitHub runners.
"""
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

import cloud_cfg_fanout as cfg
import cloud_congestion_map as reporting
import cloud_fanout_grt as routing
from cloud_fanout_local_grt import BUFFERED, CORNERS, validate_candidate
from cloud_hotspot_padding import audit_placement

ROOT = routing.ROOT
INPUT = ROOT / "build/hotspot_grt_input"
OUT = ROOT / "build/hotspot_grt"
SOURCE_RUN = 38112272623
RESULT_SHA = "3fa452da2289c65dbb69e77b375e5a687826f751b31d42d1974a733923b2999a"
PADDED = dict(BUFFERED, odb="13e88cf8935be6fe594449d86749e3e78ae38f7aa8b2d34637bb60fa02d8f5a5")


def validate_padding(directory, baseline):
    if routing.sha(directory / "result.json") != RESULT_SHA:
        raise ValueError("Wrong measured padding result")
    result = json.loads((directory / "result.json").read_text())
    if result.get("passed") is not True or result.get("source_run") != 38101405271:
        raise ValueError("Padding source was not accepted by producer guards")
    if result.get("candidate_sha256") != {k: PADDED[k] for k in ("odb", "nl")}:
        raise ValueError("Wrong padded views")
    if cfg.parse_census((directory / "before.tsv").read_text()) != cfg.parse_census((baseline / "after.tsv").read_text()):
        raise ValueError("Padding did not start from exact fixed-original baseline")
    measured = audit_placement((directory / "before.tsv").read_text(),
        (directory / "after.tsv").read_text(), (directory / "geometry_before.tsv").read_text(),
        (directory / "geometry_after.tsv").read_text(), (directory / "selected.txt").read_text().splitlines())
    if json.loads(json.dumps(measured)) != result["placement"] or len(measured["moved_instances"]) != 5:
        raise ValueError("Padding geometry evidence differs")
    for label, expected in (("baseline", BUFFERED), ("padded", PADDED)):
        for corner in CORNERS:
            case = result[label + "_sta_" + corner]
            if case["corner"] != corner or case["odb_sha256"] != expected["odb"] or case["nl_sha256"] != expected["nl"] or case["sdc_sha256"] != expected["sdc"]:
                raise ValueError("Producer STA used different views")
            metrics = case["metrics"]
            for kind in ("max_fanout", "max_slew", "max_cap"):
                if metrics[f"design__{kind}_violation__count__corner:{corner}"] != 0:
                    raise ValueError("Producer has electrical violations")
            for kind in ("setup", "hold"):
                slack = metrics[f"timing__{kind}__ws__corner:{corner}"]
                if not isinstance(slack, (int, float)) or not math.isfinite(slack) or slack <= 0 or metrics[f"timing__{kind}_vio__count__corner:{corner}"] != 0:
                    raise ValueError("Producer lacks positive shell timing")
    return measured


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise ValueError("Native routing is allowed only on the GitHub runner")
    OUT.mkdir(exist_ok=False)
    result = {"diagnostic_completed": False, "physical_acceptance": False,
              "configured_timing_acceptance": False, "underlying_route_passed": False,
              "source_runs": {"baseline": 38101405271, "padded": SOURCE_RUN},
              "padding_result_sha256": RESULT_SHA, "cases": {}}
    def save():
        (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    save()
    baseline, candidate = INPUT / "baseline", INPUT / "padded"
    validate_candidate(baseline)
    result["placement"] = validate_padding(candidate, baseline)
    bundle = candidate / "original_source/fanout_source"
    manifest = json.loads((bundle / "manifest.json").read_text())
    if manifest["source_odb_sdc_nl"] != routing.EXPECTED:
        raise ValueError("Original source manifest differs")
    for name, digest in manifest["files"].items():
        path = (bundle / name).resolve()
        if not path.is_relative_to(bundle.resolve()) or routing.sha(path) != digest:
            raise ValueError("Original source file differs")
    config = routing.transform(json.loads((bundle / "config.json").read_text()),
        lambda s: s.replace("@BUNDLE@", str(bundle)).replace("@PDK@", os.environ["PDK_ROOT"]))
    if config.get("PAD_LIBS") is None:
        config["PAD_LIBS"] = {}
    config["CTS_SINK_CLUSTERING_SIZE"] = 8
    config["meta"] = {"version": 2, "flow": ["OpenROAD.GlobalRouting"]}
    previous = INPUT / "previous/ten_buffers/1-openroad-globalrouting/config.json"
    if routing.sha(previous) != routing.ORIGINAL_ROUTING_CONFIG_SHA:
        raise ValueError("Original actual routing policy differs")
    config, protected = routing.configure_iterations(config, json.loads(previous.read_text()), 50)
    result["original_routing_config_sha256"] = routing.ORIGINAL_ROUTING_CONFIG_SHA
    result["protected_routing_settings"] = protected
    config_path = OUT / "config.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    result["identical_case_config_sha256"] = routing.sha(config_path)
    sdc = baseline / "buffered_sta_nom_typ_1p20V_25C/final/sdc/tt_um_warp.sdc"
    paths = {"baseline": {"odb": baseline / "buffered.odb", "nl": baseline / "buffered.nl.v", "sdc": sdc},
             "padded": {"odb": candidate / "padded.odb", "nl": candidate / "padded.nl.v", "sdc": sdc}}
    observer = OUT / "observe.tcl"
    observer.write_text(routing.CENSUS + '\nread_db $::env(WARP_GRT_ODB)\ncheck_placement -verbose\ncensus $::env(WARP_GRT_CENSUS)\n')
    def observe(label, odb):
        census = OUT / (label + ".tsv")
        with (OUT / (label + "_placement.log")).open("w") as log:
            subprocess.run(["docker", "run", "--rm", "-v", f"{ROOT}:{ROOT}", "-w", str(ROOT),
                "-e", f"WARP_GRT_ODB={odb}", "-e", f"WARP_GRT_CENSUS={census}",
                "--entrypoint", "openroad", routing.IMAGE, "-exit", str(observer)],
                stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
        return census.read_text()
    for label in paths:
        expected = BUFFERED if label == "baseline" else PADDED
        entry = {"route_passed": False, "source_sha256": routing.authenticate_views(paths[label], expected)}
        result["cases"][label] = entry
        save()
        census = observe(label + "_before", paths[label]["odb"])
        expected_census = (candidate / ("before.tsv" if label == "baseline" else "after.tsv")).read_text()
        if cfg.parse_census(census) != cfg.parse_census(expected_census):
            raise ValueError("Native source placement/topology differs")
        state = OUT / (label + "_input_state.json")
        state.write_text(json.dumps({**{k: str(v) for k, v in paths[label].items()}, "metrics": {}}))
        run = OUT / label
        run.mkdir()
        with (OUT / (label + ".log")).open("w") as log:
            process = subprocess.run(["docker", "run", "--rm", "-v", f"{ROOT}:{ROOT}", "-w", str(ROOT),
                "-e", f"PDK_ROOT={os.environ['PDK_ROOT']}", "--entrypoint", "python3", routing.IMAGE,
                str(Path(reporting.__file__).resolve()), "--inside", str(config_path), str(state), str(run)],
                stdout=log, stderr=subprocess.STDOUT, timeout=900)
        stages = list(run.glob("*-openroad-globalrouting"))
        if len(stages) != 1:
            raise ValueError("Missing unique actual GRT stage")
        stage = stages[0]
        raw = (stage / "openroad-globalrouting.log").read_text()
        iterations = re.findall(r"(?m)^\+ global_route -congestion_iterations (\d+)\b", raw)
        if not iterations or any(int(n) != 50 for n in iterations):
            raise ValueError("Actual native routing budget differs")
        congestion = routing.parse_congestion(raw)
        if not congestion:
            raise ValueError("Missing actual native congestion table")
        entry.update({"returncode": process.returncode, "native_congestion": congestion,
                      "overflow": congestion[-1]["total_overflow"], "native_iteration_counts": iterations})
        entry.update(reporting.hotspot_record(stage / "native-congestion.rpt", entry["overflow"]))
        resolved = json.loads((stage / "config.json").read_text())
        if resolved["CELL_LIBS"] != config["LIB"] or cfg.macro_contract(resolved["MACROS"]) != cfg.macro_contract(config["MACROS"]):
            raise ValueError("Actual library/macro changed")
        for key, value in config.items():
            if key.startswith(("GRT_", "RT_")) or key in ("CLOCK_PORT", "CLOCK_PERIOD", "CLOCK_UNCERTAINTY_CONSTRAINT", "CLOCK_TRANSITION_CONSTRAINT", "TIME_DERATING_CONSTRAINT", "CTS_SINK_CLUSTERING_SIZE", "MAX_FANOUT_CONSTRAINT", "PNR_SDC_FILE", "FALLBACK_SDC"):
                if resolved.get(key) != value:
                    raise ValueError("Protected native policy changed: " + key)
        if process.returncode == 0:
            final = json.loads((stage / "state_out.json").read_text())
            routing.require_zero_overflow(congestion, final["metrics"])
            if not (stage / "after_grt.guide").is_file() or not (stage / "after_grt.guide").stat().st_size:
                raise ValueError("Missing actual routing guides")
            if cfg.parse_census(observe(label + "_after", final["odb"])) != cfg.parse_census(census):
                raise ValueError("GRT changed placement/master/topology")
            wirelength = final["metrics"].get("global_route__wirelength")
            if not isinstance(wirelength, (int, float)) or not math.isfinite(wirelength) or wirelength <= 0:
                raise ValueError("Missing native route wirelength")
            entry["global_route_wirelength_um"] = wirelength
            entry["guide_sha256"] = routing.sha(stage / "after_grt.guide")
            entry["final_state_sha256"] = routing.sha(stage / "state_out.json")
            entry["final_odb_sha256"] = routing.sha(Path(final["odb"]))
            entry["native_placement_topology_exact"] = True
            entry["route_passed"] = True
        else:
            entry["native_error"] = "Native GRT rejected this case; retained without acceptance"
        routing.authenticate_views(paths[label], expected)
        entry["source_unchanged"] = True
        entry["native_policy_exact"] = True
        save()
    result["diagnostic_completed"] = len(result["cases"]) == 2
    result["underlying_route_passed"] = all(c["route_passed"] for c in result["cases"].values())
    save()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        path = OUT / "result.json"
        if path.is_file():
            result = json.loads(path.read_text())
            result["diagnostic_completed"] = False
            result["error"] = str(exc)
            path.write_text(json.dumps(result, indent=2) + "\n")
        raise
