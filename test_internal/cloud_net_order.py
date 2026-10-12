"""Native net-order comparison on exact original and best combined placement.

Only copied Tcl changes, using zero capacity perturbation. No cell movement,
capacity relaxation, congestion acceptance, timing waiver or hardware change.
"""
import json
import os
from pathlib import Path
import sys

import cloud_reset_combined_grt as combo
import cloud_congestion_map as reporting
from cloud_fanout_preflight import sha

ROOT = reporting.ROOT
PATCH = ROOT / "patches/grt_net_order.tcl"


def seed_from_run(run):
    suffix = run.parent.name
    if suffix not in ("net_order_seed_0", "net_order_seed_41"):
        raise ValueError("Unapproved routing-order seed/output directory")
    return int(suffix.rsplit("_", 1)[1])


def instrument(top, common, directory):
    copied_top = original_instrument(top, common, directory)
    copied_common = directory / "common-grt.tcl"
    text = copied_common.read_text()
    if text.count(reporting.COMMAND) != 1:
        raise ValueError("Nonunique routing command in copied source")
    seed = seed_from_run(directory.parent)
    insertion = f"set warp_order_seed {seed}\n" + PATCH.read_text() + "\n"
    modified = text.replace(reporting.COMMAND, insertion + reporting.COMMAND)
    if modified.replace(insertion, "", 1) != text:
        raise ValueError("Unexpected copied-script alteration")
    copied_common.write_text(modified)
    policy = {"net_order_seed": seed, "capacities_perturbation_percentage":0,
        "capacity_adjustments_unchanged":True,"patch_sha256":sha(PATCH),
        "copied_common_sha256":sha(copied_common)}
    (directory / "net-order-policy.json").write_text(json.dumps(policy, indent=2)+"\n")
    with (directory / "ATTRIBUTION.md").open("a") as file:
        file.write("D-085 also inserts our net-order patch before global_route; capacity perturbation is zero.\n")
    return copied_top


original_instrument = reporting.instrument


def main():
    seed = int(os.environ["WARP_NET_ORDER_SEED"])
    if seed not in (0,41):
        raise ValueError("Unapproved seed")
    combo.INPUT = ROOT / "build/net_order_input"
    combo.OUT = ROOT / f"build/net_order_seed_{seed}"
    # The unchanged paired engine launches this wrapper inside the pinned image.
    reporting.__file__ = str(Path(__file__).resolve())
    try:
        combo.main()
    finally:
        path = combo.OUT / "result.json"
        if path.exists():
            result = json.loads(path.read_text())
            result["scope"] = "copied Tcl net-order experiment; original and combined placement"
            result["net_order_seed"] = seed
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
