"""Read-only reset-tie locality audit from native census/geometry/markers.

Interior row gaps are conservative placement candidates, never a legality
proof: native row extents, obstructions, pin access and power still need EDA.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from audit_congestion_report import parse
from cloud_cfg_fanout import parse_census
from cloud_hotspot_padding import boxes


def audit(census, geometry, congestion):
    instances, pins = parse_census(census.read_text())
    dbu, site, shapes = boxes(geometry.read_text())
    if (dbu, site) != (1000, 480) or set(instances) != set(shapes):
        raise ValueError("Checkpoint geometry/census scope differs")
    markers = parse(congestion.read_text())
    memberships = defaultdict(list)
    for index, marker in enumerate(markers):
        for net in set(marker["source_nets_native"]):
            memberships[net.replace("\\", "")].append(index)
    nets = defaultdict(list)
    for key, value in pins.items():
        if key[0] == "PIN":
            nets[value[-1].replace("\\", "")].append((key[1], value[0]))
    rows = defaultdict(list)
    for name, (kind, box) in shapes.items():
        if kind == "CORE":
            rows[box[1]].append((box[0], box[2], name))
    gaps = []
    for bottom, cells in rows.items():
        cells.sort()
        right = cells[0][1]
        for left, end, _ in cells[1:]:
            if left - right >= 1920:
                gaps.append((right, left, bottom))
            right = max(right, end)
    resets = []
    for net, endpoints in nets.items():
        if len(endpoints) != 2:
            continue
        sources = [p for p, direction in endpoints if direction == "OUTPUT"
                   and p.endswith("/L_HI")]
        loads = [p for p, direction in endpoints if direction == "INPUT"
                 and p.endswith("/RESET_B")]
        if len(sources) != 1 or len(loads) != 1:
            continue
        tie, receiver = sources[0].rsplit("/", 1)[0], loads[0].rsplit("/", 1)[0]
        if instances[tie][0] != "sg13cmos5l_tiehi":
            raise ValueError("Unexpected reset tie master")
        tb, rb = shapes[tie][1], shapes[receiver][1]
        candidates = []
        for left, right, bottom in gaps:
            if abs(bottom - rb[1]) > 20000 or (bottom - tb[1]) % 7560:
                continue
            # Aligned interior slots only. Bbox center distance is a proxy,
            # deliberately not a routed/pin-to-pin distance claim.
            first = ((left + site - 1) // site) * site
            last = ((right - 1920) // site) * site
            if first > last:
                continue
            target = min(last, max(first, ((rb[0] + rb[2] - 1920) // (2 * site)) * site))
            proxy = abs(2 * target + 1920 - rb[0] - rb[2]) / 2 + abs(bottom - rb[1])
            candidates.append({"bbox_dbu": [target, bottom, target + 1920, bottom + 3780],
                               "bbox_center_manhattan_proxy_um": proxy / dbu})
        old_proxy = abs(tb[0] + tb[2] - rb[0] - rb[2]) / 2 + abs(tb[1] - rb[1])
        resets.append({"net": net, "tie": tie, "receiver": receiver,
                       "tie_bbox_dbu": tb, "receiver_bbox_dbu": rb,
                       "row_separation_um": abs(tb[1] - rb[1]) / dbu,
                       "bbox_center_manhattan_proxy_um": old_proxy / dbu,
                       "marker_indices": memberships.get(net, []),
                       "conservative_same_power_phase_slots_within_20um_receiver_row":
                           sorted(candidates, key=lambda c: c["bbox_center_manhattan_proxy_um"]),
                       "improving_slot_count": sum(c["bbox_center_manhattan_proxy_um"] < old_proxy / dbu
                                                   for c in candidates)})
    affected = [r for r in resets if r["marker_indices"]]
    return {"scope": "read-only placement proxy; no native legality or routing acceptance",
            "inputs_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (census, geometry, congestion)},
            "reset_tie_count": len(resets),
            "reset_ties_row_separation_ge_30um": sum(r["row_separation_um"] >= 30 for r in resets),
            "maximum_reset_row_separation_um": max(r["row_separation_um"] for r in resets),
            "marker_associated_reset_tie_count": len(affected),
            "marker_associated_without_improving_interior_slot_count":
                sum(r["improving_slot_count"] == 0 for r in affected),
            "marker_associated_reset_ties": sorted(affected, key=lambda r: (-len(r["marker_indices"]), r["net"]))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("census", type=Path)
    parser.add_argument("geometry", type=Path)
    parser.add_argument("congestion", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.census, args.geometry, args.congestion), indent=2))
