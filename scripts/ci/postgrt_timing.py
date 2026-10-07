#!/usr/bin/env python3
"""Matched saved-checkpoint STA with one corner per OpenROAD process.

Run inside the pinned LibreLane/PDK CI environment. Explicit step lists prevent
this diagnostic from entering detailed routing. Never read inherited metrics.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

CORNERS = ("nom_fast_1p32V_m40C", "nom_slow_1p08V_125C", "nom_typ_1p20V_25C")


def fresh_metrics(root, step, corner):
    paths = list(root.glob(f"*-{step}/or_metrics_out.json"))
    if len(paths) != 1:
        raise ValueError(f"Expected one fresh {step} metrics file in {root}: {paths}")
    metrics = json.loads(paths[0].read_text())
    for kind in ("setup", "hold"):
        for field in ("ws", "wns", "tns"):
            key = f"timing__{kind}__{field}__corner:{corner}"
            if key not in metrics:
                raise ValueError(f"Missing fresh metric {key} in {paths[0]}")
    return metrics


def screen(config_path, before, output, pdk_root, repaired=None, sdc=None, setup_margin=None, repair_corners=None, hold_margin=None):
    if repair_corners is not None and tuple(repair_corners) != CORNERS:
        raise ValueError("Repair corners must be the complete pinned corner set")
    base = json.loads(config_path.read_text())
    if float(base["CLOCK_PERIOD"]) != 20:
        raise ValueError("Screen requires the 20 ns candidate")
    # Source-run CLI overrides may not be present in config_merged.json.
    # The workflow validates 0.16 in the actual GlobalRouting step config.
    base["GRT_ADJUSTMENT"] = 0.16
    if sdc is not None:
        base["PNR_SDC_FILE"] = str(sdc.resolve())
    if setup_margin is not None:
        if setup_margin < 0:
            raise ValueError("Setup repair margin must be nonnegative")
        base["GRT_RESIZER_SETUP_SLACK_MARGIN"] = setup_margin
    if hold_margin is not None:
        if hold_margin not in (0.05, 0.10, 0.125, 0.15):
            raise ValueError("Hold target must be a bounded 0.05, 0.10, 0.125 or 0.15 ns experiment")
        base["GRT_RESIZER_HOLD_SLACK_MARGIN"] = hold_margin
    output.mkdir(parents=True, exist_ok=False)

    def run(tag, checkpoint, step, corner):
        config = dict(base)
        # Single-step flows have no repeated-ID or --to ambiguity.
        # Preserve legacy merged-config parsing (e.g. string DIE_AREA).
        config["meta"] = {"version": base.get("meta", {}).get("version", 1), "flow": [step]}
        config["OPENROAD_THREADS"] = 4
        config["PNR_CORNERS"] = [corner]
        config["RSZ_CORNERS"] = list(repair_corners or [CORNERS[1]])
        if step == "OpenROAD.ResizerTimingPostGRT" and repair_corners:
            config["PNR_CORNERS"] = list(repair_corners)
        config["RUN_POST_GRT_RESIZER_TIMING"] = True
        path = config_path.with_name(f"config_timing_{tag}.json")
        path.write_text(json.dumps(config, indent=2) + "\n")
        root = output / tag
        # LibreLane's CLI validates --force-run-dir before starting the flow.
        root.mkdir()
        subprocess.run([
            sys.executable, "-m", "librelane", "--pdk-root", pdk_root,
            "--docker-no-tty", "--dockerized", "--pdk", "ihp-sg13cmos5l",
            "--manual-pdk", "--run-tag", tag, "--force-run-dir", str(root),
            "--hide-progress-bar", "--with-initial-state", str(checkpoint), str(path),
        ], check=True)
        resolved = json.loads((root / "resolved.json").read_text())
        if resolved["PNR_CORNERS"] != config["PNR_CORNERS"] or resolved["OPENROAD_THREADS"] != 4:
            raise ValueError(f"Resolved corner/thread mismatch in {root}")
        # STA-only configs omit routing variables; the repair flow uses them.
        if step == "OpenROAD.ResizerTimingPostGRT" and float(resolved["GRT_ADJUSTMENT"]) != 0.16:
            raise ValueError(f"Resolved GRT adjustment mismatch in {root}")
        if step == "OpenROAD.ResizerTimingPostGRT" and hold_margin is not None:
            if resolved["GRT_RESIZER_HOLD_SLACK_MARGIN"] != hold_margin:
                raise ValueError("Resolved hold target differs from the selected experiment")
        if list(root.glob("*-openroad-detailedrouting")):
            raise ValueError(f"Unexpected detailed routing in {root}")
        return root

    results = {"before_state": str(before), "sdc": base.get("PNR_SDC_FILE"), "corners": {}}
    for corner in CORNERS:
        root = run(f"before-{corner}", before, "OpenROAD.STAMidPNR", corner)
        results["corners"][corner] = {"before": fresh_metrics(root, "openroad-stamidpnr", corner)}
    if repaired is None:
        root = run("repair", before, "OpenROAD.ResizerTimingPostGRT", CORNERS[1])
        states = list(root.glob("*-openroad-resizertimingpostgrt/state_out.json"))
        if len(states) != 1:
            raise ValueError(f"Expected one repaired checkpoint: {states}")
        repaired = states[0]
        results["repair_metrics"] = json.loads(
            states[0].with_name("or_metrics_out.json").read_text()
        )
    results["after_state"] = str(repaired)
    for corner in CORNERS:
        root = run(f"after-{corner}", repaired, "OpenROAD.STAMidPNR", corner)
        metrics = fresh_metrics(root, "openroad-stamidpnr", corner)
        row = results["corners"][corner]
        row["after"] = metrics
        row["delta"] = {
            key: metrics[key] - value for key, value in row["before"].items()
            if key in metrics and isinstance(value, (int, float))
            and isinstance(metrics[key], (int, float))
        }
        for kind in ("setup", "hold"):
            key = f"timing__{kind}__ws__corner:{corner}"
            print(f"{corner} {kind} WS: {row['before'][key]} -> {metrics[key]} ns")
    (output / "comparison.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("src/config_merged.json"))
    parser.add_argument("--before", type=Path, default=Path("runs/wokwi/39-openroad-globalrouting/state_out.json"))
    parser.add_argument("--repaired", type=Path, help="Reuse a saved resizer state instead of repeating repair")
    parser.add_argument("--output", type=Path, default=Path("runs/postgrt-timing"))
    parser.add_argument("--pdk-root", required=True)
    parser.add_argument("--sdc", type=Path, help="Use the same explicit constraint file for both checkpoints")
    parser.add_argument("--setup-margin", type=float, help="Isolated setup-repair margin in ns")
    args = parser.parse_args()
    screen(args.config, args.before, args.output, args.pdk_root, args.repaired, args.sdc, args.setup_margin)
