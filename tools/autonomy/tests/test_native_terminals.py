"""Hand-computed TSV joins; no native execution or physical qualification."""
import copy
import hashlib

import pytest

from autonomy import native_corridor as raw
from autonomy import native_terminals as n


def fixture(*, duplicate=False, supported=True, steiner=False, empty=False, outside=False):
    # Nonzero origin and pitch exercise the exact native DBU conversion.
    rows = ["SCHEMA\twarp-native-corridor-v1", "INDEXING\tzero_based_fast_route_layers_and_grid",
            "MODEL_GATE\tusage_ledger_verified\tfalse", "VIA_MODEL\tglobal_route_steps_only_no_physical_cut_capacity",
            "GRID\t2\t2\t2\t-10\t20\t100"]
    for layer in range(2):
        for axis, x, y in [("H", 0, 0), ("H", 0, 1), ("V", 0, 0), ("V", 1, 0)]:
            rows.append(f"EDGE\t{axis}\t{layer}\t{x}\t{y}\t3\t{int(layer == 0 and axis == 'H' and y == 0)}\t0\t0")
    nodes = 3 if steiner else 2
    rows += ["NET\t0\t11\tnet a\t0\t0\t1\t0\t1\t0\t2", "DEMAND\t0\t0\t1", "DEMAND\t0\t1\t1",
             "PIN\t0\t0\t0\t0\t0", "PIN\t0\t1\t1\t0\t0", f"TREE\t0\t2\t{nodes}\t1",
             "TREE_EDGE\t0\t0\t1\t0\t1\t0\t1\t1\t2", "STEP\t0\t0\t0\t0\t0\t0\t1\t0\t0\t1"]
    if empty:
        rows += ["EMPTY_SLOT\t1"]
    rows += [f"COMPLETE\t{1 + int(empty)}\t1\t1"]
    raw_bytes = ("\n".join(rows) + "\n").encode()
    count = 3 if duplicate else 2
    t = ["SCHEMA\twarp-native-terminals-v1", "MODEL_GATE\tterminal_join_verified\tfalse",
         "SCOPE\tcoarse_pin_membership_and_tree_access_not_physical_via_feasibility",
         "INDEXING\tnative_layers_zero_based_database_routing_levels_one_based", "DBU\t1000",
         "GLOBAL_GRID\t2\t2\t2\t-10\t20\t100", "LAYER\t0\t7\t1\tMetal1\tHORIZONTAL",
         "LAYER\t1\t8\t2\tMetal2\tVERTICAL", f"DATABASE_NET\t11\tnet a\t0\t0\t0\t1\t0\t0\t{count}"]
    if outside:
        t += ["DATABASE_NET\t12\tsupply\t1\t1\t0\t0\t-1\t1\t0"]
    t += [f"DATABASE_COMPLETE\t{1 + int(outside)}", f"GLOBAL_NET\t11\tnet a\t0\t0\t0\t{count}\t{count}\t1\t1\t1\t0"]
    # Duplicate driver at ordinal1 must NOT change the root to another index.
    locations = [(0, 0), (0, 1), (1, 0)] if duplicate else [(0, 0), (1, 0)]
    for ordinal, (x, driver) in enumerate(locations):
        t += [f"GLOBAL_PIN\t11\t{ordinal}\tBTERM\t{ordinal + 31}\t0\t0\tp{ordinal}\t{driver}\t{-10 + x * 100}\t20\t3\t1\t{x}\t0\t1\t0\t1",
              f"MEMBER\t11\t{ordinal}\t0\t{x}"]
    t += [f"GLOBAL_COMPLETE\t1\t{count}\t{count}", "NATIVE_GRID\t2\t2\t2\t-10\t20\t100",
          f"NATIVE_NET\t0\t11\tnet a\t2\t0\t1\t0\t2\t{nodes}\t1\t2",
          f"TREE_ACCESS_SUPPORTED\t0\t{int(supported)}", "NATIVE_PIN\t0\t0\t0\t0\t0", "NATIVE_PIN\t0\t1\t1\t0\t0"]
    for node, (x, y) in enumerate([(0, 0), (1, 0)] + ([(0, 1)] if steiner else [])):
        if supported:
            t += [f"NODE\t0\t{node}\t{x}\t{y}\t{node}\t{2 if node == 2 else 0}\t{-1 if node == 2 else 0}\t10000000\t-1",
                  f"VIA_RANGE\t0\t{node}\t{'32767' if node == 2 else '0'}\t{-1 if node == 2 else 0}\t{0 if node == 2 else 1}"]
        else:
            t += [f"NODE_UNSUPPORTED\t0\t{node}\tno_initialized_routed_tree_access_contract"]
    # Deliberately reverse unordered map iteration: no invented ordering rule.
    t += ["NODE_PIN\t0\t1\t1", "NODE_PIN\t0\t0\t0"]
    if empty:
        t += ["NATIVE_EMPTY_SLOT\t1"]
    t += [f"NATIVE_COMPLETE\t{1 + int(empty)}\t1\t{nodes}\t2", "COMPLETE\twarp-native-terminals-v1"]
    return raw_bytes, ("\n".join(t) + "\n").encode()


