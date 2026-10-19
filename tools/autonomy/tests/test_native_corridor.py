"""Independent hand-computed accounting fixtures, NOT native WARP qualification."""
import hashlib
import json

import pytest

from autonomy import native_corridor as n


def fixture(*, multiplicity=1, raw_usage=None, layers=1, via=False, two_nets=False, empty_slot=False):
    """2x2 graph: both H rows and both V columns, every declared layer."""
    usage = 2 * multiplicity if raw_usage is None else raw_usage
    if via:
        usage = 0
    if two_nets:
        usage = 4
    rows = ["SCHEMA\twarp-native-corridor-v1", "INDEXING\tzero_based_fast_route_layers_and_grid",
            "MODEL_GATE\tusage_ledger_verified\tfalse", "VIA_MODEL\tglobal_route_steps_only_no_physical_cut_capacity",
            f"GRID\t2\t2\t{layers}\t-10\t20\t100"]
    for layer in range(layers):
        rows.extend([f"EDGE\tH\t{layer}\t0\t0\t1\t{usage if layer == 0 else 0}\t3\t4",
                     f"EDGE\tH\t{layer}\t0\t1\t0\t0\t4\t4",
                     f"EDGE\tV\t{layer}\t0\t0\t0\t0\t4\t4",
                     f"EDGE\tV\t{layer}\t1\t0\t0\t0\t4\t4"])
    count = 2 if two_nets else 1
    for slot in range(count):
        rows.append(f"NET\t{slot}\t{11 + slot}\tnet {slot}\t1\t0\t3\t0\t{layers - 1}\t0\t2")
        rows.extend(f"DEMAND\t{slot}\t{layer}\t{layer + 2}" for layer in range(layers))
        target = "0\t0\t1" if via else "1\t0\t0"
        rows.extend([f"PIN\t{slot}\t0\t0\t0\t0", f"PIN\t{slot}\t1\t{target}",
                     f"TREE\t{slot}\t2\t2\t1", f"TREE_EDGE\t{slot}\t0\t1\t0\t1\t0\t1\t{multiplicity}\t{multiplicity + 1}"])
        for step in range(multiplicity):
            coords = "0\t0\t0\t0\t0\t1\t0" if via else ("0\t0\t0\t1\t0\t0\t2" if step % 2 == 0 else "1\t0\t0\t0\t0\t0\t2")
            rows.append(f"STEP\t{slot}\t0\t{step}\t{coords}")
    if empty_slot:
        rows.append(f"EMPTY_SLOT\t{count}")
    rows.append(f"COMPLETE\t{count + int(empty_slot)}\t{count}\t{count * multiplicity}")
    return ("\n".join(rows) + "\n").encode()


def replace(raw, old, new):
    assert old.encode() in raw
    return raw.replace(old.encode(), new.encode(), 1)


def test_hand_computed_raw_ledger_preserves_all_boundaries_and_costs():
    raw = fixture(empty_slot=True)
    parsed = n.parse_bytes(raw)
    report = n.audit(parsed)
    assert parsed.sha256 == hashlib.sha256(raw).hexdigest()
    assert parsed.grid == (2, 2, 1, -10, 20, 100)
    assert set(parsed.edges) == {("H", 0, 0, 0), ("H", 0, 0, 1), ("V", 0, 0, 0), ("V", 0, 1, 0)}
    assert parsed.edges[("H", 0, 0, 0)] == (1, 2, 3, 4)
    assert parsed.empty_slots == [1]
    assert parsed.nets[0]["scalar_cost"] == 3
    assert parsed.nets[0]["demands"] == [2]
    assert parsed.nets[0]["clock"] and not parsed.nets[0]["soft_ndr"]
    assert report["model_gate"] == "PASS" and report["usage_ledger_reconciled"]
    assert report["raw_usage_over_capacity_sum"] == 1  # Congestion remains valid data.
    assert report["solver_union_accounting_compatible"]
    assert not report["native_inputs_authenticated"] and not report["physical_acceptance"]


def test_duplicate_tree_steps_are_multiset_not_deduplicated():
    report = n.audit(n.parse_bytes(fixture(multiplicity=3)))
    assert report["usage_ledger_reconciled"]
    assert report["union_vs_multiplicity"]["multiset_weighted_sum"] == 6
    assert report["union_vs_multiplicity"]["union_weighted_sum"] == 2
    assert report["union_vs_multiplicity"]["extra_planar_step_occurrences"] == 2
    assert report["union_vs_multiplicity"]["repeated_net_edge_pairs"] == 1
    assert report["union_vs_multiplicity"]["disagrees"]
    assert not report["solver_union_accounting_compatible"]


