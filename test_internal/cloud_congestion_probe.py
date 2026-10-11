"""Read-only placement-origin diagnostic on actual paired shell GRT artifacts.

No EDA, netlist edits or acceptance decisions. Origins are NOT physical pin
locations: the HPWL figures below are locality proxies in database units.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re

from cloud_cfg_fanout import parse_census, verify_connections
from cloud_fanout_preflight import sha


def net_origins(instances, pins):
    nets = defaultdict(set)
    ports = defaultdict(list)
    for (kind, name), (_, signal, net) in pins.items():
        if signal in ("POWER", "GROUND") or net == "NULL":
            continue
        if kind == "PORT":
            ports[net].append(name)
        else:
            inst = name.rsplit("/", 1)[0]
            if inst not in instances:
                raise ValueError("Terminal refers to absent instance")
            nets[net].add(inst)
    result = {}
    for net, names in nets.items():
        coords = [tuple(map(int, instances[name][1].split())) for name in names]
        if any(len(point) != 2 for point in coords):
            raise ValueError("Invalid instance origin")
        bbox = [min(p[0] for p in coords), min(p[1] for p in coords),
                max(p[0] for p in coords), max(p[1] for p in coords)]
        result[net] = {"origin_bbox_dbu": bbox,
                       "origin_hpwl_dbu": bbox[2] - bbox[0] + bbox[3] - bbox[1],
                       "instances": sorted(names), "excluded_top_ports": sorted(ports[net]),
                       "includes_macro_origin": "u_fabric" in names}
    return result


def analyze(directory):
    source = {case: directory / (case + "_before.tsv")
              for case in ("cluster8", "ten_buffers")}
    texts = {case: path.read_text() for case, path in source.items()}
    contract = verify_connections(texts["cluster8"], texts["ten_buffers"])
    parsed = {case: parse_census(text) for case, text in texts.items()}
    nets = {case: net_origins(*values) for case, values in parsed.items()}
    moved = []
    old, new = parsed["cluster8"][0], parsed["ten_buffers"][0]
    for name, original in old.items():
        before = tuple(map(int, original[1].split()))
        after = tuple(map(int, new[name][1].split()))
        distance = sum(abs(a - b) for a, b in zip(before, after))
        if distance:
            moved.append({"instance": name, "before_dbu": before, "after_dbu": after,
                          "manhattan_displacement_dbu": distance,
                          "clock_name_heuristic": name.startswith(("clk", "delaybuf"))})
    logs = {case: (directory / (case + ".log")).read_text() for case in source}
    ndr = {case: sorted(set(re.findall(
        r"congestion\)\s+for net:\s+(\S+)", log))) for case, log in logs.items()}
    traced = sorted(set().union(*map(set, ndr.values())))
    delta = []
    for net in sorted(set(nets["cluster8"]) & set(nets["ten_buffers"])):
        a, b = nets["cluster8"][net], nets["ten_buffers"][net]
        if a["instances"] != b["instances"]:
            continue  # Buffer-split nets require contracted-pin geometric analysis.
        if a["includes_macro_origin"] or a["excluded_top_ports"]:
            continue  # Their real pin coordinates are absent from this census.
        change = b["origin_hpwl_dbu"] - a["origin_hpwl_dbu"]
        if change:
            delta.append({"net": net, "origin_hpwl_delta_dbu": change,
                          "before": a, "after": b})
    return {"scope": "read-only locality proxies, not routing or timing acceptance",
            "source_census_sha256": {case: sha(path) for case, path in source.items()},
            "contract": contract, "ndr_fallback_nets_from_actual_logs": ndr,
            "clock_heuristic_moved_instances": [row for row in moved if row["clock_name_heuristic"]],
            "largest_moved_instances": sorted(moved, key=lambda r: -r["manhattan_displacement_dbu"])[:20],
            "ndr_fallback_origin_locality": {net: {case: nets[case].get(net) for case in source}
                                             for net in traced},
            "largest_same_terminal_origin_hpwl_increases": sorted(delta, key=lambda r: -r["origin_hpwl_delta_dbu"])[:20],
            "added_buffer_origins": {name: value for name, value in new.items() if name not in old}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.artifact), indent=2))