def change(b, old, new):
    assert old.encode() in b
    return b.replace(old.encode(), new.encode(), 1)


def joined(rb, tb):
    return n.audit_join(raw.parse_bytes(rb), n.parse_bytes(tb))


def test_full_hand_computed_join_and_hashes(tmp_path):
    rb, tb = fixture(empty=True)
    rp, tp = tmp_path / "raw.tsv", tmp_path / "term.tsv"
    rp.write_bytes(rb)
    tp.write_bytes(tb)
    report = n.audit_files(rp, tp)
    assert report["model_gate"] == "PASS" and report["terminal_join_verified"]
    assert report["native_sha256"] == hashlib.sha256(rb).hexdigest()
    assert report["terminal_sha256"] == hashlib.sha256(tb).hexdigest()
    assert (report["database_nets"], report["global_nets"], report["native_nets"], report["physical_pins"], report["memberships"], report["tree_nodes"], report["native_empty_slots"]) == (1, 1, 1, 2, 2, 2, 1)
    assert not report["native_inputs_authenticated"] and not report["physical_acceptance"] and not report["timing_acceptance"]
    assert report["layers"][1]["direction"] == "VERTICAL"


def test_duplicate_physical_driver_uses_first_unique_native_construction():
    assert joined(*fixture(duplicate=True))["model_gate"] == "PASS"


def test_steiner_pinless_range_and_edgeid_sentinels_are_not_terminal_failures():
    report = joined(*fixture(steiner=True))
    assert report["model_gate"] == "PASS"


def test_valid_unsupported_tree_access_is_diagnostic():
    report = joined(*fixture(supported=False))
    assert report["model_gate"] == "FAIL"
    assert report["unsupported_access"] == [dict(reason="unsupported_tree_access", slot=0)]


def test_database_pins_outside_globalmap_remain_unavailable():
    report = joined(*fixture(outside=True))
    assert report["model_gate"] == "FAIL"
    assert report["unsupported_access"][-1] == dict(reason="database_net_membership_unavailable", db_id=12)


@pytest.mark.parametrize("old,new", [
    ("SCHEMA\twarp-native-terminals-v1", "SCHEMA\tother"),
    ("terminal_join_verified\tfalse", "terminal_join_verified\ttrue"),
    ("LAYER\t1\t8\t2", "LAYER\t1\t7\t2"),
    ("Metal2\tVERTICAL", "Metal1\tVERTICAL"),
    ("LAYER\t1\t8\t2", "LAYER\t1\t8\t1"),
    ("Metal2\tVERTICAL", "Metal2\tDIAGONAL"),
    ("DATABASE_COMPLETE\t1", "DATABASE_COMPLETE\t2"),
    ("GLOBAL_COMPLETE\t1\t2\t2", "GLOBAL_COMPLETE\t1\t2\t1"),
    ("NATIVE_COMPLETE\t1\t1\t2\t2", "NATIVE_COMPLETE\t1\t1\t3\t2"),
    ("DATABASE_NET\t11\tnet a\t0\t0\t0\t1", "DATABASE_NET\t11\tnet a\t0\t0\t0\t0"),
    ("BTERM\t32\t0\t0", "BTERM\t31\t0\t0"),
    ("BTERM\t31\t0\t0\tp0\t0", "BTERM\t31\t0\t0\tp0\t-1"),
    ("BTERM\t31\t0\t0", "BTERM\t31\t1\t0"),
    ("NATIVE_GRID\t2\t2\t2\t-10", "NATIVE_GRID\t2\t2\t2\t0"),
    ("NATIVE_PIN\t0\t1\t1", "NATIVE_PIN\t0\t0\t1"),
    ("VIA_RANGE\t0\t0\t0\t0\t1", "VIA_RANGE\t0\t0\t0\t1\t1"),
    ("NODE_PIN\t0\t1\t1", "NODE_PIN\t0\t0\t1"),
    ("NODE_PIN\t0\t1\t1", "NODE_PIN\t0\t1\t2"),
    ("TREE_ACCESS_SUPPORTED\t0\t1", "TREE_ACCESS_SUPPORTED\t0\t2"),
    ("DBU\t1000", "DBU\t0"),
    ("DBU\t1000", "DBU\t01000"),
])
def test_malformed_census_and_identity_rejected(old, new):
    _, tb = fixture()
    with pytest.raises(n.FormatError):
        n.parse_bytes(change(tb, old, new))


