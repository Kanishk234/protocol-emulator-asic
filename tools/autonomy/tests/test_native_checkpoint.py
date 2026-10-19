"""Exact unchanged-state guards; fixtures have no native WARP provenance."""
import json

import pytest

from autonomy import native_checkpoint as c
from autonomy import native_corridor as n


BASE = """SCHEMA	warp-native-corridor-v1
INDEXING	zero_based_fast_route_layers_and_grid
MODEL_GATE	usage_ledger_verified	false
VIA_MODEL	global_route_steps_only_no_physical_cut_capacity
GRID	2	2	1	0	0	10
EDGE	H	0	0	0	1	1	0	1
EDGE	H	0	0	1	0	0	0	0
EDGE	V	0	0	0	0	0	0	0
EDGE	V	0	1	0	0	0	0	0
NET	0	17	fixture	0	0	3	0	0	0	2
DEMAND	0	0	1
PIN	0	0	0	0	0
PIN	0	1	1	0	0
TREE	0	2	2	1
TREE_EDGE	0	0	1	0	1	0	1	1	2
STEP	0	0	0	0	0	0	1	0	0	1
COMPLETE	1	1	1
"""


@pytest.fixture
def bundle(tmp_path):
    for case in c.CASES:
        for phase in c.PHASES:
            directory = tmp_path/case/"replay"/"1-openroad-globalrouting"/("corridor-" + phase)
            directory.mkdir(parents=True)
            (directory/"native-corridor.tsv").write_text(BASE)
    return tmp_path


def test_all_initials_and_unchanged_default_final_bind_exactly(bundle):
    result = c.audit(c.bundle_paths(bundle))
    assert result["checkpoint_identity_verified"] and len(result["comparisons"]) == 3
    assert result["observations"]["default_identity"]["initial"]["coarse_pin_count"] == 2
    assert not result["physical_pin_join_authenticated"]
    assert not result["native_inputs_authenticated"] and not result["usage_ledger_reconciliation_verified"]
    assert not result["physical_acceptance"]


@pytest.mark.parametrize("case,phase", [("forced_pair", "initial"), ("rebuilt_pair", "initial"), ("default_identity", "final")])
@pytest.mark.parametrize("old,new,group", [
    ("NET\t0\t17", "NET\t0\t18", "net_id_sha256"),
    ("fixture\t0\t0\t3", "renamed\t0\t0\t3", "net_id_sha256"),
    ("fixture\t0\t0\t3", "fixture\t0\t0\t4", "cost_sha256"),
    ("PIN\t0\t1\t1\t0\t0", "PIN\t0\t1\t0\t1\t0", "terminal_sha256"),
    ("1\t1\t0\t1\nEDGE", "1\t2\t0\t1\nEDGE", "resource_sha256"),
    ("STEP\t0\t0\t0\t0\t0\t0\t1\t0\t0\t1", "STEP\t0\t0\t0\t1\t0\t0\t0\t0\t0\t1", "raw bytes"),
])
def test_every_required_identity_difference_rejects(bundle, case, phase, old, new, group):
    paths = c.bundle_paths(bundle)
    paths[case][phase].write_text(BASE.replace(old, new, 1))
    with pytest.raises(c.CheckpointError, match=group):
        c.audit(paths)


def test_repair_finals_may_change_without_relaxing_initial_identity(bundle):
    paths = c.bundle_paths(bundle)
    for case in c.CASES[1:]:
        paths[case]["final"].write_text(BASE.replace("fixture\t0\t0\t3", "fixture\t0\t0\t4"))
    result = c.audit(paths)
    assert result["checkpoint_identity_verified"]
    assert not result["repaired_finals_required_identical"]


def test_repair_final_format_still_must_validate(bundle):
    paths = c.bundle_paths(bundle)
    paths["forced_pair"]["final"].write_text(BASE.replace("DEMAND\t0\t0\t1", "DEMAND\t0\t0\t-1"))
    with pytest.raises(n.FormatError):
        c.audit(paths)


def test_identity_does_not_waive_independent_usage_ledger(bundle):
    paths = c.bundle_paths(bundle)
    mismatch = BASE.replace("1\t1\t0\t1\nEDGE", "1\t2\t0\t1\nEDGE")
    for case in c.CASES:
        for phase in c.PHASES:
            paths[case][phase].write_text(mismatch)
    assert c.audit(paths)["checkpoint_identity_verified"]
    assert n.audit_file(paths["default_identity"]["initial"])["model_gate"] == "FAIL"


@pytest.mark.parametrize("case", ["forced_pair", "rebuilt_pair"])
@pytest.mark.parametrize("replacement", [
    "EDGE\tV\t0\t1\t0\t1\t0\t0\t0",  # nonpreferred capacity
    "EDGE\tV\t0\t1\t0\t0\t0\t1\t0",  # reduction
    "EDGE\tV\t0\t1\t0\t0\t0\t0\t1",  # real capacity
])
def test_changed_repair_final_cannot_change_raw_resource_fields(bundle, case, replacement):
    paths = c.bundle_paths(bundle)
    path = paths[case]["final"]
    path.write_text(BASE.replace("EDGE\tV\t0\t1\t0\t0\t0\t0\t0", replacement))
    with pytest.raises(c.CheckpointError, match="raw capacity/reduction/real-capacity"):
        c.audit(paths)


def test_missing_case_or_phase_rejected(bundle):
    paths = c.bundle_paths(bundle)
    del paths["forced_pair"]["final"]
    with pytest.raises(c.CheckpointError):
        c.audit(paths)
    del paths["forced_pair"]
    with pytest.raises(c.CheckpointError):
        c.audit(paths)


def test_extra_export_file_rejected(bundle):
    path = c.bundle_paths(bundle)["forced_pair"]["initial"]
    (path.parent/"extra.tsv").write_text("extra")
    with pytest.raises(c.CheckpointError, match="inventory"):
        c.bundle_paths(bundle)


def test_extra_replay_stage_rejected(bundle):
    (bundle/"forced_pair"/"replay"/"2-openroad-globalrouting").mkdir()
    with pytest.raises(c.CheckpointError, match="exactly one"):
        c.bundle_paths(bundle)


def test_symlink_export_rejected(bundle):
    paths = c.bundle_paths(bundle)
    target = paths["default_identity"]["initial"]
    path = paths["forced_pair"]["initial"]
    path.unlink()
    path.symlink_to(target)
    with pytest.raises(c.CheckpointError, match="non-symlink"):
        c.audit(paths)


def test_cli_produces_scoped_result(bundle, tmp_path):
    output = tmp_path/"result.json"
    assert c.main([str(bundle), "--output", str(output)]) == 0
    result = json.loads(output.read_text())
    assert result["checkpoint_identity_verified"]
    assert not result["native_inputs_authenticated"]