def test_same_edge_in_different_tree_routes_still_preserves_multiplicity():
    raw = replace(fixture(raw_usage=4), "TREE\t0\t2\t2\t1", "TREE\t0\t2\t2\t2")
    raw = replace(raw, "COMPLETE\t1\t1\t1", "TREE_EDGE\t0\t1\t1\t0\t1\t0\t1\t1\t2\n"
                  "STEP\t0\t1\t0\t0\t0\t0\t1\t0\t0\t2\nCOMPLETE\t1\t1\t2")
    report = n.audit(n.parse_bytes(raw))
    assert report["usage_ledger_reconciled"]
    assert report["union_vs_multiplicity"]["multiset_weighted_sum"] == 4
    assert report["union_vs_multiplicity"]["union_weighted_sum"] == 2


def test_two_nets_sharing_edge_do_not_count_as_same_net_multiplicity():
    report = n.audit(n.parse_bytes(fixture(two_nets=True)))
    assert report["usage_ledger_reconciled"]
    assert report["live_net_count"] == 2
    assert report["union_vs_multiplicity"]["multiset_weighted_sum"] == 4
    assert not report["union_vs_multiplicity"]["disagrees"]


def test_soft_ndr_with_nonunit_layer_cost_is_impossible_native_state():
    # Pinned FastRoute.cpp FrNet::getLayerEdgeCost(l): soft => return1.
    # Even exactly matching raw usage cannot make contradictory state valid.
    raw = replace(fixture(), "net 0\t1\t0\t3", "net 0\t1\t1\t3")
    with pytest.raises(n.FormatError, match="soft-NDR.*unit demand"):
        n.parse_bytes(raw)


def test_soft_ndr_requires_unit_demand_on_unused_layers_too():
    raw = replace(fixture(layers=2), "net 0\t1\t0\t3", "net 0\t1\t1\t3")
    raw = replace(raw, "DEMAND\t0\t0\t2", "DEMAND\t0\t0\t1")
    with pytest.raises(n.FormatError, match="soft-NDR.*unit demand"):
        n.parse_bytes(raw)  # The unused layer still exports nonunit3.


def test_soft_ndr_preserves_nonunit_scalar_with_unit_layer_demands():
    raw = replace(fixture(raw_usage=1), "net 0\t1\t0\t3", "net 0\t1\t1\t3")
    raw = replace(raw, "DEMAND\t0\t0\t2", "DEMAND\t0\t0\t1")
    raw = replace(raw, "STEP\t0\t0\t0\t0\t0\t0\t1\t0\t0\t2", "STEP\t0\t0\t0\t0\t0\t0\t1\t0\t0\t1")
    parsed = n.parse_bytes(raw)
    assert parsed.nets[0]["scalar_cost"] == 3 and parsed.nets[0]["soft_ndr"]
    assert n.audit(parsed)["usage_ledger_reconciled"]


@pytest.mark.parametrize("raw_usage,missing,excess", [(5, 3, 0), (0, 0, 2)])
def test_mismatch_is_explicit_gate_failure_not_fabricated_background(raw_usage, missing, excess):
    report = n.audit(n.parse_bytes(fixture(raw_usage=raw_usage)))
    assert report["format_verified"] and report["model_gate"] == "FAIL"
    assert not report["usage_ledger_reconciled"]
    assert report["reconciliation"]["mismatched_edges"] == 1
    assert report["reconciliation"]["unexplained_raw_usage"] == missing
    assert report["reconciliation"]["excess_step_contributions"] == excess
    assert report["reconciliation"]["samples"][0]["raw_minus_steps"] == raw_usage - 2


def test_via_is_adjacent_zero_planar_demand_and_retained_separately():
    parsed = n.parse_bytes(fixture(layers=2, via=True))
    assert len(parsed.edges) == 8
    assert parsed.nets[0]["demands"] == [2, 3]
    assert parsed.nets[0]["via_steps"] == 1
    report = n.audit(parsed)
    assert report["usage_ledger_reconciled"] and report["union_vs_multiplicity"]["multiset_weighted_sum"] == 0
    assert report["via_model"] == "global_route_steps_only_no_physical_cut_capacity"


