#!/usr/bin/env python3
"""Repair the region trial and measure its post-antenna gates, without DRT."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from postgrt_timing import CORNERS, screen


def repair_config(disable_mirroring):
    path = Path("src/config_merged.json")
    if disable_mirroring:
        config = json.loads(path.read_text())
        config["PL_OPTIMIZE_MIRRORING"] = False
        path = Path("src/config_hotspot_repair_base.json")
        path.write_text(json.dumps(config, indent=2) + "\n")
    return path


def followup_source(previous):
    gates = json.loads((previous / "gates.json").read_text())
    source = previous / "antenna/3-openroad-checkantennas-1/state_out.json"
    if Path(gates["state"]).resolve() != source.resolve() or not gates["critical_branch"] or not gates["disable_mirroring"]:
        raise ValueError("Unexpected branch follow-up source")
    antenna = json.loads(source.with_name("or_metrics_out.json").read_text())
    if antenna["antenna__violating__nets"] or antenna["antenna__violating__pins"]:
        raise ValueError("Follow-up requires clean source antenna")
    return source


def main(disable_mirroring=False, critical_branch=False, postantenna=False):
    if critical_branch and not disable_mirroring:
        raise ValueError("Branch comparison requires the established no-mirroring baseline")
    if postantenna and (critical_branch or not disable_mirroring):
        raise ValueError("Follow-up must retain no-mirroring and must not reinsert the branch")
    root = Path("runs/branch-followup" if postantenna else "runs/hotspot-repair")
    source = Path("runs/hotspot-screen/region/2-openroad-checkantennas/state_out.json")
    provenance = json.loads(Path("runs/hotspot-screen/screen.json").read_text())
    if Path(provenance["region"]["state"]).resolve() != source.resolve():
        raise ValueError("Unexpected region checkpoint")
    cfg = json.loads(Path("runs/hotspot-screen/region/1-openroad-globalrouting/config.json").read_text())
    if float(cfg["GRT_ADJUSTMENT"]) != 0.16 or cfg["OPENROAD_THREADS"] != 4:
        raise ValueError("Unexpected routing inputs")
    log = Path("runs/hotspot-screen/region/1-openroad-globalrouting/openroad-globalrouting.log")
    if "TRIPWIRE hotspot screen:" not in log.read_text():
        raise ValueError("Missing region execution evidence")
    if postantenna:
        source = followup_source(Path("runs/hotspot-repair"))
    state = json.loads(source.read_text())
    for key in ("odb", "def", "nl", "pnl", "sdc"):
        if not Path(state[key]).is_file():
            raise ValueError(f"Missing region state {key}")
    root.mkdir(exist_ok=False)
    config_path = repair_config(disable_mirroring)
    os.environ["LIBRELANE_IMAGE_OVERRIDE"] = "tripwire-hotspot:local"
    screen(config_path, source, root / "timing", os.environ["PDK_ROOT"],
           sdc=Path("src/signoff.sdc"), setup_margin=0)
    repair = root / "timing/repair/1-openroad-resizertimingpostgrt"
    resolved = json.loads((repair / "config.json").read_text())
    if disable_mirroring and resolved["PL_OPTIMIZE_MIRRORING"] is not False:
        raise ValueError("Repair did not disable mirroring")
    if "TRIPWIRE hotspot screen:" not in (repair / "openroad-resizertimingpostgrt.log").read_text():
        raise ValueError("Timing repair failed to preserve region reservation")
    if critical_branch and "TRIPWIRE critical branch:" not in (repair / "openroad-resizertimingpostgrt.log").read_text():
        raise ValueError("Missing critical-branch execution evidence")
    config = json.loads(config_path.read_text())
    config.update(GRT_ADJUSTMENT=0.16, OPENROAD_THREADS=4,
                  PNR_SDC_FILE=str(Path("src/signoff.sdc").resolve()))
    config["meta"] = {"version": config.get("meta", {}).get("version", 1),
                      "flow": ["OpenROAD.CheckAntennas", "OpenROAD.RepairAntennas", "OpenROAD.CheckAntennas"]}
    path = Path("src/config_hotspot_repair_antenna.json")
    path.write_text(json.dumps(config, indent=2) + "\n")
    antenna = root / "antenna"
    antenna.mkdir()
    subprocess.run([sys.executable, "-m", "librelane", "--pdk-root", os.environ["PDK_ROOT"],
                    "--docker-no-tty", "--dockerized", "--pdk", "ihp-sg13cmos5l", "--manual-pdk",
                    "--run-tag", "antenna", "--force-run-dir", str(antenna), "--hide-progress-bar",
                    "--with-initial-state", str(repair / "state_out.json"), str(path)], check=True)
    final = antenna / "3-openroad-checkantennas-1/state_out.json"
    for log in antenna.glob("**/openroad-diodeinsertion.log"):
        if "TRIPWIRE hotspot screen:" not in log.read_text():
            raise ValueError("Antenna rerouting failed to preserve region reservation")
    screen(config_path, repair / "state_out.json", root / "postantenna-sta",
           os.environ["PDK_ROOT"], repaired=final, sdc=Path("src/signoff.sdc"))
    metrics = json.loads(final.with_name("or_metrics_out.json").read_text())
    timing = json.loads((root / "postantenna-sta/comparison.json").read_text())
    ready = all(timing["corners"][corner]["after"][f"timing__{kind}__ws__corner:{corner}"] >= 0
                for corner in CORNERS for kind in ("setup", "hold"))
    ready &= metrics["antenna__violating__nets"] == 0 and metrics["antenna__violating__pins"] == 0
    (root / "gates.json").write_text(json.dumps({"state": str(final), "antenna": metrics,
        "estimated_timing_and_antenna_pass": ready, "drt_launched": False,
        "disable_mirroring": disable_mirroring, "critical_branch": critical_branch or postantenna,
        "postantenna_followup": postantenna}, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disable-mirroring", action="store_true")
    parser.add_argument("--critical-branch", action="store_true")
    parser.add_argument("--postantenna", action="store_true")
    args = parser.parse_args()
    main(args.disable_mirroring, args.critical_branch, args.postantenna)
