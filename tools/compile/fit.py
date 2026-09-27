"""Design-set resource check on the real compile flow's synthesis (tile library cells, carry
chain, complex flip-flops), before a fabric large enough to place them exists.

    python -m compile.fit [-o build/fit]

Same designs and parameters as tools/profiling (docs/reports/profiling.md), so the numbers
compare with its LUT4 column. Sanity check: counter4 (tools/compile/examples), whose LC count
nextpnr reports after place and route.
"""

import argparse
import json
from pathlib import Path

from compile.compile import ROOT, synth_only
from profiling.workload import PROTOCOLS


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", default=str(ROOT / "build" / "fit"))
    a = ap.parse_args(argv)
    out = Path(a.out)
    rows = {}
    rows["counter4 (check)"] = synth_only([ROOT / "tools/compile/examples/counter4.v"], "counter4",
                                          out / "counter4")
    for p in PROTOCOLS:
        rows[p.name] = synth_only([ROOT / f for f in p.files], p.top, out / p.name, p.params)
    (out / "fit.json").write_text(json.dumps(rows, indent=2) + "\n")
    print("| Design | LUTs (of which carry) | FFs | LCs (est.) | IO | other cells |")
    print("|---|---|---|---|---|---|")
    for name, r in rows.items():
        print(f"| {name} | {r['luts']} ({r['carry_luts']}) | {r['ffs']} | **{r['lcs']}** | {r['io']} | "
              f"{', '.join(r['other_cells']) or '-'} |")


if __name__ == "__main__":
    main()
