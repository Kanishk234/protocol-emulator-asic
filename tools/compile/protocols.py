"""Compile every design-set protocol (protocols/*/pins.yaml) onto the current architecture and
report fit, resources and timing (PHASE2 "Protocols on G0", docs/reports/g0_results.md).

    python -m compile.protocols [-o build/protocols]

A design that does not fit fails in place and route; its demand is then taken from the
synthesized netlist (cell_estimate, which matches nextpnr's packing on the designs that place).
"""

import argparse
import json
from pathlib import Path

import yaml

from compile.compile import (ROOT, CompileError, cell_estimate, compile_design, current_arch,
                             load_arch)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", default=str(ROOT / "build" / "protocols"))
    ap.add_argument("--arch", default=str(current_arch()))
    ap.add_argument("--only", nargs="*", help="protocol names (default: all)")
    ap.add_argument("--require", nargs="*", default=[], metavar="NAME",
                    help="exit 1 unless these protocols place and route (CI: the fallback set)")
    ap.add_argument("--set", nargs="*", default=[], metavar="NAME=VALUE",
                    help="override a parameter of every design (e.g. PRIMS=0 for a fabric without primitives)")
    a = ap.parse_args(argv)
    arch = Path(a.arch).resolve()
    overrides = dict(kv.split("=", 1) for kv in a.set)
    meta, _ = load_arch(arch)
    rows = {}
    for pins in sorted((ROOT / "protocols").glob("*/pins.yaml")):
        name = pins.parent.name
        if a.only and name not in a.only:
            continue
        sources = sorted(p for p in pins.parent.glob("*.v"))
        out = Path(a.out) / name
        spec = yaml.safe_load(pins.read_text())
        spec["params"] = dict(spec.get("params") or {},
                              **{k: v for k, v in overrides.items() if k in (spec.get("params") or {})})
        try:
            path, rep = compile_design(sources, pins, arch, out, set_params=spec["params"])
            est = cell_estimate(out / "design.json", "warp_top")
            rows[name] = {"fits": True, "lcs": rep["utilisation"].get("FABULOUS_LC", {}).get("used"),
                          "io": rep["utilisation"].get("IOBUF", {}).get("used"),
                          "ffs": est["ffs"], "luts": est["luts"], "carry": est["carry_luts"],
                          "timers": est["timers"], "shifts": est["shifts"],
                          "fmax_mhz": rep["fmax_mhz"], "words": rep["words"], "params": spec.get("params")}
        except CompileError as e:
            est = cell_estimate(out / "design.json", "warp_top") if (out / "design.json").exists() else {}
            rows[name] = {"fits": False, "lcs": est.get("lcs"), "ffs": est.get("ffs"),
                          "luts": est.get("luts"), "carry": est.get("carry_luts"), "io": est.get("io"),
                          "timers": est.get("timers"), "shifts": est.get("shifts"),
                          "error": str(e).splitlines()[-1][:160], "params": spec.get("params")}
    (Path(a.out) / "results.json").write_text(json.dumps({"arch": meta["name"], "luts": meta["luts"],
                                                          "results": rows}, indent=2) + "\n")
    print(f"| Protocol | Fits {meta['name']} ({meta['luts']} LCs)? | LCs | LUTs (carry) | FFs | timers, shifts | IO cells | Fmax (slow corner) |")
    print("|---|---|---|---|---|---|---|---|")
    for n, r in rows.items():
        fmax = f"{r['fmax_mhz']:.1f} MHz" if r.get("fmax_mhz") else "-"
        print(f"| {n} | {'yes' if r['fits'] else '**no**'} | {r['lcs']} | {r['luts']} ({r['carry']}) | "
              f"{r['ffs']} | {r.get('timers', 0)}, {r.get('shifts', 0)} | {r['io']} | {fmax} |")
    for n, r in rows.items():
        if not r["fits"]:
            print(f"{n}: {r['error']}")
    missing = [n for n in a.require if not rows.get(n, {}).get("fits")]
    if missing:
        print(f"error: required protocols do not fit {meta['name']}: {', '.join(missing)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
