#!/usr/bin/env python3
"""Matched RTL screen ending at GRT plus fresh signoff-aware timing repair."""
import json
import os
from pathlib import Path
import subprocess
import sys

from postgrt_timing import screen, CORNERS


def timing_placement(variant):
    if variant not in {"baseline", "rx-factor", "pad-mux", "load-select", "input-decode", "cached-input", "timing-placement", "cts-cluster8", "drop-counter", "drop-qual", "bs-resync", "bs-csa", "bs-event-late", "bs-load-flat", "setup-margin"}:
        raise ValueError("Unknown timing screen variant")
    return variant in {"timing-placement", "cts-cluster8", "drop-counter", "drop-qual", "bs-resync", "bs-csa", "bs-event-late", "bs-load-flat", "setup-margin"}


def repair_margin(variant):
    timing_placement(variant)  # reject an unknown experiment before any flow runs
    return 2.0 if variant == "setup-margin" else 0.0


def checkpoint(root):
    if list(root.glob("*-openroad-detailedrouting")):
        raise ValueError("Unexpected detailed routing in the RTL screen")
    states = list(root.glob("*-openroad-globalrouting/state_out.json"))
    if len(states) != 1:
        raise ValueError("Exactly one global-route checkpoint required")
    state = json.loads(states[0].read_text())
    for key in ("odb", "def", "nl", "pnl", "sdc"):
        if not Path(state[key]).is_file():
            raise ValueError(f"Missing global-route {key}")
    return states[0]


def main():
    config = json.loads(Path("src/config_merged.json").read_text())
    if float(config["CLOCK_PERIOD"]) != 20 or float(config["PL_TARGET_DENSITY_PCT"]) != 56:
        raise ValueError("Unexpected candidate clock/density")
    config.update(GRT_ADJUSTMENT=0.16, OPENROAD_THREADS=4, PL_OPTIMIZE_MIRRORING=False,
                  PL_TIMING_DRIVEN=timing_placement(os.environ["VARIANT"]),
                  PL_RESIZER_SETUP_SLACK_MARGIN=0, GRT_RESIZER_SETUP_SLACK_MARGIN=0,
                  PNR_SDC_FILE=str(Path("src/signoff.sdc").resolve()),
                  PNR_CORNERS=[CORNERS[1], CORNERS[0], CORNERS[2]], RSZ_CORNERS=[CORNERS[1]])
    if os.environ["VARIANT"] == "cts-cluster8":
        config["CTS_SINK_CLUSTERING_SIZE"] = 8
    path = Path("src/config_rx_screen.json")
    path.write_text(json.dumps(config, indent=2) + "\n")
    root = Path("runs/rtl-grt-screen")
    flow = root / "flow"
    flow.mkdir(parents=True, exist_ok=False)
    os.environ["LIBRELANE_IMAGE_OVERRIDE"] = "tripwire-hotspot:local"
    subprocess.run([sys.executable, "-m", "librelane", "--pdk-root", os.environ["PDK_ROOT"],
                    "--docker-no-tty", "--dockerized", "--pdk", "ihp-sg13cmos5l", "--manual-pdk",
                    "--run-tag", "rtl-screen", "--force-run-dir", str(flow), "--hide-progress-bar",
                    # GlobalRouting occurs once in the pinned Classic flow.
                    "--to", "OpenROAD.GlobalRouting", str(path)], check=True)
    source = checkpoint(flow)
    screen(path, source, root / "timing", os.environ["PDK_ROOT"],
           sdc=Path("src/signoff.sdc"), setup_margin=repair_margin(os.environ["VARIANT"]),
           repair_corners=CORNERS if os.environ.get("ALL_CORNER_REPAIR") == "1" else None)


if __name__ == "__main__":
    main()
