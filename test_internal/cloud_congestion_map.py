"""Native hotspot reports on unchanged authenticated paired GRT checkpoints.

Reuses source/placement/policy gates from cloud_fanout_grt. Only copied Tcl
reporting options differ. A successful diagnostic NEVER means routing passed.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

import cloud_fanout_grt as paired
from cloud_fanout_preflight import sha

ROOT = paired.ROOT
OUT = ROOT / "build/congestion_map"
TOP_SHA = "9cceedd2c477f85b25362d5e3833fe0e9c0d85f14248060fc38e3fdec0c6187c"
COMMON_SHA = "55b64e4725fb0e58e8ca56945f2858e6f0c88c0a183252c682b63f6675e22681"
SOURCE = 'source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl'
COMMAND = 'log_cmd global_route {*}$arg_list'


def instrument(top, common, directory):
    if sha(top) != TOP_SHA or sha(common) != COMMON_SHA:
        raise ValueError("Pinned original Tcl source hashes differ")
    original_top, original_common = top.read_text(), common.read_text()
    if original_top.count(SOURCE) != 1 or original_common.count(COMMAND) != 1:
        raise ValueError("Reporting insertion anchors are not unique")
    directory.mkdir(exist_ok=False)
    copied_common = directory / "common-grt.tcl"
    flags = ('lappend arg_list -congestion_report_file $::env(STEP_DIR)/native-congestion.rpt\n'
             'lappend arg_list -congestion_report_iter_step $::env(GRT_OVERFLOW_ITERS)\n')
    modified = original_common.replace(COMMAND, flags + COMMAND)
    if modified.replace(flags, "", 1) != original_common:
        raise ValueError("Unexpected non-reporting Tcl change")
    copied_common.write_text(modified)
    copied_top = directory / "grt.tcl"
    copied_top.write_text(original_top.replace(SOURCE, 'source {' + str(copied_common) + '}'))
    (directory / "original-grt.tcl").write_text(original_top)
    (directory / "original-common-grt.tcl").write_text(original_common)
    (directory / "ATTRIBUTION.md").write_text(
        "Copied from pinned LibreLane3.1.0.dev3 Docker image; Efabless2020–2023, Apache2.0.\n"
        "Copyright/license headers retained. Only congestion reporting flags added.\n"
        "Upstream installed files remain unchanged.\n")
    (directory / "source-sha256.json").write_text(json.dumps({"top": TOP_SHA, "common": COMMON_SHA,
        "reporting_top": sha(copied_top), "reporting_common": sha(copied_common)}, indent=2))
    return copied_top


def inside(config, state, run):
    from librelane.flows import SequentialFlow
    from librelane.state import State
    from librelane.steps import OpenROAD

    class ReportRouting(OpenROAD.GlobalRouting):
        def get_script_path(self):
            if hasattr(self, "_reporting_script"):
                return self._reporting_script
            top = Path(super().get_script_path())
            self._reporting_script = str(instrument(top, top.parent / "common/grt.tcl", run / "reporting-source"))
            return self._reporting_script

    class ReportFlow(SequentialFlow):
        Steps = [ReportRouting]

    flow = ReportFlow(str(config), design_dir=str(ROOT), pdk="ihp-sg13cmos5l",
                      pdk_root=os.environ["PDK_ROOT"])
    flow.start(with_initial_state=State.loads(state.read_text()), _force_run_dir=str(run))


def main():
    # Retain the existing helper's complete source/census/policy authentication.
    # Replace ONLY its two native GRT subprocess launches with the API wrapper.
    original_run = subprocess.run
    launch_count = 0

    def dispatch(command, **kwargs):
        nonlocal launch_count
        if isinstance(command, list) and command[:3] == [sys.executable, "-m", "librelane"]:
            launch_count += 1
            if launch_count > 2:
                raise ValueError("Unexpected third GRT launch")
            run = Path(command[command.index("--force-run-dir") + 1])
            state = Path(command[command.index("--with-initial-state") + 1])
            config = Path(command[-1])
            wrapped = ["docker", "run", "--rm", "-v", f"{ROOT}:{ROOT}", "-w", str(ROOT),
                       "-e", f"PDK_ROOT={os.environ['PDK_ROOT']}", "--entrypoint", "python3",
                       paired.IMAGE, str(Path(__file__).resolve()), "--inside", str(config), str(state), str(run)]
            return original_run(wrapped, **kwargs)
        return original_run(command, **kwargs)

    paired.OUT = OUT
    subprocess.run = dispatch
    error = None
    try:
        paired.main(50)
    except Exception as exc:
        error = str(exc)  # Preserve strict native failure in result.json, not a waiver.
    finally:
        subprocess.run = original_run
    result = json.loads((OUT / "result.json").read_text())
    diagnostic = {"physical_acceptance": False, "configured_timing_acceptance": False,
                  "underlying_route_passed": result["passed"], "underlying_error": error,
                  "native_launches": launch_count, "cases": {}}
    for label in ("cluster8", "ten_buffers"):
        reports = list((OUT / label).glob("*-openroad-globalrouting/native-congestion.rpt"))
        entry = result["stages"].get(label, {})
        if len(reports) != 1 or not entry.get("native_congestion"):
            raise RuntimeError("Missing actual native hotspot evidence for " + label)
        overflow = entry["native_congestion"][-1]["total_overflow"]
        if overflow and not reports[0].stat().st_size:
            raise RuntimeError("Empty native hotspot report with nonzero overflow")
        resolved = json.loads((reports[0].parent / "config.json").read_text())
        source_config = json.loads((OUT / "config.json").read_text())
        for key, val in source_config.items():
            if key.startswith(("GRT_", "RT_")) or key in (
                    "CLOCK_PORT", "CLOCK_PERIOD", "MAX_FANOUT_CONSTRAINT", "PNR_SDC_FILE", "FALLBACK_SDC"):
                if resolved.get(key) != val:
                    raise RuntimeError("Protected native setting changed: " + key)
        if resolved["CELL_LIBS"] != source_config["LIB"] or paired.macro_contract(resolved["MACROS"]) != paired.macro_contract(source_config["MACROS"]):
            raise RuntimeError("Native library or fixed macro views changed")
        diagnostic["cases"][label] = {"route_passed": entry["passed"], "native_error": entry.get("error"),
            "overflow": overflow, "raw_hotspot_report": str(reports[0].relative_to(OUT)),
            "report_sha256": sha(reports[0]), "report_bytes": reports[0].stat().st_size,
            "resolved_native_policy_exact": True}
    if launch_count != 2 or result.get("authenticated_sources_unchanged") is not True:
        raise RuntimeError("Incomplete authenticated native diagnostic")
    diagnostic["diagnostic_collection_passed"] = True
    (OUT / "diagnostic.json").write_text(json.dumps(diagnostic, indent=2) + "\n")


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--inside":
        inside(*map(Path, sys.argv[2:]))
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit("Unsupported invocation")