def test_all_real_boundary_edges_are_in_usage_reconciliation():
    raw = replace(fixture(), "EDGE\tH\t0\t0\t1\t0\t0\t4\t4", "EDGE\tH\t0\t0\t1\t0\t1\t4\t4")
    report = n.audit(n.parse_bytes(raw))
    assert report["model_gate"] == "FAIL"
    assert report["reconciliation"]["samples"][0]["edge"] == {"direction": "H", "layer": 0, "x": 0, "y": 1}


def test_long_integer_input_is_format_error_not_unbounded_conversion():
    with pytest.raises(n.FormatError):
        n.parse_bytes(replace(fixture(), "1\t2\t3\t4", "1\t" + "9" * 5000 + "\t3\t4"))


def test_route_vector_tail_is_retained_without_inventing_extra_steps():
    raw = replace(fixture(), "\t1\t2\nSTEP", "\t1\t5\nSTEP")
    snapshot = n.parse_bytes(raw)
    assert snapshot.nets[0]["tree_edges"][0]["grid_size"] == 5
    assert snapshot.steps == 1
    assert n.audit(snapshot)["usage_ledger_reconciled"]


@pytest.mark.parametrize("old,new", [
    ("warp-native-corridor-v1", "warp-native-corridor-v2"),
    ("usage_ledger_verified\tfalse", "usage_ledger_verified\ttrue"),
    ("zero_based_fast_route_layers_and_grid", "one_based"),
    ("no_physical_cut_capacity", "physical_cut_capacity"),
    ("GRID\t2\t2\t1", "GRID\t1\t2\t1"),
    ("GRID\t2\t2\t1", "GRID\t2\t2\t65"),
    ("-10\t20\t100", "-10\t20\t0"),
    ("EDGE\tH\t0\t0\t1", "EDGE\tH\t0\t0\t0"),
    ("EDGE\tV\t0\t1\t0", "EDGE\tV\t0\t2\t0"),
    ("1\t2\t3\t4", "1\t2\t3\t65536"),
    ("1\t2\t3\t4", "1\t-1\t3\t4"),
    ("1\t2\t3\t4", "1\t2.0\t3\t4"),
    ("1\t2\t3\t4", "1\t+2\t3\t4"),
    ("NET\t0\t11", "NET\t1\t11"),
    ("NET\t0\t11", "NET\t0\t0"),
    ("net 0\t1\t0\t3", "net 0\t2\t0\t3"),
    ("net 0\t1\t0\t3", "net 0\t1\t0\t128"),
    ("net 0\t1\t0\t3", "net 0\t1\t0\t-1"),
    ("DEMAND\t0\t0\t2", "DEMAND\t0\t1\t2"),
    ("DEMAND\t0\t0\t2", "DEMAND\t0\t0\t-1"),
    ("PIN\t0\t1\t1\t0\t0", "PIN\t0\t2\t1\t0\t0"),
    ("PIN\t0\t1\t1\t0\t0", "PIN\t0\t1\t2\t0\t0"),
    ("TREE\t0\t2\t2\t1", "TREE\t0\t3\t2\t1"),
    ("TREE\t0\t2\t2\t1", "TREE\t0\t2\t1\t1"),
    ("TREE_EDGE\t0\t0", "TREE_EDGE\t0\t1"),
    ("TREE_EDGE\t0\t0\t1\t0\t1", "TREE_EDGE\t0\t0\t1\t0\t2"),
    ("\t1\t2\nSTEP", "\t1\t1\nSTEP"),
    ("STEP\t0\t0\t0", "STEP\t0\t0\t1"),
    ("STEP\t0\t0\t0\t0\t0\t0\t1\t0\t0\t2", "STEP\t0\t0\t0\t0\t0\t0\t0\t0\t0\t2"),
    ("STEP\t0\t0\t0\t0\t0\t0\t1\t0\t0\t2", "STEP\t0\t0\t0\t0\t0\t0\t1\t1\t0\t2"),
    ("STEP\t0\t0\t0\t0\t0\t0\t1\t0\t0\t2", "STEP\t0\t0\t0\t0\t0\t0\t1\t0\t0\t1"),
    ("COMPLETE\t1\t1\t1", "COMPLETE\t1\t1\t0"),
    ("COMPLETE\t1\t1\t1", "COMPLETE\t2\t1\t1"),
])
def test_malformed_field_bounds_costs_census_fail_closed(old, new):
    with pytest.raises(n.FormatError):
        n.parse_bytes(replace(fixture(), old, new))


@pytest.mark.parametrize("kind", ["EDGE", "DEMAND", "PIN", "TREE", "TREE_EDGE", "STEP", "COMPLETE"])
def test_missing_rows_are_not_inferred(kind):
    lines = fixture().decode().splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith(kind + "\t"))
    del lines[index]
    with pytest.raises(n.FormatError):
        n.parse_bytes(("\n".join(lines) + "\n").encode())


