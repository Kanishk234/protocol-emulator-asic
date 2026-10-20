"""Read-only native terminal inventory/cross-join audit, never physical access proof.

Malformed observations raise FormatError. Valid but unsupported access remains an
explicit diagnostic FAIL. Checkpoint/process authentication belongs to the caller.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from autonomy import native_corridor as corridor

FormatError = corridor.FormatError
_I = corridor._int
_LIMIT = corridor.MAX_COUNT


def _signed(v: str) -> int:
    return _I(v, "signed field", -(2**31), 2**31 - 1)


def _count(v: str) -> int:
    return _I(v, "count")


def _flag(v: str) -> int:
    return _I(v, "Boolean", 0, 1)


def _id(v: str) -> int:
    return _I(v, "database ID", 1, 2**32 - 1)


def _text(v: str) -> str:
    if not v or any(ord(c) < 32 for c in v):
        raise FormatError("empty/control character text")
    return v


def _grid(row: list[str]) -> tuple:
    return (_I(row[1], "nx", 2, 32767), _I(row[2], "ny", 2, 32767),
            _I(row[3], "layers", 1, 64), _signed(row[4]), _signed(row[5]),
            _I(row[6], "pitch", 1, 2**31 - 1))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FormatError(message)


@dataclass
class TerminalState:
    sha256: str
    dbu: int
    grid: tuple
    layers: list[dict]
    database: dict[int, dict]
    global_nets: dict[int, dict]
    nets: dict[int, dict]
    empty_slots: list[int]


def parse_file(path: Path) -> TerminalState:
    with Path(path).open("rb") as stream:
        return parse_bytes(stream.read(corridor.MAX_BYTES + 1))


def parse_bytes(raw: bytes) -> TerminalState:
    if len(raw) > corridor.MAX_BYTES:
        raise FormatError("terminal export exceeds byte limit")
    try:
        rows = corridor._Rows(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise FormatError("terminal export is not UTF-8") from exc
    for expected in [("SCHEMA", "warp-native-terminals-v1"),
                     ("MODEL_GATE", "terminal_join_verified", "false"),
                     ("SCOPE", "coarse_pin_membership_and_tree_access_not_physical_via_feasibility"),
                     ("INDEXING", "native_layers_zero_based_database_routing_levels_one_based")]:
        _require(rows.take(expected[0], len(expected)) == list(expected), "unsupported terminal contract")
    dbu = _I(rows.take("DBU", 2)[1], "DBU", 1, 2**31 - 1)
    grid = _grid(rows.take("GLOBAL_GRID", 7))
    nx, ny, nl, _, _, _ = grid
    layers, layer_ids, layer_names = [], set(), set()
    for layer in range(nl):
        r = rows.take("LAYER", 6)
        entry = dict(index=_count(r[1]), db_id=_id(r[2]), level=_count(r[3]), name=_text(r[4]), direction=r[5])
        _require(entry["index"] == layer and entry["level"] == layer + 1
                 and entry["db_id"] not in layer_ids and entry["name"] not in layer_names
                 and entry["direction"] in ("HORIZONTAL", "VERTICAL"), "layer census/identity mismatch")
        layer_ids.add(entry["db_id"])
        layer_names.add(entry["name"])
        layers.append(entry)
    database, names = {}, set()
    previous = 0
    while True:
        r = rows.next()
        if r[0] == "DATABASE_COMPLETE":
            _require(len(r) == 2 and _count(r[1]) == len(database), "database footer mismatch")
            break
        _require(r[0] == "DATABASE_NET" and len(r) == 10 and len(database) < _LIMIT, "invalid database row")
        dbid, name = _id(r[1]), _text(r[2])
        _require(dbid > previous and name not in names, "database order/duplicate identity")
        previous = dbid
        names.add(name)
        database[dbid] = dict(name=name, special=_flag(r[3]), supply=_flag(r[4]), clock=_flag(r[5]),
                              global_map=_flag(r[6]), slot=_I(r[7], "slot", -1),
                              iterms=_count(r[8]), bterms=_count(r[9]))
    globals_, physical_ids = {}, set()
    previous = pin_total = member_total = 0
    while True:
        r = rows.next()
        if r[0] == "GLOBAL_COMPLETE":
            _require(len(r) == 4 and [_count(x) for x in r[1:]] == [len(globals_), pin_total, member_total], "global footer mismatch")
            break
        _require(r[0] == "GLOBAL_NET" and len(r) == 12 and len(globals_) < _LIMIT, "invalid global net")
        dbid, name = _id(r[1]), _text(r[2])
        _require(dbid > previous and dbid in database and database[dbid]["name"] == name, "global database identity/order mismatch")
        previous = dbid
        n = dict(name=name, local=_flag(r[3]), merged=_flag(r[4]), clock=_flag(r[5]),
                 pin_count=_count(r[6]), num_pins=_count(r[7]), max_layer=_signed(r[8]),
                 has_route=_flag(r[9]), segments=_count(r[10]), slot=_I(r[11], "slot", -1), pins=[])
        _require(n["pin_count"] == n["num_pins"] and (n["has_route"] or not n["segments"]), "global count/route contradiction")
        for ordinal in range(n["pin_count"]):
            p = rows.take("GLOBAL_PIN", 18)
            _require([_id(p[1]), _count(p[2])] == [dbid, ordinal] and p[3] in ("BTERM", "ITERM"), "physical pin order/kind mismatch")
            ids = tuple(_I(v, "physical ID", 0, 2**32 - 1) for v in p[4:7])
            pin = dict(kind=p[3], ids=ids, name=_text(p[7]), driver=_I(p[8], "driver", -1, 1),
                       dbu_xy=tuple(_signed(v) for v in p[9:11]), original_layer=_signed(p[11]),
                       clamped_layer=_signed(p[12]), xy=tuple(_signed(v) for v in p[13:15]),
                       eligible=_flag(p[15]), slot=_I(p[16], "slot", -1), members=[])
            resolved = ids[0] > 0 and (ids[1:] == (0, 0) if p[3] == "BTERM" else all(ids[1:]))
            if resolved:
                _require(pin["driver"] >= 0 and (p[3], ids[0]) not in physical_ids, "duplicate/unresolved physical identity")
                physical_ids.add((p[3], ids[0]))
            else:
                _require((ids == (0, 0, 0) or (p[3] == "ITERM" and ids[0] > 0 and ids[1:] == (0, 0)))
                         and pin["name"] == "UNRESOLVED" and pin["driver"] == -1,
                         "malformed unresolved physical identity")
            for _ in range(_count(p[17])):
                m = rows.take("MEMBER", 5)
                _require([_id(m[1]), _count(m[2])] == [dbid, ordinal], "membership parent mismatch")
                pin["members"].append((_count(m[3]), _count(m[4])))
                member_total += 1
            n["pins"].append(pin)
            pin_total += 1
        globals_[dbid] = n
    _require(set(globals_) == {d for d, n in database.items() if n["global_map"]}, "database/global map census mismatch")
    _require(_grid(rows.take("NATIVE_GRID", 7)) == grid, "global/native grid mismatch")
    nets, empty = {}, []
    slot = node_total = mapping_total = 0
    native_ids = set()
    while True:
        r = rows.next()
        if r[0] == "NATIVE_COMPLETE":
            _require(len(r) == 5 and [_count(v) for v in r[1:]] == [slot, len(nets), node_total, mapping_total], "native footer mismatch")
            break
        _require(slot < _LIMIT, "native slot limit")
        if r[0] == "NATIVE_EMPTY_SLOT":
            _require(len(r) == 2 and _count(r[1]) == slot, "empty slot order mismatch")
            empty.append(slot)
            slot += 1
            continue
        _require(r[0] == "NATIVE_NET" and len(r) == 12 and _count(r[1]) == slot, "native net order/shape mismatch")
        dbid = _id(r[2])
        _require(dbid not in native_ids and dbid in database and _text(r[3]) == database[dbid]["name"], "native database identity mismatch")
        native_ids.add(dbid)
        n = dict(db_id=dbid, name=r[3], pin_count=_count(r[4]), minimum_layer=_I(r[5], "minimum layer", 0, nl - 1),
                 maximum_layer=_I(r[6], "maximum layer", 0, nl - 1), driver_index=_signed(r[7]),
                 tree_terminals=_count(r[8]), tree_nodes=_count(r[9]), tree_edges=_count(r[10]),
                 mapping_count=_count(r[11]), pins=[], nodes=[], mapping={})
        _require(n["minimum_layer"] <= n["maximum_layer"] and -1 <= n["driver_index"] < n["pin_count"]
                 and n["tree_terminals"] <= n["pin_count"] and n["tree_terminals"] <= n["tree_nodes"], "native bounds contradiction")
        a = rows.take("TREE_ACCESS_SUPPORTED", 3)
        _require(_count(a[1]) == slot, "access slot mismatch")
        n["access_supported"] = _flag(a[2])
        _require(not n["access_supported"] or (n["pin_count"] >= 2 and n["tree_terminals"] >= 2 and n["tree_nodes"] and n["tree_edges"]), "impossible supported tree")
        for pin in range(n["pin_count"]):
            p = rows.take("NATIVE_PIN", 6)
            _require([_count(v) for v in p[1:3]] == [slot, pin], "native pin order mismatch")
            n["pins"].append((_I(p[3], "pin x", 0, nx - 1), _I(p[4], "pin y", -1, ny - 1), _I(p[5], "pin layer", 0, nl - 1)))
        for node in range(n["tree_nodes"]):
            if n["access_supported"]:
                p = rows.take("NODE", 10)
                _require([_count(v) for v in p[1:3]] == [slot, node], "node order mismatch")
                value = dict(xy=(_I(p[3], "node x", 0, nx - 1), _I(p[4], "node y", -1, ny - 1)),
                             alias=_signed(p[5]), bottom=_signed(p[6]), top=_signed(p[7]), high_id=_signed(p[8]), low_id=_signed(p[9]))
                v = rows.take("VIA_RANGE", 6)
                _require([_count(x) for x in v[1:3]] == [slot, node], "via-range parent mismatch")
                value["via_range"] = (_signed(v[3]), _signed(v[4]), _count(v[5]))
                at_xy = [p[2] for p in n["pins"] if p[:2] == value["xy"]]
                expected = (min(at_xy), max(at_xy), len(at_xy)) if at_xy else (32767, -1, 0)
                _require(value["via_range"] == expected, "via-range differs from native pin census")
            else:
                p = rows.take("NODE_UNSUPPORTED", 4)
                _require([_count(v) for v in p[1:3]] == [slot, node]
                         and p[3] == "no_initialized_routed_tree_access_contract", "unsupported node mismatch")
                value = None
            n["nodes"].append(value)
            node_total += 1
        for _ in range(n["mapping_count"]):
            m = rows.take("NODE_PIN", 4)
            _require(_count(m[1]) == slot, "node-pin slot mismatch")
            node = _I(m[2], "mapped node", 0, n["tree_nodes"] - 1)
            pin = _I(m[3], "mapped pin", -1, n["pin_count"] - 1)
            _require(node not in n["mapping"], "duplicate mapped node")
            n["mapping"][node] = pin
            mapping_total += 1
        nets[slot] = n
        slot += 1
    _require(rows.take("COMPLETE", 2) == ["COMPLETE", "warp-native-terminals-v1"], "completion contract mismatch")
    try:
        next(rows.rows)
    except StopIteration:
        pass
    else:
        raise FormatError("trailing terminal data")
    native_slots = {n["db_id"]: s for s, n in nets.items()}
    for dbid, d in database.items():
        _require(native_slots.get(dbid, -1) == d["slot"], "database/native slot census mismatch")
    return TerminalState(hashlib.sha256(raw).hexdigest(), dbu, grid, layers, database, globals_, nets, empty)


def _trunc(n: int, denominator: int) -> int:
    return (abs(n) // denominator) * (-1 if n < 0 else 1)


def audit_join(snapshot: corridor.Snapshot, state: TerminalState) -> dict:
    """Check all common inventories and native construction; unsupported != proof."""
    _require(snapshot.grid == state.grid and set(snapshot.nets) == set(state.nets)
             and snapshot.empty_slots == state.empty_slots, "raw/terminal grid or slot inventory mismatch")
    nx, ny, nl, ox, oy, pitch = state.grid
    unsupported = []
    def note(reason: str, **identity) -> None:
        unsupported.append(dict(reason=reason, **identity))
    for slot, n in state.nets.items():
        raw = snapshot.nets[slot]
        for key in ("db_id", "name", "minimum_layer", "maximum_layer", "driver_index", "pins", "tree_terminals", "tree_nodes"):
            _require(n[key] == raw[key], f"raw/terminal {key} mismatch at slot {slot}")
        _require(n["tree_edges"] == len(raw["tree_edges"]), "raw/terminal tree edge count mismatch")
        _require(n["db_id"] in state.global_nets, "native net absent from GlobalRouter map")
        global_ = state.global_nets[n["db_id"]]
        _require(global_["slot"] == slot, "native/global slot mismatch")
        _require(state.database[n["db_id"]]["clock"] == raw["clock"], "native/database signal-type clock mismatch")
        if not n["access_supported"]:
            note("unsupported_tree_access", slot=slot)
        if global_["merged"]:
            note("merged_tree_membership_not_authenticated", slot=slot)
        for node, pin in n["mapping"].items():
            access = n["nodes"][node]
            if pin < 0:
                note("unresolved_node_pin_mapping", slot=slot, node=node)
            elif access is not None:
                _require(access["xy"] == n["pins"][pin][:2], "node-pin coordinate mismatch")
        if n["access_supported"]:
            if set(n["mapping"]) != set(range(n["tree_terminals"])):
                note("terminal_node_mapping_incomplete", slot=slot)
            position_occurrences = {}
            for node, access in enumerate(n["nodes"]):
                if node < n["tree_terminals"] and not global_["merged"]:
                    xy = access["xy"]
                    occurrence = position_occurrences.get(xy, 0)
                    position_occurrences[xy] = occurrence + 1
                    candidates = [p for p, xyz in enumerate(n["pins"]) if xyz[:2] == xy]
                    expected_pin = candidates[occurrence] if occurrence < len(candidates) else -1
                    mapped = n["mapping"].get(node, -1)
                    if mapped >= 0:
                        _require(mapped == expected_pin, "terminal occurrence-order/layer membership mismatch")
                if not 0 <= access["alias"] < n["tree_nodes"]:
                    note("unsupported_stack_alias", slot=slot, node=node)
                    continue
                alias = n["nodes"][access["alias"]]
                _require(alias["xy"] == access["xy"], "stack alias coordinate mismatch")
                if node < n["tree_terminals"]:
                    if not (0 <= alias["bottom"] <= alias["top"] < nl):
                        note("terminal_access_layer_sentinel", slot=slot, node=node)
                    if access["via_range"][2] == 0:
                        note("terminal_has_no_native_pin_range", slot=slot, node=node)
    physical_count = membership_count = 0
    for dbid, g in state.global_nets.items():
        db = state.database[dbid]
        _require(g["slot"] == db["slot"], "database/global native slot mismatch")
        n = state.nets.get(g["slot"])
        reconstructed, root = [], 0
        kinds = {"ITERM": 0, "BTERM": 0}
        for ordinal, p in enumerate(g["pins"]):
            physical_count += 1
            kinds[p["kind"]] += 1
            if p["driver"] < 0:
                note("unresolved_physical_pin", db_id=dbid, ordinal=ordinal)
            clamped = min(p["original_layer"], g["max_layer"])
            x, y = (_trunc(p["dbu_xy"][0] - ox, pitch), _trunc(p["dbu_xy"][1] - oy, pitch))
            eligible = 0 <= x < nx and -1 <= y < ny and 0 < clamped <= nl
            _require((clamped, (x, y), int(eligible), g["slot"]) ==
                     (p["clamped_layer"], p["xy"], p["eligible"], p["slot"]), "physical clamp/coarse/eligibility/slot mismatch")
            xyz = (x, y, clamped - 1)
            expected_members = [(g["slot"], i) for i, pin in enumerate(n["pins"]) if pin == xyz] if n else []
            _require(p["members"] == expected_members, "physical/native exact membership mismatch")
            membership_count += len(p["members"])
            if eligible and xyz not in reconstructed:
                reconstructed.append(xyz)
                if p["driver"] == 1:
                    root = len(reconstructed) - 1
            if not eligible:
                note("ineligible_physical_pin", db_id=dbid, ordinal=ordinal)
        if kinds != {"ITERM": db["iterms"], "BTERM": db["bterms"]}:
            note("database_physical_pin_coverage_unavailable", db_id=dbid,
                 observed=kinds, database=dict(ITERM=db["iterms"], BTERM=db["bterms"]))
        if n and not g["merged"]:
            _require(reconstructed == n["pins"], "deduplicated physical pin vector differs from native construction")
            _require(root == n["driver_index"], "native driver differs from first-unique physical construction")
        if not n and g["pins"]:
            note("global_physical_pins_without_native_net", db_id=dbid)
    outside = [dbid for dbid, d in state.database.items() if not d["global_map"] and (d["iterms"] or d["bterms"])]
    for dbid in outside:
        note("database_net_membership_unavailable", db_id=dbid)
    return dict(schema="warp-native-terminal-audit-v1", terminal_sha256=state.sha256,
                native_sha256=snapshot.sha256, model_gate="FAIL" if unsupported else "PASS",
                terminal_join_verified=not unsupported, native_inputs_authenticated=False,
                physical_acceptance=False, timing_acceptance=False,
                database_nets=len(state.database), global_nets=len(state.global_nets), native_nets=len(state.nets),
                native_empty_slots=len(state.empty_slots), physical_pins=physical_count,
                memberships=membership_count, tree_nodes=sum(n["tree_nodes"] for n in state.nets.values()),
                unsupported_access=unsupported, layers=state.layers)


def audit_files(raw_path: Path, terminal_path: Path) -> dict:
    with Path(raw_path).open("rb") as stream:
        raw = corridor.parse_bytes(stream.read(corridor.MAX_BYTES + 1))
    return audit_join(raw, parse_file(terminal_path))


def audit_selection(snapshot: corridor.Snapshot, state: TerminalState, slots: list[int]) -> dict:
    """Explicit subset admission; preserve the whole-inventory gate unchanged.

    This verifies selected memberships/access, never physical via feasibility.
    Unscoped unsupported observations fail closed rather than disappearing.
    """
    if (not isinstance(slots, list) or not 1 <= len(slots) <= 128 or
            any(type(slot) is not int or slot not in snapshot.nets for slot in slots) or
            len(set(slots)) != len(slots)):
        raise FormatError('Require one to128 unique existing native slots')
    whole = audit_join(snapshot, state)
    if not corridor.audit(snapshot)['usage_ledger_reconciled']:
        raise FormatError('Selected model requires reconciled raw usage ledger')
    selected = set(slots)
    dbids = {snapshot.nets[slot]['db_id'] for slot in selected}
    relevant = []
    for item in whole['unsupported_access']:
        if ('slot' not in item and 'db_id' not in item) or item.get('slot') in selected or item.get('db_id') in dbids:
            relevant.append(item)
    return {'schema': 'warp-selected-terminal-admission-v1',
            'native_sha256': snapshot.sha256, 'terminal_sha256': state.sha256,
            'selected_slots': sorted(selected), 'selected_database_ids': sorted(dbids),
            'selected_membership_and_access_verified': not relevant,
            'whole_inventory_terminal_join_verified': whole['terminal_join_verified'],
            'unsupported_selected_access': relevant,
            'excluded_unsupported_observations': len(whole['unsupported_access'])-len(relevant),
            'raw_usage_ledger_reconciled': True,
            'native_inputs_authenticated': False, 'physical_acceptance': False, 'timing_acceptance': False,
            'scope': 'Explicit selected coarse memberships/access only; frozen exterior and physical via legality unverified'}
