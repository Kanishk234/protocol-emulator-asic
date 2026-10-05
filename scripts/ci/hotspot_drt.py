#!/usr/bin/env python3
"""Route the audited no-mirroring checkpoint; this is not full signoff."""
import json
import os
from pathlib import Path
import subprocess
import sys

from postgrt_timing import CORNERS


def validate(root):
    gates = json.loads((root / "gates.json").read_text())
    state = root / "antenna/3-openroad-checkantennas-1/state_out.json"
    if Path(gates["state"]).resolve() != state.resolve():
        raise ValueError("Unexpected checkpoint")
    if not gates["disable_mirroring"] or not gates["estimated_timing_and_antenna_pass"]:
        raise ValueError("Source trial did not pass required gates")
    cfg = json.loads((root / "timing/repair/1-openroad-resizertimingpostgrt/config.json").read_text())
    if cfg["PL_OPTIMIZE_MIRRORING"] is not False or float(cfg["GRT_ADJUSTMENT"]) != 0.16:
        raise ValueError("Wrong source mirroring/routing config")
    if cfg["OPENROAD_THREADS"] != 4 or float(cfg["GRT_RESIZER_SETUP_SLACK_MARGIN"]) != 0:
        raise ValueError("Wrong source repair inputs")
    if Path(cfg["PNR_SDC_FILE"]).resolve() != Path("src/signoff.sdc").resolve():
        raise ValueError("Wrong source constraints")
    timing = json.loads((root / "postantenna-sta/comparison.json").read_text())
    if Path(timing["after_state"]).resolve() != state.resolve():
        raise ValueError("Timing covers wrong state")
    for corner in CORNERS:
        m = timing["corners"][corner]["after"]
        for kind in ("setup", "hold"):
            if m[f"timing__{kind}__ws__corner:{corner}"] < 0 or m[f"timing__{kind}_vio__count__corner:{corner}"] != 0:
                raise ValueError("Failing source timing")
    antenna = json.loads(state.with_name("or_metrics_out.json").read_text())
    if antenna["antenna__violating__nets"] != 0 or antenna["antenna__violating__pins"] != 0:
        raise ValueError("Dirty antenna source")
    for key in ("odb", "def", "nl", "pnl", "sdc"):
        if not Path(json.loads(state.read_text())[key]).is_file():
            raise ValueError(f"Missing checkpoint {key}")
    return state


def main():
    state = validate(Path("runs/hotspot-repair"))
    config = json.loads(Path("src/config_merged.json").read_text())
    if float(config["CLOCK_PERIOD"]) != 20 or float(config["PL_TARGET_DENSITY_PCT"]) != 56:
        raise ValueError("Wrong candidate")
    config.update(GRT_ADJUSTMENT=0.16, OPENROAD_THREADS=4, PL_OPTIMIZE_MIRRORING=False,
                  PNR_SDC_FILE=str(Path("src/signoff.sdc").resolve()), DRT_SAVE_DRC_REPORT_ITERS=5)
    config["meta"] = {"version": config.get("meta", {}).get("version", 1), "flow": ["OpenROAD.DetailedRouting"]}
    path = Path("src/config_hotspot_drt.json")
    path.write_text(json.dumps(config, indent=2) + "\n")
    output = Path("runs/hotspot-drt")
    output.mkdir(exist_ok=False)
    os.environ["LIBRELANE_IMAGE_OVERRIDE"] = "tripwire-hotspot:local"
    subprocess.run([sys.executable, "-m", "librelane", "--pdk-root", os.environ["PDK_ROOT"],
                    "--docker-no-tty", "--dockerized", "--pdk", "ihp-sg13cmos5l", "--manual-pdk",
                    "--run-tag", "hotspot-drt", "--force-run-dir", str(output), "--hide-progress-bar",
                    "--with-initial-state", str(state), str(path)], check=True)


if __name__ == "__main__":
    main()
