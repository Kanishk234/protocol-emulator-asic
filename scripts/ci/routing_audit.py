#!/usr/bin/env python3
"""Summarize intermediate OpenROAD DRC markers; never infer route signoff."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re


def audit(report, placement=None, bin_size=50):
    if bin_size <= 0:
        raise ValueError("Bin size must be positive")
    content = Path(report).read_text()
    pattern = (r"violation type: (.*?)\n\s*srcs: (.*?)\n"
               r"\s*bbox = \((.*?), (.*?)\) - \((.*?), (.*?)\) on Layer (\S+)")
    records = re.findall(pattern, content)
    declared = content.count("violation type:")
    if len(records) != declared or not records:
        raise ValueError(f"Parsed {len(records)} of {declared} markers; refuse incomplete audit")
    bins, names = Counter(), Counter()
    for _, sources, x0, y0, x1, y1, _ in records:
        x, y = (float(x0) + float(x1)) / 2, (float(y0) + float(y1)) / 2
        bins[(math.floor(x / bin_size) * bin_size,
              math.floor(y / bin_size) * bin_size)] += 1
        # Count each named net once per marker, even if both shapes belong to it.
        names.update(sorted(set(re.findall(r"net:(\S+)", sources))))
    result = {
        "report": str(report), "marker_records": len(records),
        "interpretation": "Intermediate marker records, possibly overlapping; not final DRC",
        "types": dict(Counter(r[0] for r in records)),
        "layers": dict(Counter(r[6] for r in records)),
        "bin_size_um": bin_size,
        "bins": [{"x_um": x, "y_um": y, "records": n}
                 for (x, y), n in bins.most_common()],
        "nets": [{"name": name, "marker_records": n}
                 for name, n in sorted(names.items(), key=lambda row: (-row[1], row[0]))],
    }
    if placement is not None:
        text = Path(placement).read_text()
        units = int(re.search(r"UNITS DISTANCE MICRONS (\d+)", text)[1])
        components = text.split("COMPONENTS ", 1)[1].split("END COMPONENTS", 1)[0]
        origins = {name: (cell, int(x) / units, int(y) / units)
                   for name, cell, x, y in re.findall(
                       r"^\s*- (\S+) (\S+)[^;]*?\+ (?:PLACED|FIXED) \( (\d+) (\d+) \)",
                       components, re.M)}
        nets = text.split("\nNETS ", 1)[1].split("END NETS", 1)[0]
        blocks = {b.split()[0]: b for b in re.split(r"\n\s*- ", nets)[1:]}
        for row in result["nets"]:
            pins = []
            for inst, pin in re.findall(r"\( (\S+) (\S+) \)", blocks.get(row["name"], "")):
                if inst in origins:
                    cell, x, y = origins[inst]
                    pins.append({"instance": inst, "pin": pin, "cell": cell,
                                 "origin_x_um": x, "origin_y_um": y})
            row["placed_connections"] = pins
        result["placement"] = str(placement)
        result["coordinate_note"] = "Component origins, not pin coordinates or routed wire lengths"
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--placement", type=Path)
    parser.add_argument("--bin-size", type=int, default=50)
    args = parser.parse_args()
    print(json.dumps(audit(args.report, args.placement, args.bin_size), indent=2))
