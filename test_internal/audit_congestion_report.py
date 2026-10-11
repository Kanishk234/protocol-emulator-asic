"""Strict read-only parser for pinned OpenROAD native TR congestion markers.

Marker coordinates retain their native decimal text. Layer '-' is unset; planar
marker totals must not be equated with the per-layer final GRT overflow table.
"""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

NUMBER = r"-?\d+(?:\.\d+)?"
BBOX = re.compile(r"\s*bbox = \((" + NUMBER + r"), (" + NUMBER + r")\) - \((" + NUMBER + r"), (" + NUMBER + r")\) on Layer (\S+)\s*")
COMMENT = re.compile(r"\s*comment: capacity:(\d+) usage:(\d+) overflow:(\d+)\s*")
KINDS = {"violation type: Horizontal congestion": "horizontal",
         "violation type: Vertical congestion": "vertical"}
TR_WRITER = "https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/odb/src/db/dbMarker.cpp#L215"


def parse(text):
    lines = text.splitlines()
    if len(lines) % 4:
        raise ValueError("Incomplete four-line native congestion marker")
    markers = []
    for index in range(0, len(lines), 4):
        kind, sources, comment, box = lines[index:index + 4]
        if kind not in KINDS:
            raise ValueError("Unsupported native violation type")
        if not sources.startswith("\tsrcs:"):
            raise ValueError("Missing native source line")
        nets = sources.split(":", 1)[1].split()
        if any(not token.startswith("net:") or len(token) <= 4 for token in nets):
            raise ValueError("Unsupported congestion marker source")
        values = COMMENT.fullmatch(comment)
        coordinates = BBOX.fullmatch(box)
        if not values or not coordinates:
            raise ValueError("Unsupported native comment or bounding box")
        capacity, usage, overflow = map(int, values.groups())
        if usage - capacity != overflow or overflow <= 0:
            raise ValueError("Invalid native overflow arithmetic")
        raw = list(coordinates.groups()[:4])
        x0, y0, x1, y1 = map(Decimal, raw)
        if x1 <= x0 or y1 <= y0:
            raise ValueError("Degenerate or inverted marker box")
        markers.append({"direction": KINDS[kind], "capacity": capacity,
                        "usage": usage, "overflow": overflow,
                        "bbox_native_decimal_text": raw, "layer_native": coordinates[5],
                        "source_nets_native": [name[4:] for name in nets]})
    return markers


def audit(path, expected=None):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected is not None and digest != expected:
        raise ValueError("Native report digest does not match diagnostic manifest")
    markers = parse(raw.decode("utf-8"))
    totals = {}
    for direction in ("horizontal", "vertical"):
        subset = [row for row in markers if row["direction"] == direction]
        totals[direction] = {"markers": len(subset),
                             "planar_marker_overflow_sum": sum(row["overflow"] for row in subset),
                             "zero_capacity_markers": sum(row["capacity"] == 0 for row in subset)}
    net_counts = Counter(name for row in markers for name in set(row["source_nets_native"]))
    return {"source_sha256": digest, "source_bytes": len(raw),
            "scope": "native planar congestion markers; no routing/timing acceptance",
            "coordinate_unit": "micrometers; native decimal text retained without conversion",
            "coordinate_unit_source": TR_WRITER,
            "layer_dash_means": "unset, not a physical routing layer",
            "marker_count": len(markers), "direction_summary": totals,
            "net_marker_counts": dict(sorted(net_counts.items(), key=lambda item: (-item[1], item[0]))),
            "markers": markers}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--sha256", help="Require exact report digest from native diagnostic.json")
    args = parser.parse_args()
    print(json.dumps(audit(args.report, args.sha256), indent=2))
