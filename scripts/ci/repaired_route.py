#!/usr/bin/env python3
"""Continue the audited signoff-aware repair through antenna repair and DRT."""
import json
import os
import subprocess
import sys
from pathlib import Path

from postgrt_timing import screen


def main():
    output = Path("runs/repaired-route")
    output.mkdir(parents=True, exist_ok=False)
    repair_root = Path("runs/postgrt-timing/repair")
    states = list(repair_root.glob("*-openroad-resizertimingpostgrt/state_out.json"))
    if len(states) != 1:
        raise ValueError(f"Expected one saved repaired checkpoint: {states}")
    repaired = states[0]
    config = json.loads(Path("src/config_merged.json").read_text())
    source_cfg = json.loads(Path("runs/wokwi/39-openroad-globalrouting/config.json").read_text())
    repair_cfg = json.loads(repaired.with_name("config.json").read_text())
    comparison = json.loads(Path("runs/postgrt-timing/comparison.json").read_text())
    if float(config["CLOCK_PERIOD"]) != 20 or float(config["PL_TARGET_DENSITY_PCT"]) != 56:
        raise ValueError("Unexpected candidate clock/density")
    for cfg in (source_cfg, repair_cfg):
        if float(cfg["GRT_ADJUSTMENT"]) != 0.16:
            raise ValueError("Unexpected checkpoint routing adjustment")
    if float(repair_cfg["GRT_RESIZER_SETUP_SLACK_MARGIN"]) != 0:
        raise ValueError("Repair must be the audited zero-margin screen")
    if repair_cfg["RSZ_CORNERS"] != ["nom_slow_1p08V_125C"]:
        raise ValueError("Repair must target the audited slow corner")
    if Path(repair_cfg["PNR_SDC_FILE"]).resolve() != Path("src/signoff.sdc").resolve():
        raise ValueError("Repair must use signoff constraints")
    state = json.loads(repaired.read_text())
    for key in ("odb", "def", "sdc", "pnl", "nl"):
        if not Path(state[key]).is_file():
            raise ValueError(f"Missing repaired checkpoint {key}")
    for corner, row in comparison["corners"].items():
        for kind in ("setup", "hold"):
            if row["after"][f"timing__{kind}__ws__corner:{corner}"] < 0:
                raise ValueError("Source repair has negative setup/hold slack")
    config.update(GRT_ADJUSTMENT=0.16, OPENROAD_THREADS=4,
                  PNR_SDC_FILE=str(Path("src/signoff.sdc").resolve()),
                  DRT_SAVE_DRC_REPORT_ITERS=5)

    def run(tag, checkpoint, steps):
        cfg = dict(config)
        cfg["meta"] = {"version": config.get("meta", {}).get("version", 1), "flow": steps}
        path = Path(f"src/config_repaired_{tag}.json")
        path.write_text(json.dumps(cfg, indent=2) + "\n")
        root = output / tag
        root.mkdir()
        subprocess.run([
            sys.executable, "-m", "librelane", "--pdk-root", os.environ["PDK_ROOT"],
            "--docker-no-tty", "--dockerized", "--pdk", "ihp-sg13cmos5l",
            "--manual-pdk", "--run-tag", tag, "--force-run-dir", str(root),
            "--hide-progress-bar", "--with-initial-state", str(checkpoint), str(path),
        ], check=True)
        return root

    antenna = run("antenna", repaired, ["OpenROAD.CheckAntennas", "OpenROAD.RepairAntennas",
                                        "OpenROAD.CheckAntennas"])
    # Duplicate CheckAntennas steps are normalized to -1 by SequentialFlow.
    final_checks = list(antenna.glob("*-openroad-checkantennas-1/state_out.json"))
    if len(final_checks) != 1:
        raise ValueError(f"Expected final antenna check: {final_checks}")
    post = final_checks[0]
    (output / "postantenna_checkpoint.txt").write_text(str(post) + "\n")
    screen(Path("src/config_merged.json"), repaired, output / "postantenna-sta",
           os.environ["PDK_ROOT"], repaired=post, sdc=Path("src/signoff.sdc"))
    fresh = json.loads((output / "postantenna-sta/comparison.json").read_text())
    for corner, row in fresh["corners"].items():
        for kind in ("setup", "hold"):
            if row["after"][f"timing__{kind}__ws__corner:{corner}"] < 0:
                raise ValueError(f"Post-antenna {corner} {kind} failed; DRT not launched")
    run("drt", post, ["OpenROAD.DetailedRouting"])


if __name__ == "__main__":
    main()
