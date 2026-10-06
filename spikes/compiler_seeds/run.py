"""Compare deterministic placement seeds on frozen G1; model timing, not signoff."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from compile.compile import CompileError, compile_design


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    args = ap.parse_args()
    if args.out.exists():
        ap.error("Use a fresh output directory to avoid stale evidence")
    args.out.mkdir(parents=True)
    rows = []
    for protocol in ("uart", "spi_ctrl", "i2c_ctrl"):
        base = ROOT / "protocols" / protocol
        for seed in args.seeds:
            row = {"protocol": protocol, "seed": seed}
            try:
                bitfile, report = compile_design(sorted(base.glob("*.v")),
                    base / "pins.yaml", ROOT / "arch/warp_g1",
                    args.out / protocol / f"seed{seed}", seed=seed)
                row.update(fits=True, fmax_mhz_model=report["fmax_mhz"],
                    utilisation=report["utilisation"], bitfile=str(bitfile))
            except CompileError as exc:
                row.update(fits=False, error=str(exc))
            rows.append(row)
            (args.out / "summary.json").write_text(json.dumps({
                "arch": "warp_g1", "timing_is_model_only": True,
                "loaded_simulation_verified": False, "results": rows}, indent=2) + "\n")
            print(json.dumps(row), flush=True)
    return 0 if all(row["fits"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
