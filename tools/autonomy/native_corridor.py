"""Strict read-only audit of warp-native-corridor-v1; never infer background usage.

Reconciliation compares weighted STEP MULTISETS with every raw native3D edge.
Agreement does not authenticate a WARP checkpoint, terminals, or physical routing.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

MAX_BYTES = 256 * 1024 * 1024
MAX_ROWS = 3_000_000
MAX_EDGES = 2_000_000
MAX_COUNT = 1_000_000
Edge = tuple[str, int, int, int]


class FormatError(ValueError):
    """Incomplete, inconsistent or unsupported native export."""


def _int(token: str, where: str, lo: int = 0, hi: int = MAX_COUNT) -> int:
    if len(token) > 20 or token == "-0" or not re.fullmatch(r"-?(?:0|[1-9][0-9]*)", token):
        raise FormatError(f"{where}: require canonical integer, got {token!r}")
    value = int(token)
    if not lo <= value <= hi:
        raise FormatError(f"{where}: integer outside [{lo},{hi}]")
    return value


class _Rows:
    def __init__(self, text: str):
        if not text or not text.endswith("\n") or "\r" in text or "\x00" in text:
            raise FormatError("require complete LF-terminated TSV without CR/NUL")
        self.rows = iter(text.split("\n")[:-1])
        self.number = 0

    def next(self) -> list[str]:
        try:
            row = next(self.rows)
        except StopIteration as exc:
            raise FormatError("unexpected end of native export") from exc
        self.number += 1
        if self.number > MAX_ROWS or not row:
            raise FormatError("empty row or row limit exceeded")
        return row.split("\t")

    def take(self, kind: str, count: int) -> list[str]:
        row = self.next()
        if len(row) != count or row[0] != kind:
            raise FormatError(f"row{self.number}: expected {kind} with {count} fields")
        return row


@dataclass
class Snapshot:
    sha256: str
    grid: tuple[int, int, int, int, int, int]
    edges: dict[Edge, tuple[int, int, int, int]]
    nets: dict[int, dict]
    empty_slots: list[int]
    steps: int


def parse_bytes(raw: bytes) -> Snapshot:
    if len(raw) > MAX_BYTES:
        raise FormatError("native export exceeds byte limit")
    try:
        rows = _Rows(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise FormatError("native export is not UTF-8") from exc
    for expected in [("SCHEMA", "warp-native-corridor-v1"),
                     ("INDEXING", "zero_based_fast_route_layers_and_grid"),
                     ("MODEL_GATE", "usage_ledger_verified", "false"),
                     ("VIA_MODEL", "global_route_steps_only_no_physical_cut_capacity")]:
        if rows.take(expected[0], len(expected)) != list(expected):
            raise FormatError(f"unsupported {expected[0]} contract")
    grid_row = rows.take("GRID", 7)
    nx, ny = (_int(grid_row[i], "grid dimension", 2, 32767) for i in (1, 2))
    nl = _int(grid_row[3], "grid layers", 1, 64)
    ox, oy = (_int(grid_row[i], "grid origin", -(2**31), 2**31 - 1) for i in (4, 5))
    pitch = _int(grid_row[6], "grid pitch", 1, 2**31 - 1)
    edge_count = nl * ((nx - 1) * ny + nx * (ny - 1))
    if edge_count > MAX_EDGES:
        raise FormatError("raw edge census exceeds limit")
    edges = {}
    # Requiring native emission order simultaneously detects missing, duplicate,
    # out-of-bounds, out-of-order and omitted real boundary/nonpreferred edges.
    for layer in range(nl):
        for direction, xmax, ymax in (("H", nx - 1, ny), ("V", nx, ny - 1)):
            for y in range(ymax):
                for x in range(xmax):
                    row = rows.take("EDGE", 9)
                    key = (row[1], _int(row[2], "edge layer"), _int(row[3], "edge x"), _int(row[4], "edge y"))
                    if key != (direction, layer, x, y):
                        raise FormatError(f"raw edge census/order mismatch at {key}")
                    edges[key] = tuple(_int(v, "uint16 resource", 0, 65535) for v in row[5:])
    nets, empty_slots = {}, []
    names, database_ids = set(), set()
    slot = step_count = 0
    while True:
        row = rows.next()
        if row[0] == "COMPLETE":
            if len(row) != 4 or [_int(v, "footer") for v in row[1:]] != [slot, len(nets), step_count]:
                raise FormatError("completion footer census mismatch")
            try:
                next(rows.rows)
            except StopIteration:
                break
            raise FormatError("trailing data after completion")
        if slot >= MAX_COUNT:
            raise FormatError("net slot limit exceeded")
        if row[0] == "EMPTY_SLOT":
            if len(row) != 2 or _int(row[1], "empty slot") != slot:
                raise FormatError("invalid empty slot/order")
            empty_slots.append(slot)
            slot += 1
            continue
        if row[0] != "NET" or len(row) != 11 or _int(row[1], "net slot") != slot:
            raise FormatError("invalid net slot/order/field count")
        dbid = _int(row[2], "database net ID", 1, 2**32 - 1)
        name = row[3]
        if not name or any(ord(c) < 32 for c in name) or name in names or dbid in database_ids:
            raise FormatError("invalid or duplicate native net name/database ID")
        names.add(name)
        database_ids.add(dbid)
        clock, soft = (_int(row[i], "native Boolean", 0, 1) for i in (4, 5))
        scalar = _int(row[6], "scalar edge cost", 0, 127)
        minimum, maximum = (_int(row[i], "planar layer", 0, nl - 1) for i in (7, 8))
        if minimum > maximum:
            raise FormatError("inverted planar layer interval")
        pins_count = _int(row[10], "pin count")
        driver = _int(row[9], "driver index", -1, max(-1, pins_count - 1))
        demands = []
        for layer in range(nl):
            r = rows.take("DEMAND", 4)
            if [_int(v, "demand index") for v in r[1:3]] != [slot, layer]:
                raise FormatError("demand layer census/order mismatch")
            demands.append(_int(r[3], "layer edge cost", 0, 127))
        # Pinned FrNet::getLayerEdgeCost returns1 on EVERY layer whenever
        # is_soft_ndr_ is true, independently of the scalar2D getEdgeCost.
        # Never infer the converse or require scalar==1: reset can preserve
        # soft-NDR while assigning a new, nonunit scalar cost.
        if soft and any(cost != 1 for cost in demands):
            raise FormatError("soft-NDR net must export unit demand on every layer")
        pins = []
        for pin in range(pins_count):
            r = rows.take("PIN", 6)
            if [_int(v, "pin index") for v in r[1:3]] != [slot, pin]:
                raise FormatError("pin census/order mismatch")
            pins.append((_int(r[3], "pin x", 0, nx - 1), _int(r[4], "pin y", 0, ny - 1),
                         _int(r[5], "pin layer", 0, nl - 1)))
        r = rows.take("TREE", 5)
        if _int(r[1], "tree net") != slot:
            raise FormatError("tree net mismatch")
        terminals = _int(r[2], "tree terminal count", 0, pins_count)
        tree_nodes = _int(r[3], "tree node count", terminals)
        tree_edges_count = _int(r[4], "tree edge count")
        contributions = Counter()
        vias = 0
        tree_edges = []
        for edge in range(tree_edges_count):
            r = rows.take("TREE_EDGE", 10)
            if [_int(v, "tree edge index") for v in r[1:3]] != [slot, edge]:
                raise FormatError("tree edge census/order mismatch")
            length = _int(r[3], "tree edge length", 0, 2**31 - 1)
            endpoints = tuple(_int(v, "tree node index", 0, tree_nodes - 1) for v in r[4:8])
            route_length = _int(r[8], "route length")
            grid_size = _int(r[9], "route grid size")
            if route_length and grid_size < route_length + 1:
                raise FormatError("route grid vector shorter than step census")
            tree_edges.append({"length": length, "nodes": endpoints, "route_length": route_length, "grid_size": grid_size})
            previous = None
            for step in range(route_length):
                r = rows.take("STEP", 11)
                if [_int(v, "step index") for v in r[1:4]] != [slot, edge, step]:
                    raise FormatError("step census/order mismatch")
                a = (_int(r[4], "step x", 0, nx - 1), _int(r[5], "step y", 0, ny - 1), _int(r[6], "step layer", 0, nl - 1))
                b = (_int(r[7], "step x", 0, nx - 1), _int(r[8], "step y", 0, ny - 1), _int(r[9], "step layer", 0, nl - 1))
                cost = _int(r[10], "step cost", 0, 127)
                if previous is not None and a != previous:
                    raise FormatError("discontinuous consecutive tree route steps")
                previous = b
                if sum(abs(u - v) for u, v in zip(a, b)) != 1:
                    raise FormatError("step must be one planar edge or co-located adjacent-layer via")
                if a[2] != b[2]:
                    if cost != 0:
                        raise FormatError("via step must have zero native planar-track demand")
                    vias += 1
                else:
                    if cost != demands[a[2]]:
                        raise FormatError("step cost differs from live per-layer demand")
                    key = ("H", a[2], min(a[0], b[0]), a[1]) if a[1] == b[1] else ("V", a[2], a[0], min(a[1], b[1]))
                    if key not in edges:
                        raise FormatError("step addresses absent physical edge")
                    contributions[key] += 1  # MULTISET, not union.
                step_count += 1
        nets[slot] = {"db_id": dbid, "name": name, "clock": bool(clock), "soft_ndr": bool(soft),
                      "scalar_cost": scalar, "minimum_layer": minimum, "maximum_layer": maximum,
                      "driver_index": driver, "demands": demands, "pins": pins, "tree_terminals": terminals,
                      "tree_nodes": tree_nodes, "tree_edges": tree_edges, "planar_step_multiplicity": contributions,
                      "via_steps": vias}
        slot += 1
    return Snapshot(hashlib.sha256(raw).hexdigest(), (nx, ny, nl, ox, oy, pitch), edges, nets, empty_slots, step_count)


def _key(edge: Edge) -> dict:
    return dict(zip(("direction", "layer", "x", "y"), edge))


def audit(snapshot: Snapshot) -> dict:
    """Compare exact raw usage, preserving unexplained residuals as gate FAIL."""
    weighted, union = Counter(), Counter()
    repeated_pairs = repeated_steps = 0
    duplicate_samples = []
    zero_costs = []
    for slot, net in snapshot.nets.items():
        for layer, demand in enumerate(net["demands"]):
            if demand == 0:
                zero_costs.append({"slot": slot, "name": net["name"], "layer": layer})
        for edge, count in net["planar_step_multiplicity"].items():
            cost = net["demands"][edge[1]]
            weighted[edge] += count * cost
            union[edge] += cost
            if count > 1:
                repeated_pairs += 1
                repeated_steps += count - 1
                if len(duplicate_samples) < 20:
                    duplicate_samples.append({"slot": slot, "name": net["name"], "edge": _key(edge),
                                              "multiplicity": count, "layer_demand": cost})
    mismatches = []
    mismatch_count = missing_usage = excess_contributions = wrap_candidates = 0
    overflow = 0
    for edge, (capacity, usage, reduction, real_capacity) in snapshot.edges.items():
        del reduction, real_capacity
        overflow += max(0, usage - capacity)
        accounted = weighted[edge]
        if accounted != usage:
            mismatch_count += 1
            missing_usage += max(0, usage - accounted)
            excess_contributions += max(0, accounted - usage)
            wrap = accounted > 65535 and accounted % 65536 == usage
            wrap_candidates += int(wrap)
            if len(mismatches) < 20:
                mismatches.append({"edge": _key(edge), "raw_usage": usage, "weighted_steps": accounted,
                                   "raw_minus_steps": usage - accounted, "possible_uint16_wrap": wrap})
    ledger_ok = mismatch_count == 0
    union_disagreement = sum(weighted[e] != union[e] for e in snapshot.edges)
    return {
        "schema_version": 1, "input_sha256": snapshot.sha256,
        "format_verified": True, "model_gate": "PASS" if ledger_ok else "FAIL",
        "usage_ledger_reconciled": ledger_ok,
        "conclusion_scope": "raw_export_accounting_only",
        "native_inputs_authenticated": False, "physical_acceptance": False, "timing_acceptance": False,
        "grid": list(snapshot.grid), "raw_edge_count": len(snapshot.edges), "live_net_count": len(snapshot.nets),
        "empty_slot_count": len(snapshot.empty_slots), "step_count": snapshot.steps,
        "clock_net_count": sum(n["clock"] for n in snapshot.nets.values()),
        "soft_ndr_net_count": sum(n["soft_ndr"] for n in snapshot.nets.values()),
        "raw_usage_over_capacity_sum": overflow,
        "reconciliation": {"mismatched_edges": mismatch_count, "unexplained_raw_usage": missing_usage,
                           "excess_step_contributions": excess_contributions, "possible_uint16_wrap_edges": wrap_candidates,
                           "samples": mismatches},
        "union_vs_multiplicity": {"disagrees": bool(union_disagreement), "disagreeing_edges": union_disagreement,
                                  "repeated_net_edge_pairs": repeated_pairs, "extra_planar_step_occurrences": repeated_steps,
                                  "multiset_weighted_sum": sum(weighted.values()), "union_weighted_sum": sum(union.values()),
                                  "samples": duplicate_samples},
        "zero_layer_demand_count": len(zero_costs), "zero_layer_demand_samples": zero_costs[:20],
        "solver_union_accounting_compatible": ledger_ok and not union_disagreement and not zero_costs,
        "via_model": "global_route_steps_only_no_physical_cut_capacity",
    }


def audit_file(path: Path) -> dict:
    with path.open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    return audit(parse_bytes(raw))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit_file(args.input)
    except (FormatError, OSError) as exc:
        parser.exit(2, f"native corridor audit: {exc}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if result["usage_ledger_reconciled"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