@pytest.mark.parametrize("old,new", [
    ("20\t3\t1\t0\t0\t1", "20\t3\t2\t0\t0\t1"),  # wrong clamp
    ("-10\t20\t3\t1", "90\t20\t3\t1"),  # wrong native coordinate arithmetic
    ("3\t1\t0\t0\t1\t0\t1", "3\t1\t0\t0\t0\t0\t1"),
    ("MEMBER\t11\t0\t0\t0", "MEMBER\t11\t0\t0\t1"),
    ("NODE_PIN\t0\t1\t1", "NODE_PIN\t0\t1\t0"),
])
def test_crossjoin_contradictions_rejected(old, new):
    rb, tb = fixture()
    with pytest.raises(n.FormatError):
        joined(rb, change(tb, old, new))


def test_signed_cxx_division_truncates_towards_zero():
    rb, tb = fixture()
    # x=-109-origin(-10)=-99; C++ -99/100==0, Python // would be-1.
    tb = change(tb, "p0\t0\t-10\t20", "p0\t0\t-109\t20")
    assert joined(rb, tb)["model_gate"] == "PASS"


def test_driver_after_unique_new_pin_updates_root_and_bad_root_rejected():
    rb, tb = fixture()
    tb = change(tb, "p1\t0\t90", "p1\t1\t90")
    with pytest.raises(n.FormatError, match="driver"):
        joined(rb, tb)
    rb = change(rb, "NET\t0\t11\tnet a\t0\t0\t1\t0\t1\t0\t2", "NET\t0\t11\tnet a\t0\t0\t1\t0\t1\t1\t2")
    tb = change(tb, "NATIVE_NET\t0\t11\tnet a\t2\t0\t1\t0", "NATIVE_NET\t0\t11\tnet a\t2\t0\t1\t1")
    assert joined(rb, tb)["model_gate"] == "PASS"


@pytest.mark.parametrize("ids", ["0\t0\t0", "31\t0\t0"])
def test_unresolved_iterm_ids_are_preserved_diagnostic(ids):
    rb, tb = fixture()
    tb = change(tb, "BTERM\t31\t0\t0\tp0\t0", f"ITERM\t{ids}\tUNRESOLVED\t-1")
    tb = change(tb, "DATABASE_NET\t11\tnet a\t0\t0\t0\t1\t0\t0\t2", "DATABASE_NET\t11\tnet a\t0\t0\t0\t1\t0\t1\t1")
    report = joined(rb, tb)
    assert report["model_gate"] == "FAIL"
    assert any(x["reason"] == "unresolved_physical_pin" for x in report["unsupported_access"])


@pytest.mark.parametrize("old,new,reason", [
    ("NODE\t0\t0\t0\t0\t0\t0\t0", "NODE\t0\t0\t0\t0\t0\t2\t-1", "terminal_access_layer_sentinel"),
    ("NODE\t0\t0\t0\t0\t0", "NODE\t0\t0\t0\t0\t-1", "unsupported_stack_alias"),
    ("NODE_PIN\t0\t0\t0", "NODE_PIN\t0\t0\t-1", "unresolved_node_pin_mapping"),
])
def test_native_sentinels_diagnostic_not_repaired(old, new, reason):
    rb, tb = fixture()
    report = joined(rb, change(tb, old, new))
    assert report["model_gate"] == "FAIL"
    assert any(x["reason"] == reason for x in report["unsupported_access"])


@pytest.mark.parametrize("mutation", [lambda b: b[:-1], lambda b: b + b"EXTRA\tx\n", lambda b: b.replace(b"\n", b"\r\n"), lambda b: b + b"\x00", lambda b: b.replace(b"net a", b"\xff")])
def test_encoding_and_completion_fail_closed(mutation):
    with pytest.raises(n.FormatError):
        n.parse_bytes(mutation(fixture()[1]))


