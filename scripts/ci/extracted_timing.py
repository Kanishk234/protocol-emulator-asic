#!/usr/bin/env python3
"""Prepared extraction/STA diagnostic; requires an actual completed clean route."""
import json
import os
import subprocess
import sys
from pathlib import Path

STEPS = ["Odb.RemoveRoutingObstructions", "OpenROAD.CheckAntennas", "Checker.TrDRC",
         "Odb.ReportDisconnectedPins", "Checker.DisconnectedPins", "Odb.ReportWireLength",
         "Checker.WireLength", "OpenROAD.FillInsertion", "Odb.CellFrequencyTables",
         "OpenROAD.RCX", "OpenROAD.STAPostPNR"]


def route_checkpoint(root):
    states = list(root.glob("*-openroad-detailedrouting/state_out.json"))
    if len(states) != 1:
        raise ValueError("A completed DRT state is required; a timeout cannot be extracted")
    state = json.loads(states[0].read_text())
    if state["metrics"].get("route__drc_errors") != 0:
        raise ValueError("Completed route must have zero route DRC errors")
    for key in ("odb", "def", "nl", "pnl"):
        if not Path(state[key]).is_file():
            raise ValueError(f"Missing final route {key}")
    return states[0]


def main():
    checkpoint = route_checkpoint(Path("runs/repaired-route/drt"))
    config = json.loads(Path("src/config_merged.json").read_text())
    if float(config["CLOCK_PERIOD"]) != 20:
        raise ValueError("Expected the unchanged 20 ns candidate")
    config.update(meta={"version": config.get("meta", {}).get("version", 1), "flow": STEPS},
                  OPENROAD_THREADS=4, STA_THREADS=3,
                  SIGNOFF_SDC_FILE=str(Path("src/signoff.sdc").resolve()))
    config["STA_CORNERS"] = ["nom_fast_1p32V_m40C", "nom_slow_1p08V_125C", "nom_typ_1p20V_25C"]
    path = Path("src/config_extracted_timing.json")
    path.write_text(json.dumps(config, indent=2) + "\n")
    output = Path("runs/extracted-timing")
    output.mkdir(parents=True, exist_ok=False)
    subprocess.run([sys.executable, "-m", "librelane", "--pdk-root", os.environ["PDK_ROOT"],
                    "--docker-no-tty", "--dockerized", "--pdk", "ihp-sg13cmos5l",
                    "--manual-pdk", "--run-tag", "extracted-timing", "--force-run-dir", str(output),
                    "--hide-progress-bar", "--with-initial-state", str(checkpoint), str(path)], check=True)
    states = list(output.glob("*-openroad-stapostpnr/state_out.json"))
    if len(states) != 1:
        raise ValueError("Fresh extracted STA state missing")
    metrics = json.loads(states[0].read_text())["metrics"]
    fresh = {}
    for corner in config["STA_CORNERS"]:
        # Require reports from each newly executed corner, not just inherited state keys.
        corner_dir = states[0].parent / corner
        for kind in ("setup", "hold"):
            report = corner_dir / ("ws.max.rpt" if kind == "setup" else "ws.min.rpt")
            if not report.is_file() or corner not in report.read_text():
                raise ValueError(f"Fresh extracted {corner} {kind} report missing")
            key = f"timing__{kind}__ws__corner:{corner}"
            fresh[key] = metrics[key]
    (output / "corner_summary.json").write_text(json.dumps(fresh, indent=2) + "\n")
    print(json.dumps(fresh, indent=2))
    # Deliberately retain negative results as diagnostic evidence. This is not
    # the official full GDS/DRC/LVS/precheck signoff workflow.


if __name__ == "__main__":
    main()
