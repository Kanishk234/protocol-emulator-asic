"""Alternate CUGR routing with calibrated native grid and guide guards.

Only copied Tcl selects CUGR and observes it, retaining native errors. No cell movement,
capacity relaxation, congestion acceptance, timing waiver or hardware change.
"""
import json
from pathlib import Path
import sys

import cloud_reset_combined_grt as combo
import cloud_hotspot_grt as paired
from audit_native_grid import audit as audit_grid, guide_coverage
import cloud_congestion_map as reporting
from cloud_fanout_preflight import sha

ROOT = reporting.ROOT
PATCH = ROOT / "patches/grt_cugr_observer.tcl"


def instrument(top, common, directory):
    copied_top = original_instrument(top, common, directory)
    copied_common = directory / "common-grt.tcl"
    text = copied_common.read_text()
    if text.count(reporting.COMMAND) != 1:
        raise ValueError("Nonunique routing command in copied source")
    if directory.parent.parent.name != "cugr":
        raise ValueError("Unexpected grid-observer output scope")
    modified = text.replace(reporting.COMMAND, PATCH.read_text())
    if modified.replace(PATCH.read_text(), reporting.COMMAND, 1) != text:
        raise ValueError("Unexpected copied-source change")
    copied_common.write_text(modified)
    (directory / "grid-observer-policy.json").write_text(json.dumps({
        "read_only_grid_observer":True,"router_error_preserved":True,
        "patch_sha256":sha(PATCH),"copied_common_sha256":sha(copied_common)},indent=2)+"\n")
    with (directory / "ATTRIBUTION.md").open("a") as file:
        file.write("D-088 adds CUGR plus a read-only grid and guide observer and preserves router failure status.\n")
    return copied_top


original_instrument = reporting.instrument


def collect(stage, raw):
    grid = audit_grid(stage / "native-grid.tsv")
    return {"native_grid":grid,"overflow":grid["total_overflow"],
        "overflow_source":"native OpenDB grid, not a FastRoute report",
        "native_marker_report_present":(stage / "native-congestion.rpt").is_file(),
        "engine":"CUGR"}


def require_clean(stage, entry, final, census):
    if entry["native_grid"]["total_overflow"]!=0:
        raise ValueError("Nonzero native CUGR grid overflow")
    if sum(v["usage"] for v in entry["native_grid"]["layers"].values())<=0:
        raise ValueError("Empty routing usage")
    coverage=guide_coverage(stage / "native-guides.tsv",census)
    entry["guide_coverage"]=coverage
    if coverage["missing_guides"]:
        raise ValueError("Required signal nets lack guides")
    violations={k:v for k,v in final["metrics"].items() if "overflow" in k.lower()}
    if any(v!=0 for v in violations.values()):
        raise ValueError("Native metrics report overflow")


def main():
    combo.INPUT = ROOT / "build/cugr_input"
    combo.OUT = ROOT / "build/cugr"
    if combo.OUT.name != "cugr" or combo.INPUT.name != "cugr_input":
        raise ValueError("CUGR run/artifact directories differ")
    # The unchanged paired engine launches this wrapper inside the pinned image.
    reporting.__file__ = str(Path(__file__).resolve())
    error = None
    try:
        paired.INPUT,paired.OUT = combo.INPUT,combo.OUT
        paired.SOURCE_RUN,paired.RESULT_SHA,paired.PADDED = combo.SOURCE_RUN,combo.RESULT_SHA,combo.CANDIDATE
        paired.validate_padding = combo.validate_move
        paired.main(observer=sys.modules[__name__])
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        path = combo.OUT / "result.json"
        if path.exists():
            result = json.loads(path.read_text())
            result["scope"] = "CUGR native grid/guide diagnostic; unchanged original and combined placement"
            result["native_grid_observer"] = True
            result["engine"] = "CUGR"
            if error:
                result["diagnostic_completed"] = False
                result["error"] = error
            result["capacity_perturbation_percentage"] = 0
            result["patch_sha256"] = sha(PATCH)
            for case in result.get("cases", {}).values():
                if "native_policy_exact" in case:
                    case["native_configuration_exact"] = case.pop("native_policy_exact")
            path.write_text(json.dumps(result,indent=2)+"\n")


if __name__ == "__main__":
    if len(sys.argv)==5 and sys.argv[1]=="--inside":
        reporting.instrument = instrument
        reporting.inside(*map(Path,sys.argv[2:]))
    elif len(sys.argv)==1:
        main()
    else:
        raise SystemExit("Unsupported invocation")