@pytest.mark.parametrize("field,value", [("name", "other"), ("db_id", 12), ("minimum_layer", 1), ("driver_index", 1), ("tree_nodes", 3), ("tree_terminals", 1), ("pins", [(0, 0, 1), (1, 0, 0)])])
def test_independent_raw_checkpoint_must_crossjoin(field, value):
    rb, tb = fixture()
    snapshot = copy.deepcopy(raw.parse_bytes(rb))
    snapshot.nets[0][field] = value
    with pytest.raises(n.FormatError):
        n.audit_join(snapshot, n.parse_bytes(tb))


def colocated_layer_fixture():
    rb, tb = fixture()
    rb = change(rb, "PIN\t0\t1\t1\t0\t0", "PIN\t0\t1\t0\t0\t1")
    tb = change(tb, "GLOBAL_NET\t11\tnet a\t0\t0\t0\t2\t2\t1", "GLOBAL_NET\t11\tnet a\t0\t0\t0\t2\t2\t2")
    tb = change(tb, "p0\t0\t-10\t20\t3\t1", "p0\t0\t-10\t20\t1\t1")
    tb = change(tb, "p1\t0\t90\t20\t3\t1\t1\t0", "p1\t0\t-10\t20\t3\t2\t0\t0")
    tb = change(tb, "NATIVE_PIN\t0\t1\t1\t0\t0", "NATIVE_PIN\t0\t1\t0\t0\t1")
    tb = change(tb, "NODE\t0\t1\t1\t0", "NODE\t0\t1\t0\t0")
    tb = change(tb, "VIA_RANGE\t0\t0\t0\t0\t1", "VIA_RANGE\t0\t0\t0\t1\t2")
    tb = change(tb, "VIA_RANGE\t0\t1\t0\t0\t1", "VIA_RANGE\t0\t1\t0\t1\t2")
    return rb, tb


def test_colocated_multilayer_pins_join_by_occurrence_not_xy_alone():
    rb, tb = colocated_layer_fixture()
    assert joined(rb, tb)["model_gate"] == "PASS"
    tb = change(tb, "NODE_PIN\t0\t1\t1", "NODE_PIN\t0\t1\t0")
    with pytest.raises(n.FormatError, match="occurrence-order/layer"):
        joined(rb, tb)


def test_stack_alias_must_refer_to_same_coordinate():
    rb, tb = fixture()
    tb = change(tb, "NODE\t0\t0\t0\t0\t0", "NODE\t0\t0\t0\t0\t1")
    with pytest.raises(n.FormatError, match="stack alias coordinate"):
        joined(rb, tb)


def test_merged_membership_remains_explicitly_unsupported():
    rb, tb = fixture()
    tb = change(tb, "GLOBAL_NET\t11\tnet a\t0\t0\t0", "GLOBAL_NET\t11\tnet a\t0\t1\t0")
    report = joined(rb, tb)
    assert report["model_gate"] == "FAIL"
    assert any(v["reason"] == "merged_tree_membership_not_authenticated" for v in report["unsupported_access"])


def test_declared_pin_coverage_mismatch_not_silently_accepted():
    rb, tb = fixture()
    tb = change(tb, "DATABASE_NET\t11\tnet a\t0\t0\t0\t1\t0\t0\t2", "DATABASE_NET\t11\tnet a\t0\t0\t0\t1\t0\t0\t3")
    report = joined(rb, tb)
    assert report["model_gate"] == "FAIL"
    assert any(v["reason"] == "database_physical_pin_coverage_unavailable" for v in report["unsupported_access"])


def test_parse_bounds_without_allocating_giant_input(monkeypatch):
    _, tb = fixture()
    monkeypatch.setattr(raw, "MAX_BYTES", len(tb) - 1)
    with pytest.raises(n.FormatError, match="byte limit"):
        n.parse_bytes(tb)


def test_database_clock_and_nonleaf_global_clock_have_distinct_semantics():
    rb, tb = fixture()
    rb = change(rb, "NET\t0\t11\tnet a\t0\t0", "NET\t0\t11\tnet a\t1\t0")
    with pytest.raises(n.FormatError, match="signal-type clock"):
        joined(rb, tb)
    tb = change(tb, "DATABASE_NET\t11\tnet a\t0\t0\t0", "DATABASE_NET\t11\tnet a\t0\t0\t1")
    # Valid leaf clock: GLOBAL_NET isClockNet=false, DB signal-type CLOCK=true.
    assert joined(rb, tb)["model_gate"] == "PASS"
    tb = change(tb, "GLOBAL_NET\t11\tnet a\t0\t0\t0", "GLOBAL_NET\t11\tnet a\t0\t0\t1")
    assert joined(rb, tb)["model_gate"] == "PASS"