def test_native_name_and_db_identity_must_be_unique():
    raw = fixture(two_nets=True)
    for old, new in [("NET\t1\t12\tnet 1", "NET\t1\t11\tnet 1"),
                     ("NET\t1\t12\tnet 1", "NET\t1\t12\tnet 0")]:
        with pytest.raises(n.FormatError):
            n.parse_bytes(replace(raw, old, new))


def test_missing_or_misordered_empty_slot_rejected():
    with pytest.raises(n.FormatError):
        n.parse_bytes(replace(fixture(empty_slot=True), "EMPTY_SLOT\t1", "EMPTY_SLOT\t2"))


def test_tree_step_sequence_continuity_required():
    raw = fixture(multiplicity=3)
    raw = replace(raw, "STEP\t0\t0\t1\t1\t0\t0\t0\t0\t0\t2",
                  "STEP\t0\t0\t1\t0\t0\t0\t1\t0\t0\t2")
    with pytest.raises(n.FormatError, match="discontinuous"):
        n.parse_bytes(raw)


@pytest.mark.parametrize("newcoords", ["0\t0\t0\t0\t0\t1\t2", "0\t0\t0\t1\t0\t1\t0"])
def test_via_nonzero_demand_or_planar_motion_rejected(newcoords):
    raw = replace(fixture(layers=2, via=True), "0\t0\t0\t0\t0\t1\t0\nCOMPLETE", newcoords + "\nCOMPLETE")
    with pytest.raises(n.FormatError):
        n.parse_bytes(raw)


def test_nonadjacent_via_inside_valid_global_layer_bounds_rejected():
    raw = replace(fixture(layers=3, via=True), "0\t0\t0\t0\t0\t1\t0\nCOMPLETE",
                  "0\t0\t0\t0\t0\t2\t0\nCOMPLETE")
    with pytest.raises(n.FormatError, match="adjacent-layer via"):
        n.parse_bytes(raw)


@pytest.mark.parametrize("mutate", [lambda raw: raw[:-1], lambda raw: raw + b"\n", lambda raw: raw + b"EXTRA\n",
                                    lambda raw: raw.replace(b"\n", b"\r\n"), lambda raw: raw + b"\x00",
                                    lambda raw: raw.replace(b"net 0", b"net\x01"), lambda raw: raw.replace(b"net 0", b"\xff")])
def test_bad_encoding_trailing_data_and_incomplete_file_rejected(mutate):
    with pytest.raises(n.FormatError):
        n.parse_bytes(mutate(fixture()))


def test_uint16_wrap_is_mismatch_not_modular_reconciliation():
    # Deliberately fabricate a parsed internal fixture to test >65535 arithmetic
    # without a 32K-row text fixture. Multiset count32769 at cost2 gives65538.
    snapshot = n.parse_bytes(fixture())
    snapshot.nets[0]["planar_step_multiplicity"][("H", 0, 0, 0)] = 32769
    report = n.audit(snapshot)
    assert report["model_gate"] == "FAIL"
    assert report["reconciliation"]["possible_uint16_wrap_edges"] == 1
    assert report["reconciliation"]["excess_step_contributions"] == 65536


def test_zero_demand_is_retained_but_not_solver_compatible():
    raw = replace(fixture(raw_usage=0), "DEMAND\t0\t0\t2", "DEMAND\t0\t0\t0")
    raw = replace(raw, "STEP\t0\t0\t0\t0\t0\t0\t1\t0\t0\t2", "STEP\t0\t0\t0\t0\t0\t0\t1\t0\t0\t0")
    report = n.audit(n.parse_bytes(raw))
    assert report["usage_ledger_reconciled"]
    assert report["zero_layer_demand_count"] == 1
    assert not report["solver_union_accounting_compatible"]


def test_cli_writes_model_gate_failure_with_nonzero_exit(tmp_path):
    path, output = tmp_path / "native.tsv", tmp_path / "audit.json"
    path.write_bytes(fixture(raw_usage=5))
    assert n.main([str(path), "--output", str(output)]) == 1
    report = json.loads(output.read_text())
    assert report["format_verified"] and report["model_gate"] == "FAIL"
    path.write_bytes(fixture())
    assert n.main([str(path), "--output", str(output)]) == 0
    assert n.audit_file(path)["usage_ledger_reconciled"]
