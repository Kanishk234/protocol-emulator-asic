#!/usr/bin/env python3
"""Matched local routing-resource screen; explicitly never run DRT."""
import json
import os
from pathlib import Path
import subprocess
import sys

from postgrt_timing import screen


def main():
    root = Path("runs/hotspot-screen")
    root.mkdir(exist_ok=False)
    source = Path("runs/repaired-route/antenna/3-openroad-checkantennas-1/state_out.json")
    config = json.loads(Path("src/config_merged.json").read_text())
    check = json.loads(Path("runs/repaired-route/postantenna-sta/comparison.json").read_text())
    if Path(check["after_state"]).resolve() != source.resolve():
        raise ValueError("Unexpected post-antenna checkpoint")
    for corner, row in check["corners"].items():
        for kind in ("setup", "hold"):
            if row["after"][f"timing__{kind}__ws__corner:{corner}"] < 0:
                raise ValueError("Source failed estimated timing")
    state = json.loads(source.read_text())
    for key in ("odb", "def", "nl", "pnl", "sdc"):
        if not Path(state[key]).is_file():
            raise ValueError(f"Missing source {key}")
    if float(config["CLOCK_PERIOD"]) != 20 or float(config["PL_TARGET_DENSITY_PCT"]) != 56:
        raise ValueError("Wrong candidate clock/density")
    config.update(GRT_ADJUSTMENT=0.16, OPENROAD_THREADS=4,
                  PNR_SDC_FILE=str(Path("src/signoff.sdc").resolve()))
    results = {}
    for tag, image in (("baseline", None), ("region", "tripwire-hotspot:local")):
        if image is None:
            os.environ.pop("LIBRELANE_IMAGE_OVERRIDE", None)
        else:
            os.environ["LIBRELANE_IMAGE_OVERRIDE"] = image
        cfg = dict(config)
        cfg["meta"] = {"version": config.get("meta", {}).get("version", 1),
                       "flow": ["OpenROAD.GlobalRouting", "OpenROAD.CheckAntennas"]}
        path = Path(f"src/config_hotspot_{tag}.json")
        path.write_text(json.dumps(cfg, indent=2) + "\n")
        output = root / tag
        output.mkdir()
        subprocess.run([sys.executable, "-m", "librelane", "--pdk-root", os.environ["PDK_ROOT"],
                        "--docker-no-tty", "--dockerized", "--pdk", "ihp-sg13cmos5l",
                        "--manual-pdk", "--run-tag", tag, "--force-run-dir", str(output),
                        "--hide-progress-bar", "--with-initial-state", str(source), str(path)], check=True)
        grt = output / "1-openroad-globalrouting"
        resolved = json.loads((grt / "config.json").read_text())
        if float(resolved["GRT_ADJUSTMENT"]) != 0.16 or resolved["OPENROAD_THREADS"] != 4:
            raise ValueError("Resolved routing inputs changed")
        if tag == "region" and "TRIPWIRE hotspot screen:" not in (grt / "openroad-globalrouting.log").read_text():
            raise ValueError("Region override did not execute")
        final = output / "2-openroad-checkantennas/state_out.json"
        fresh = json.loads((grt / "or_metrics_out.json").read_text())
        results[tag] = {"state": str(final), "grt_metrics": fresh,
                        "antenna_metrics": json.loads(final.with_name("or_metrics_out.json").read_text())}
        if list(output.glob("*-openroad-detailedrouting")):
            raise ValueError("Unexpected DRT")
    os.environ.pop("LIBRELANE_IMAGE_OVERRIDE", None)
    screen(Path("src/config_merged.json"), Path(results["baseline"]["state"]),
           root / "sta", os.environ["PDK_ROOT"], repaired=Path(results["region"]["state"]),
           sdc=Path("src/signoff.sdc"))
    (root / "screen.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
