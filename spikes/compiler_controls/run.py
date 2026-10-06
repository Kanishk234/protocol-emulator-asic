"""Screen shared enable/reset mapping thresholds on the unchanged G1 design set.

Run in the project venv. Each compiler is a separate process because the
existing WARP_MIN_CTRL setting is read at module import. Timing is a model;
successful compilation alone is not loaded-bitstream verification.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--thresholds", type=int, nargs="+", default=[2, 4, 8])
    args = ap.parse_args()
    if args.out.exists():
        ap.error("Use a fresh output directory to avoid stale evidence")
    if any(value < 1 for value in args.thresholds):
        ap.error("Thresholds must be positive")
    args.out.mkdir(parents=True)
    rows = []
    for name in ("uart", "spi_ctrl", "i2c_ctrl"):
        base = ROOT / "protocols" / name
        for threshold in args.thresholds:
            work = (args.out / name / f"minctrl{threshold}").resolve()
            work.mkdir(parents=True)
            env = dict(os.environ, WARP_MIN_CTRL=str(threshold),
                       PYTHONPATH=str(ROOT / "tools"))
            cmd = [sys.executable, "-m", "compile.compile",
                   *map(str, sorted(base.glob("*.v"))), "--pins", str(base / "pins.yaml"),
                   "--arch", str(ROOT / "arch/warp_g1"), "--seed", "1", "-o", str(work)]
            with (work / "compile.log").open("w") as log:
                result = subprocess.run(cmd, cwd=ROOT, env=env, stdout=log,
                                        stderr=subprocess.STDOUT)
            row = {"protocol": name, "min_ctrl": threshold, "seed": 1,
                   "fits": result.returncode == 0, "exit_code": result.returncode,
                   "log": str(work / "compile.log")}
            if row["fits"]:
                report = json.loads((work / "report.json").read_text())
                row.update(utilisation=report["utilisation"],
                           fmax_mhz_model=report["fmax_mhz"], tools=report["tools"],
                           words=report["words"])
            rows.append(row)
            (args.out / "summary.json").write_text(json.dumps({
                "arch": "warp_g1", "timing_is_model_only": True,
                "loaded_simulation_verified": False, "results": rows}, indent=2) + "\n")
            print(json.dumps(row), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
