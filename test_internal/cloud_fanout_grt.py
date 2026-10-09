"""Paired authenticated cluster8/ten-buffer GRT screen; no detailed routing.

Pins, instances and placement must stay exact within each routing-only case.
Native congestion evidence is required; this never qualifies chip timing/views.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile

from cloud_fanout_preflight import IMAGE, EXPECTED, sha, transform, macro_contract
from cloud_cfg_fanout import CENSUS, SOURCE_SHA, DERIVED, parse_census, verify_connections

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/fanout_grt"
INPUT = ROOT / "build/fanout_grt_input"
BUFFERED = {"odb": "b5968bc650ffdb24d01639fcc08b4c51ccd6f857ae589bd072ec077e2e246f66",
            "nl": "3e3e9fd0a7632c1669858c99ff968aebcd671550488736f4c51c8d2222722136",
            "sdc": DERIVED["sdc"]}


def parse_congestion(text):
    """Pinned OpenROAD dcf3613 GlobalRouter.cpp reportCongestion table, last report."""
    if "Final congestion report:" not in text: raise ValueError("Missing native final congestion report")
    section = text.rsplit("Final congestion report:", 1)[1]
    rows = []
    pattern = r"^\s*(\S+)\s+(\d+)\s+(\d+)\s+(\d+(?:\.\d+)?)%\s+(\d+)\s*/\s*(\d+)\s*/\s*(\d+)\s*$"
    for line in section.splitlines():
        match = re.match(pattern, line)
        if not match: continue
        row = {"layer": match[1], "resource": int(match[2]), "demand": int(match[3]),
               "usage_percent": float(match[4]), "max_h_overflow": int(match[5]),
               "max_v_overflow": int(match[6]), "total_overflow": int(match[7])}
        rows.append(row)
        if row["layer"] == "Total": break
    if len(rows) < 2 or rows[-1]["layer"] != "Total" or len({r["layer"] for r in rows}) != len(rows):
        raise ValueError("Incomplete/duplicate native congestion rows")
    for field in ("resource", "demand", "max_h_overflow", "max_v_overflow", "total_overflow"):
        if sum(r[field] for r in rows[:-1]) != rows[-1][field]: raise ValueError("Native congestion total inconsistent")
    return rows


def require_zero_overflow(rows, metrics):
    overflow = {key: val for key, val in metrics.items() if "overflow" in key.lower()}
    if any(not isinstance(val, (int, float)) or val != 0 for val in overflow.values()):
        raise ValueError("Nonzero/unsupported actual overflow metric")
    if any(row[field] != 0 for row in rows
           for field in ("max_h_overflow", "max_v_overflow", "total_overflow")):
        raise ValueError("Native final congestion reports nonzero overflow")
    return overflow


def authenticate_views(paths, expected):
    if set(paths) != set(expected): raise ValueError("Incomplete source views")
    actual = {kind: sha(path) for kind, path in paths.items()}
    if actual != expected: raise ValueError("Source view authentication failed")
    return actual


def main():
    OUT.mkdir(exist_ok=False)
    result = {"passed": False, "scope": "paired GRT-only congestion screen",
              "physical_or_timing_acceptance": False, "configured_timing_acceptance": False,
              "detailed_routing": False, "driver_resize": False, "stages": {},
              "source_runs": {"cluster8": 37811985079, "ten_buffers": 37956470190}}
    def save(): (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    save()
    try:
        archive = ROOT / "build/fanout-preflight-source.tar.gz"
        if sha(archive) != SOURCE_SHA: raise ValueError("Original source release authentication failed")
        source_root = ROOT / "build/fanout_preflight"
        source_root.mkdir(exist_ok=False)
        with tarfile.open(archive) as tf: tf.extractall(source_root, filter="data")
        bundle = source_root / "fanout_source"
        manifest = json.loads((bundle / "manifest.json").read_text())
        if manifest["source_odb_sdc_nl"] != EXPECTED: raise ValueError("Wrong original source manifest")
        for name, digest in manifest["files"].items():
            path = (bundle / name).resolve()
            if not path.is_relative_to(bundle.resolve()) or sha(path) != digest: raise ValueError("Changed original source input")
        for name in ("LICENSE", "ATTRIBUTION.md", "manifest.json"):
            (OUT / ("source_" + name)).write_bytes((bundle / name).read_bytes())
        cluster = INPUT / "cluster8/cluster8/final"
        buffered = INPUT / "ten_buffers"
        paths = {"cluster8": {kind: cluster / kind / ("tt_um_warp." + ("nl.v" if kind == "nl" else kind)) for kind in DERIVED},
                 "ten_buffers": {"odb": buffered / "buffered.odb", "nl": buffered / "buffered.nl.v",
                    "sdc": buffered / "buffered_sta_nom_typ_1p20V_25C/final/sdc/tt_um_warp.sdc"}}
        authenticate_views(paths["cluster8"], DERIVED)
        authenticate_views(paths["ten_buffers"], BUFFERED)
        measured = json.loads((buffered / "result.json").read_text())
        if measured["passed"] is not True or measured["buffered_sha256"] != {k: BUFFERED[k] for k in ("odb", "nl")}:
            raise ValueError("Buffered source did not pass authenticated screen")
        result["buffer_source_connectivity"] = verify_connections((buffered / "before.tsv").read_text(), (buffered / "after.tsv").read_text())
        config = transform(json.loads((bundle / "config.json").read_text()),
                           lambda text: text.replace("@BUNDLE@", str(bundle)).replace("@PDK@", os.environ["PDK_ROOT"]))
        if config.get("PAD_LIBS") is None: config["PAD_LIBS"] = {}
        config["CTS_SINK_CLUSTERING_SIZE"] = 8
        config["meta"] = {"version": 2, "flow": ["OpenROAD.GlobalRouting"]}
        config_path = OUT / "config.json"
        config_path.write_text(json.dumps(config, indent=2) + "\n")
        result["identical_case_config_sha256"] = sha(config_path)
        result["original_source_archive_sha256"] = SOURCE_SHA
        observer = OUT / "observe.tcl"
        observer.write_text(CENSUS + '\nread_db $::env(WARP_GRT_ODB)\ncheck_placement -verbose\ncensus $::env(WARP_GRT_CENSUS)\n')
        def observe(label, odb):
            census = OUT / (label + ".tsv")
            command = ["docker", "run", "--rm", "-v", f"{ROOT}:{ROOT}", "-w", str(ROOT),
                       "-e", f"WARP_GRT_ODB={odb}", "-e", f"WARP_GRT_CENSUS={census}",
                       "--entrypoint", "openroad", IMAGE, "-exit", str(observer)]
            with (OUT / (label + "_placement.log")).open("w") as log:
                subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
            return census.read_text()
        for label in ("cluster8", "ten_buffers"):
            entry = {"passed": False, "source_sha256": authenticate_views(paths[label], DERIVED if label == "cluster8" else BUFFERED)}
            result["stages"][label] = entry
            save()
            try:
                before = observe(label + "_before", paths[label]["odb"])
                expected_census = (buffered / ("before.tsv" if label == "cluster8" else "after.tsv")).read_text()
                if parse_census(before) != parse_census(expected_census): raise ValueError("Authenticated original placement/connectivity census differs")
                state = {**{kind: str(path) for kind, path in paths[label].items()}, "metrics": {}}
                state_path = OUT / (label + "_input_state.json")
                state_path.write_text(json.dumps(state) + "\n")
                run = OUT / label
                run.mkdir()
                command = [sys.executable, "-m", "librelane", "--docker-no-tty", "--dockerized", "--pdk", "ihp-sg13cmos5l",
                           "--pdk-root", os.environ["PDK_ROOT"], "--manual-pdk", "--hide-progress-bar", "--force-run-dir", str(run),
                           "--with-initial-state", str(state_path), str(config_path)]
                with (OUT / (label + ".log")).open("w") as log:
                    entry["returncode"] = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=900).returncode
                stages = list(run.glob("*-openroad-globalrouting"))
                if len(stages) != 1: raise ValueError("Missing unique GRT stage")
                stage = stages[0]
                rawlog = (stage / "openroad-globalrouting.log").read_text()
                entry["native_congestion"] = parse_congestion(rawlog)
                if entry["returncode"] != 0: raise RuntimeError("Native GRT failed")
                final = json.loads((stage / "state_out.json").read_text())
                metrics = final["metrics"]
                entry["metrics"] = metrics
                overflow = require_zero_overflow(entry["native_congestion"], metrics)
                entry["reported_overflow_metrics"] = overflow
                if not isinstance(metrics.get("global_route__wirelength"), (int, float)) or metrics["global_route__wirelength"] <= 0:
                    raise ValueError("Missing native GRT wirelength")
                entry["global_route_wirelength_um"] = metrics["global_route__wirelength"]
                guide = stage / "after_grt.guide"
                if not guide.is_file() or guide.stat().st_size == 0: raise ValueError("Missing actual routing guides")
                entry["guide_sha256"] = sha(guide)
                entry["final_state_sha256"] = sha(stage / "state_out.json")
                entry["final_odb_sha256"] = sha(Path(final["odb"]))
                after = observe(label + "_after", final["odb"])
                if parse_census(after) != parse_census(before): raise ValueError("Routing mutated placement/master/top/pin connectivity")
                entry["native_placement_and_topology_exact"] = True
                resolved = json.loads((stage / "config.json").read_text())
                if resolved["CELL_LIBS"] != config["LIB"] or macro_contract(resolved["MACROS"]) != macro_contract(config["MACROS"]):
                    raise ValueError("GRT changed actual library/macro inputs")
                for key, val in config.items():
                    if key.startswith("GRT_") or key in ("CLOCK_PORT", "CLOCK_PERIOD", "MAX_FANOUT_CONSTRAINT", "PNR_SDC_FILE", "FALLBACK_SDC"):
                        if resolved.get(key) != val: raise ValueError("GRT changed protected setting " + key)
                entry["passed"] = True
            except Exception as exc:
                entry["error"] = str(exc)
            finally: save()
        for label in paths: authenticate_views(paths[label], DERIVED if label == "cluster8" else BUFFERED)
        result["authenticated_sources_unchanged"] = True
        result["passed"] = len(result["stages"]) == 2 and all(stage["passed"] for stage in result["stages"].values())
        if not result["passed"]: raise RuntimeError("One or more actual paired GRT cases failed")
    except Exception as exc:
        result["error"] = str(exc)
        raise
    finally: save()


if __name__ == "__main__": main()
