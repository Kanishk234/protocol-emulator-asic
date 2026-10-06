#!/usr/bin/env python3
"""Summarize native TritonRoute markers, preserving their actual layer names.

Counts describe markers, not independent electrical faults or signoff results.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import re


def summarize(path, macro_bbox, bin_um=50):
    source = Path(path).read_text()
    blocks = source.split("violation type:")[1:]
    layers, types, regions, nets, hotspots = (Counter() for _ in range(5))
    net_groups = Counter()
    xmin, ymin, xmax, ymax = macro_bbox
    for block in blocks:
        match = re.search(r"bbox = \(([-\d.]+), ([-\d.]+)\) - "
                          r"\(([-\d.]+), ([-\d.]+)\) on Layer (\S+)", block)
        if match is None:
            raise ValueError(f"Unrecognized marker in {path}: {block[:200]}")
        x1, y1, x2, y2 = map(float, match.groups()[:4])
        x, y = (x1 + x2) / 2, (y1 + y2) / 2
        region = ("west" if x < xmin else "east" if x > xmax else
                  "south" if y < ymin else "north" if y > ymax else "macro")
        regions[region] += 1
        layers[match[5]] += 1
        types[block.splitlines()[0].strip()] += 1
        marker_nets = set(re.findall(r"net:(\S+)", block))
        nets.update(marker_nets)
        net_groups[tuple(sorted(marker_nets))] += 1
        hotspots[f"{int(x // bin_um) * bin_um:g},{int(y // bin_um) * bin_um:g}"] += 1
    return {
        "report": str(Path(path).resolve()), "markers": len(blocks),
        "macro_bbox_um": list(macro_bbox), "by_layer": dict(layers),
        "by_type": dict(types), "by_region_center": dict(regions),
        "top_nets_marker_incidence": nets.most_common(15),
        "top_net_groups_marker_incidence": net_groups.most_common(15),
        "hotspots_lower_left_um": hotspots.most_common(15), "bin_um": bin_um,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--macro-bbox", nargs=4, type=float, required=True,
                        metavar=("XMIN", "YMIN", "XMAX", "YMAX"))
    parser.add_argument("--bin-um", type=float, default=50)
    args = parser.parse_args()
    if args.bin_um <= 0 or args.macro_bbox[0] >= args.macro_bbox[2] or args.macro_bbox[1] >= args.macro_bbox[3]:
        parser.error("Require positive bins and an ordered macro bounding box")
    print(json.dumps(summarize(args.report, args.macro_bbox, args.bin_um), indent=2))
