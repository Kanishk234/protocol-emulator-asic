#!/usr/bin/env python3
"""Prepared extraction/STA diagnostic; requires an actual completed clean route."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from electrical_report import audit_corners

STEPS = ["Odb.RemoveRoutingObstructions", "OpenROAD.CheckAntennas", "Checker.TrDRC",
         "Odb.ReportDisconnectedPins", "Checker.DisconnectedPins", "Odb.ReportWireLength",
         "Checker.WireLength", "OpenROAD.FillInsertion", "Odb.CellFrequencyTables",
         "OpenROAD.RCX", "OpenROAD.STAPostPNR"]


def preserve_signoff_constraints(source, output):
    """Export the exact STA input separately from inherited PnR state views."""
    data = source.read_bytes()
    saved = output / 'effective-signoff.sdc'
    saved.write_bytes(data)
    (output / 'constraint_identity.json').write_text(json.dumps({
        'sta_constraint_file': str(saved.resolve()),
        'source_constraint_file': str(source.resolve()),
        'sha256': hashlib.sha256(data).hexdigest(),
        'inherited_state_sdc_is_signoff_evidence': False,
    }, indent=2) + '\n')
    return saved.resolve()


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


def main(route_root=Path("runs/repaired-route/drt")):
    checkpoint = route_checkpoint(route_root)
    config = json.loads(Path("src/config_merged.json").read_text())
    if float(config["CLOCK_PERIOD"]) != 20:
        raise ValueError("Expected the unchanged 20 ns candidate")
    config.update(meta={"version": config.get("meta", {}).get("version", 1), "flow": STEPS},
                  OPENROAD_THREADS=4, STA_THREADS=3,
                  SIGNOFF_SDC_FILE=str(Path("src/signoff.sdc").resolve()))
    config["STA_CORNERS"] = ["nom_fast_1p32V_m40C", "nom_slow_1p08V_125C", "nom_typ_1p20V_25C"]
    output = Path("runs/extracted-timing")
    output.mkdir(parents=True, exist_ok=False)
    config['SIGNOFF_SDC_FILE'] = str(preserve_signoff_constraints(Path('src/signoff.sdc'), output))
    path = Path("src/config_extracted_timing.json")
    path.write_text(json.dumps(config, indent=2) + "\n")
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
    electrical = audit_corners(states[0].parent, config['STA_CORNERS'])
    (output / 'electrical_summary.json').write_text(json.dumps(electrical, indent=2) + '\n')
    print(json.dumps(fresh, indent=2))
    # Deliberately retain negative results as diagnostic evidence. This is not
    # the official full GDS/DRC/LVS/precheck signoff workflow.


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-root", type=Path, default=Path("runs/repaired-route/drt"))
    main(parser.parse_args().route_root)
