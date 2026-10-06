"""Compare native, binary and one-hot FSM mapping on copied design-set RTL.

Frozen protocol files and chip RTL are never edited. Generated copies add
only a Yosys fsm_encoding attribute to the existing state register.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from compile.compile import CompileError, compile_design


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        ap.error("Use a fresh output directory")
    if os.environ.get("WARP_MIN_CTRL", "4") != "4":
        ap.error("Keep WARP_MIN_CTRL=4 for this matched FSM comparison")
    args.out.mkdir(parents=True)
    rows = []
    for name in ("spi_ctrl", "i2c_ctrl"):
        base = ROOT / "protocols" / name
        for encoding in ("native", "binary", "one-hot"):
            work = args.out / name / encoding
            sources = []
            changed = 0
            for original in sorted(base.glob("*.v")):
                text = original.read_text()
                if encoding != "native":
                    text, count = re.subn(r"(?m)^(\s*)(reg\s+\[[^\]\n]+\]\s+state\s*;)",
                        lambda m: f'{m[1]}(* fsm_encoding = "{encoding}" *) {m[2]}', text)
                    changed += count
                dst = work / "sources" / original.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(text)
                sources.append(dst)
            if encoding != "native" and changed != 1:
                raise RuntimeError(f"Expected exactly one state register in {name}; found {changed}")
            row = {"protocol": name, "encoding": encoding, "seed": 1}
            try:
                bitfile, report = compile_design(sources, base / "pins.yaml",
                    ROOT / "arch/warp_g1", work, seed=1)
                row.update(fits=True, utilisation=report["utilisation"],
                    fmax_mhz_model=report["fmax_mhz"], bitfile=str(bitfile), tools=report["tools"])
            except CompileError as exc:
                row.update(fits=False, error=str(exc))
            rows.append(row)
            (args.out / "summary.json").write_text(json.dumps({
                "arch": "warp_g1", "min_ctrl": 4, "timing_is_model_only": True,
                "loaded_simulation_verified": False, "results": rows}, indent=2) + "\n")
            print(json.dumps(row), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
