"""Bounded feasibility of an explicitly declared layer graph, NOT chip routing.

Every listed terminal of each net must connect inside the supplied graph. Physical
wires are undirected resources: an edge's capacity charges each occupying net
once, including a shared trunk serving multiple terminals. Layer costs and fixed
background usage are input contracts, never inferred from OpenDB display counts.

Optional dependency: requirements-routing.txt. No EDA, network or installation is
performed here. CLI: python -m autonomy.corridor_solver INPUT --output RESULT.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any


SOLVER_VERSION = "9.14.6206"
MAX_NODES = 5_000
MAX_EDGES = 12_000
MAX_NETS = 128
MAX_VARIABLES = 500_000
MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_COUNT = 1_000_000
CONTRACT = {
    "graph": "explicit_undirected_layer_graph",
    "occupancy": "per_net_edge_union",
    "capacity_units": "declared_integer_demand_units",
    "fixed_usage": "excludes_all_selected_nets",
    "terminals": "all_listed_nodes_required_within_graph",
    "boundary": "fixed_nodes_without_implicit_exterior_connections",
    "pin_access": "declared_terminal_nodes_only",
}
REQUIRED_OMISSIONS = {"physical_drc", "track_assignment", "timing", "antenna"}


class InputError(ValueError):
    """An input or witness does not satisfy the explicit model contract."""


def _keys(value: Any, keys: set[str], where: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise InputError(f"{where}: require exactly {sorted(keys)}")


def _name(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 256 or any(ord(c) < 32 for c in value):
        raise InputError(f"{where}: require nonempty text without control characters (max256)")
    return value


def _integer(value: Any, where: str, minimum: int = 0, maximum: int = MAX_COUNT) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise InputError(f"{where}: require integer in [{minimum}, {maximum}]")
    return value


def _items(value: Any, where: str, maximum: int, minimum: int = 0) -> list:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise InputError(f"{where}: require list of size [{minimum}, {maximum}]")
    return value


def _names(value: Any, where: str, allowed: set[str], *, minimum: int = 0) -> list[str]:
    names = _items(value, where, len(allowed), minimum)
    for name in names:
        _name(name, where)
        if name not in allowed:
            raise InputError(f"{where}: unknown node {name!r}")
    if len(set(names)) != len(names):
        raise InputError(f"{where}: duplicate node")
    return names


def validate_graph(value: Any) -> dict:
    """Validate strictly, return an independent JSON copy with canonical ordering.

    This validates a declared abstract graph; it authenticates no native routing
    state. In particular, encoded reporting-grid capacities are not raw tracks.
    """
    _keys(value, {"schema_version", "contract", "provenance", "layers", "nodes", "edges", "nets"}, "graph")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise InputError("schema_version: require integer1")
    contract = value["contract"]
    _keys(contract, set(CONTRACT) | {"vias", "nonpreferred", "omitted_constraints"}, "contract")
    for key, expected in CONTRACT.items():
        if contract[key] != expected:
            raise InputError(f"contract.{key}: require {expected!r}")
    if contract["vias"] not in ("forbidden", "explicit_capacity_edges", "unlimited_coarse_edges"):
        raise InputError("contract.vias: require forbidden, explicit_capacity_edges or unlimited_coarse_edges")
    if contract["nonpreferred"] not in ("forbidden", "explicit_edges"):
        raise InputError("contract.nonpreferred: require forbidden or explicit_edges")
    omissions = _items(contract["omitted_constraints"], "omitted_constraints", 32, 4)
    for omission in omissions:
        _name(omission, "omitted_constraints")
    if len(set(omissions)) != len(omissions) or not REQUIRED_OMISSIONS <= set(omissions):
        raise InputError("omitted_constraints: require unique entries including physical_drc, track_assignment, timing, antenna")
    provenance = value["provenance"]
    _keys(provenance, {"kind", "description", "source_sha256"}, "provenance")
    if provenance["kind"] not in ("abstract_fixture", "external_explicit_graph"):
        raise InputError("provenance.kind: unsupported")
    _name(provenance["description"], "provenance.description")
    source_hash = provenance["source_sha256"]
    if source_hash is not None and (not isinstance(source_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", source_hash)):
        raise InputError("provenance.source_sha256: require lower-case SHA256 or null")
    if provenance["kind"] == "external_explicit_graph" and source_hash is None:
        raise InputError("external graph requires a source digest; digest is recorded, not authenticated")

    layers = {}
    for layer in _items(value["layers"], "layers", 16, 1):
        _keys(layer, {"id", "preferred_direction"}, "layer")
        name = _name(layer["id"], "layer.id")
        if name in layers or layer["preferred_direction"] not in ("horizontal", "vertical"):
            raise InputError("layer: duplicate ID or invalid preferred direction")
        layers[name] = layer
    nodes = {}
    positions = set()
    for node in _items(value["nodes"], "nodes", MAX_NODES, 1):
        _keys(node, {"id", "x", "y", "layer"}, "node")
        name = _name(node["id"], "node.id")
        _name(node["layer"], "node.layer")
        if name in nodes or node["layer"] not in layers:
            raise InputError("node: duplicate ID or unknown layer")
        x = _integer(node["x"], "node.x", -10**9, 10**9)
        y = _integer(node["y"], "node.y", -10**9, 10**9)
        position = (x, y, node["layer"])
        if position in positions:
            raise InputError("node: duplicate layer/coordinate; use one explicit junction")
        positions.add(position)
        nodes[name] = node
    edges = {}
    links = set()
    for edge in _items(value["edges"], "edges", MAX_EDGES):
        _keys(edge, {"id", "u", "v", "direction", "capacity", "fixed_usage"}, "edge")
        name = _name(edge["id"], "edge.id")
        _name(edge["u"], "edge.u")
        _name(edge["v"], "edge.v")
        if name in edges or edge["u"] not in nodes or edge["v"] not in nodes or edge["u"] == edge["v"]:
            raise InputError("edge: duplicate ID, unknown endpoint or self-loop")
        u, v = nodes[edge["u"]], nodes[edge["v"]]
        link = tuple(sorted((edge["u"], edge["v"])))
        if link in links:
            raise InputError("edge: duplicate endpoint pair; combine capacity explicitly")
        links.add(link)
        _integer(edge["fixed_usage"], "edge.fixed_usage")
        direction = edge["direction"]
        if u["layer"] != v["layer"]:
            layer_ids = list(layers)
            if (direction != "via" or contract["vias"] == "forbidden"
                    or u["x"] != v["x"] or u["y"] != v["y"]
                    or abs(layer_ids.index(u["layer"]) - layer_ids.index(v["layer"])) != 1):
                raise InputError("via: require co-located adjacent declared layers and explicit capacity contract")
            if contract["vias"] == "unlimited_coarse_edges":
                if edge["capacity"] is not None or edge["fixed_usage"] != 0:
                    raise InputError("unlimited coarse via: require null capacity and zero fixed demand")
            else:
                _integer(edge["capacity"], "edge.capacity")
        else:
            _integer(edge["capacity"], "edge.capacity")
            actual = "horizontal" if u["y"] == v["y"] else "vertical" if u["x"] == v["x"] else None
            if direction != actual or actual is None:
                raise InputError("wire: require matching orthogonal direction")
            if direction != layers[u["layer"]]["preferred_direction"] and contract["nonpreferred"] != "explicit_edges":
                raise InputError("wire: nonpreferred motion forbidden")
        edges[name] = edge
    nets = {}
    for net in _items(value["nets"], "nets", MAX_NETS, 1):
        _keys(net, {"id", "terminals", "boundary_terminals", "track_demand_by_layer", "via_track_demand", "allowed_planar_layers"}, "net")
        name = _name(net["id"], "net.id")
        if name in nets:
            raise InputError("net: duplicate ID")
        terminals = _names(net["terminals"], "net.terminals", set(nodes), minimum=1)
        boundary = _names(net["boundary_terminals"], "net.boundary_terminals", set(terminals))
        del boundary  # Validation only; all are pinned, required terminals.
        demand = net["track_demand_by_layer"]
        _keys(demand, set(layers), "net.track_demand_by_layer")
        for layer, count in demand.items():
            _integer(count, f"net.track_demand_by_layer.{layer}", 1)
        _names(net["allowed_planar_layers"], "net.allowed_planar_layers", set(layers), minimum=1)
        if contract["vias"] == "explicit_capacity_edges":
            _integer(net["via_track_demand"], "net.via_track_demand", 1)
        elif contract["vias"] == "unlimited_coarse_edges":
            _integer(net["via_track_demand"], "net.via_track_demand", 0, 0)
        elif net["via_track_demand"] is not None:
            raise InputError("net.via_track_demand: require null when vias forbidden")
        nets[name] = net
    # Copy first: validation must not mutate callers' fixtures/artifacts.
    result = json.loads(json.dumps(value))
    for key in ("nodes", "edges", "nets"):
        result[key].sort(key=lambda item: item["id"])
    # Layer array order is semantically meaningful for via adjacency.
    result["contract"]["omitted_constraints"].sort()
    for net in result["nets"]:
        net["terminals"].sort()
        net["boundary_terminals"].sort()
        net["allowed_planar_layers"].sort()
    return result


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _edge_demand(net: dict, edge: dict, nodes: dict) -> int:
    if edge["direction"] == "via":
        return net["via_track_demand"]
    return net["track_demand_by_layer"][nodes[edge["u"]]["layer"]]


def _connected(edges: dict, selected: set[str], root: str) -> set[str]:
    neighbors = defaultdict(list)
    for name in selected:
        edge = edges[name]
        neighbors[edge["u"]].append(edge["v"])
        neighbors[edge["v"]].append(edge["u"])
    reached, pending = {root}, deque([root])
    while pending:
        for node in neighbors[pending.popleft()]:
            if node not in reached:
                reached.add(node)
                pending.append(node)
    return reached


def validate_witness(graph: dict, witness: Any) -> dict:
    """Independently check resource use and graph connectivity without CP-SAT."""
    graph = validate_graph(graph)
    nodes = {node["id"]: node for node in graph["nodes"]}
    edges = {edge["id"]: edge for edge in graph["edges"]}
    nets = {net["id"]: net for net in graph["nets"]}
    _keys(witness, set(nets), "witness")
    usage = {name: edge["fixed_usage"] for name, edge in edges.items()}
    for name, net in nets.items():
        selected = set(_names(witness[name], f"witness.{name}", set(edges)))
        reached = _connected(edges, selected, net["terminals"][0])
        if not set(net["terminals"]) <= reached:
            raise InputError(f"witness.{name}: required terminal disconnected")
        if any(edges[item]["u"] not in reached or edges[item]["v"] not in reached for item in selected):
            raise InputError(f"witness.{name}: disconnected extraneous route component")
        for item in selected:
            if edges[item]["direction"] != "via" and nodes[edges[item]["u"]]["layer"] not in net["allowed_planar_layers"]:
                raise InputError(f"witness.{name}: forbidden planar layer")
            usage[item] += _edge_demand(net, edges[item], nodes)
    for name, count in usage.items():
        if edges[name]["capacity"] is not None and count > edges[name]["capacity"]:
            raise InputError(f"witness: capacity exceeded on {name!r}: {count}>{edges[name]['capacity']}")
    return {"checked": True, "edge_usage": usage, "terminal_connectivity": True,
            "capacity_feasible": True, "physical_acceptance": False}


def _limit(value: Any, name: str, maximum: float) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= maximum:
        raise InputError(f"{name}: require finite positive number <= {maximum}")
    return float(value)


def solve(graph: dict, *, max_seconds: float = 30, max_deterministic_time: float = 10,
          max_memory_mb: int = 1024, max_variables: int = 100_000) -> dict:
    """Solve exactly the explicit graph; UNKNOWN includes any inconclusive stop.

    Limits are CP-SAT solver limits, not an OS-enforced process memory sandbox.
    There is no optimization objective; native OPTIMAL is normalized to FEASIBLE.
    """
    graph = validate_graph(graph)
    max_seconds = _limit(max_seconds, "max_seconds", 300)
    max_deterministic_time = _limit(max_deterministic_time, "max_deterministic_time", 300)
    _integer(max_memory_mb, "max_memory_mb", 1, 4096)
    _integer(max_variables, "max_variables", 1, MAX_VARIABLES)
    nodes = {node["id"]: node for node in graph["nodes"]}
    edges = {edge["id"]: edge for edge in graph["edges"]}
    # One occupied-edge Boolean plus one signed aggregate connectivity flow per
    # edge/net. Flow sends one unit to every non-root terminal; trunk occupancy
    # is still charged ONCE, not once per unit or sink.
    variable_count = len(edges) * len(graph["nets"]) * 2
    if variable_count > max_variables:
        raise InputError(f"model requires {variable_count} variables, exceeds declared limit {max_variables}")
    try:
        import ortools
        from ortools.sat.python import cp_model
    except ImportError as exc:
        raise RuntimeError("optional routing solver missing; install requirements-routing.txt in the project venv") from exc
    if ortools.__version__ != SOLVER_VERSION:
        raise RuntimeError(f"require pinned ortools=={SOLVER_VERSION}, found {ortools.__version__}")

    model = cp_model.CpModel()
    occupancy = {}
    contributions = defaultdict(list)
    incident = defaultdict(list)
    for edge in graph["edges"]:
        incident[edge["u"]].append((edge["id"], 1))
        incident[edge["v"]].append((edge["id"], -1))
    for ni, net in enumerate(graph["nets"]):
        sinks = len(net["terminals"]) - 1
        flow = {}
        for ei, edge in enumerate(graph["edges"]):
            key = (net["id"], edge["id"])
            used = model.NewBoolVar(f"x_{ni}_{ei}")
            transfer = model.NewIntVar(-sinks, sinks, f"f_{ni}_{ei}")
            occupancy[key] = used
            if edge["direction"] != "via" and nodes[edge["u"]]["layer"] not in net["allowed_planar_layers"]:
                model.Add(used == 0)
            flow[edge["id"]] = transfer
            model.Add(transfer <= sinks * used)
            model.Add(transfer >= -sinks * used)
            contributions[edge["id"]].append(_edge_demand(net, edge, nodes) * used)
        required = set(net["terminals"])
        root = net["terminals"][0]
        for node in graph["nodes"]:
            name = node["id"]
            balance = sinks if name == root else -1 if name in required else 0
            if incident[name] or balance:
                model.Add(sum(sign * flow[edge] for edge, sign in incident[name]) == balance)
    for edge in graph["edges"]:
        if edge["capacity"] is not None:
            model.Add(sum(contributions[edge["id"]]) + edge["fixed_usage"] <= edge["capacity"])
    if len(model.Proto().variables) > max_variables:
        raise InputError("constructed model exceeds declared variable limit")
    invalid = model.Validate()
    if invalid:
        raise RuntimeError(f"CP-SAT rejected constructed model: {invalid}")
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    solver.parameters.max_time_in_seconds = max_seconds
    solver.parameters.max_deterministic_time = max_deterministic_time
    solver.parameters.max_memory_in_mb = max_memory_mb
    status = solver.Solve(model)
    names = {cp_model.OPTIMAL: "OPTIMAL", cp_model.FEASIBLE: "FEASIBLE",
             cp_model.INFEASIBLE: "INFEASIBLE", cp_model.UNKNOWN: "UNKNOWN"}
    if status not in names:
        raise RuntimeError("unexpected CP-SAT response (including MODEL_INVALID); no feasibility conclusion")
    native = names[status]
    result = {
        "schema_version": 1, "status": "FEASIBLE" if native in ("OPTIMAL", "FEASIBLE") else native,
        "native_status": native, "solver": {"name": "ortools-cp-sat", "version": ortools.__version__},
        "graph_sha256": digest(canonical_bytes(graph)),
        "model_sha256": digest(model.Proto().SerializeToString(deterministic=True)),
        "model_size": {"nodes": len(nodes), "edges": len(edges), "nets": len(graph["nets"]),
                       "variables": len(model.Proto().variables), "constraints": len(model.Proto().constraints)},
        "limits": {"wall_seconds": max_seconds, "deterministic_time": max_deterministic_time,
                   "solver_memory_mb": max_memory_mb, "variables": max_variables, "workers": 1,
                   "os_memory_limit_enforced": False},
        "contract": graph["contract"], "provenance": graph["provenance"],
        "conclusion_scope": "declared_explicit_graph_only", "native_inputs_authenticated": False,
        "physical_acceptance": False, "timing_acceptance": False,
        "infeasibility_independently_certified": False,
        "response_stats": solver.ResponseStats(), "witness": None, "witness_sha256": None,
        "witness_check": None,
    }
    if result["status"] == "FEASIBLE":
        witness = {}
        for net in graph["nets"]:
            selected = {edge for edge in edges if solver.Value(occupancy[(net["id"], edge)])}
            reached = _connected(edges, selected, net["terminals"][0])
            # CP-SAT may set irrelevant disconnected occupancy bits. Dropping
            # those can only decrease resource consumption; verify afterwards.
            witness[net["id"]] = sorted(edge for edge in selected if edges[edge]["u"] in reached)
        result["witness_check"] = validate_witness(graph, witness)
        result["witness"] = witness
        result["witness_sha256"] = digest(canonical_bytes(witness))
    return result


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"JSON: duplicate key {key!r}")
        result[key] = value
    return result


def load_graph(path: Path) -> tuple[dict, str]:
    """Read a finite JSON document; duplicate keys and non-finite numbers fail."""
    with path.open("rb") as handle:
        raw = handle.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError("input exceeds byte limit")
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object,
                           parse_constant=lambda token: (_ for _ in ()).throw(InputError(f"non-finite JSON value {token}")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError(f"invalid JSON: {exc}") from exc
    return validate_graph(value), digest(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-seconds", type=float, default=30)
    parser.add_argument("--max-deterministic-time", type=float, default=10)
    parser.add_argument("--max-memory-mb", type=int, default=1024)
    parser.add_argument("--max-variables", type=int, default=100_000)
    args = parser.parse_args(argv)
    try:
        graph, raw_hash = load_graph(args.input)
        result = solve(graph, max_seconds=args.max_seconds, max_deterministic_time=args.max_deterministic_time,
                       max_memory_mb=args.max_memory_mb, max_variables=args.max_variables)
        result["input_file_sha256"] = raw_hash
    except (InputError, RuntimeError, OSError) as exc:
        parser.exit(2, f"corridor solver: {exc}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    # A nonzero routing answer is still a successfully collected experiment.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
