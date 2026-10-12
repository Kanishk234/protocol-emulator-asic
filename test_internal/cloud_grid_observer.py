"""Read-only native grid observation on authenticated routing checkpoints.

Only copied Tcl gains observation, retaining the original router error. No cell movement,
capacity relaxation, congestion acceptance, timing waiver or hardware change.
"""
import json
from pathlib import Path
import sys

import cloud_reset_combined_grt as combo
import cloud_congestion_map as reporting
from cloud_fanout_preflight import sha

ROOT = reporting.ROOT
PATCH = ROOT / "patches/grt_grid_observer.tcl"


def instrument(top, common, directory):
    copied_top = original_instrument(top, common, directory)
    copied_common = directory / "common-grt.tcl"
    text = copied_common.read_text()
    if text.count(reporting.COMMAND) != 1:
        raise ValueError("Nonunique routing command in copied source")
    if directory.parent.parent.name != "grid_observer":
        raise ValueError("Unexpected grid-observer output scope")
    modified = text.replace(reporting.COMMAND, PATCH.read_text())
    if modified.replace(PATCH.read_text(), reporting.COMMAND, 1) != text:
        raise ValueError("Unexpected copied-source change")
    copied_common.write_text(modified)
    (directory / "grid-observer-policy.json").write_text(json.dumps({
        "read_only_grid_observer":True,"router_error_preserved":True,
        "patch_sha256":sha(PATCH),"copied_common_sha256":sha(copied_common)},indent=2)+"\n")
    with (directory / "ATTRIBUTION.md").open("a") as file:
        file.write("D-087 adds a read-only grid observer and preserves router failure status.\n")
    return copied_top


original_instrument = reporting.instrument


def main():
    combo.INPUT = ROOT / "build/grid_observer_input"
    combo.OUT = ROOT / "build/grid_observer"
    # The unchanged paired engine launches this wrapper inside the pinned image.
    reporting.__file__ = str(Path(__file__).resolve())
    try:
        combo.main()
    finally:
        path = combo.OUT / "result.json"
        if path.exists():
            result = json.loads(path.read_text())
            result["scope"] = "read-only native grid observation; unchanged original and combined routing"
            result["native_grid_observer"] = True
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
