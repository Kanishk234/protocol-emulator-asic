"""Strict cross-snapshot identity for the three controlled native routing cases.

This binds exported native IDs/coarse pins/costs/trees/resources, not physical pin
membership, PDK identity, capacity-ledger reconciliation, or routing acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from . import native_corridor as native

CASES = ("default_identity", "forced_pair", "rebuilt_pair")
PHASES = ("initial", "final")


class CheckpointError(ValueError):
    """The required unchanged native state was not reproduced exactly."""


def _digest_rows(rows):
    digest = hashlib.sha256()
    for row in rows:
        digest.update(json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def fingerprint(path: Path) -> dict:
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise CheckpointError(f"native snapshot must be a regular non-symlink file: {path}")
    with path.open("rb") as stream:
        snapshot = native.parse_bytes(stream.read(native.MAX_BYTES + 1))
    # parse_bytes already validates unique IDs/names, complete slot membership,
    # pin indices/bounds, cost layers, trees and steps. These separate digests
    # explain a failed exact-byte identity check; they never replace it.
    nets = list(snapshot.nets.items())
    groups = {
        "resource_sha256": _digest_rows([snapshot.grid] + [[key, value] for key, value in snapshot.edges.items()]),
        "net_id_sha256": _digest_rows([[snapshot.empty_slots]] + [[slot, net["db_id"], net["name"]] for slot, net in nets]),
        "terminal_sha256": _digest_rows([[slot, net["db_id"], net["name"], net["pins"], net["driver_index"],
                                           net["tree_terminals"], net["tree_nodes"]] for slot, net in nets]),
        "cost_sha256": _digest_rows([[slot, net["clock"], net["soft_ndr"], net["scalar_cost"], net["demands"],
                                       net["minimum_layer"], net["maximum_layer"]] for slot, net in nets]),
        "tree_ledger_sha256": _digest_rows([[slot, net["tree_edges"], sorted(net["planar_step_multiplicity"].items()),
                                              net["via_steps"]] for slot, net in nets]),
    }
    return {"file_sha256": snapshot.sha256, "groups": groups, "grid": list(snapshot.grid),
            "live_nets": len(nets), "empty_slots": len(snapshot.empty_slots),
            "coarse_pin_count": sum(len(net["pins"]) for _, net in nets),
            "native_pin_id_census_verified": True,
            "physical_pin_join_authenticated": False}


def audit(paths: dict) -> dict:
    """Parse all six files, compare four unchanged snapshots, allow repair finals.

    `paths` has exactly CASES, each mapping initial/final to native TSV Paths.
    Any required difference raises CheckpointError. Accounting remains a separate
    native_corridor.audit_file gate, including for the permitted changed finals.
    """
    if not isinstance(paths, dict) or set(paths) != set(CASES):
        raise CheckpointError("require exactly default_identity, forced_pair, rebuilt_pair")
    observations = {}
    for case in CASES:
        if not isinstance(paths[case], dict) or set(paths[case]) != set(PHASES):
            raise CheckpointError(f"{case}: require exactly initial and final snapshots")
        observations[case] = {phase: fingerprint(paths[case][phase]) for phase in PHASES}
    reference = observations["default_identity"]["initial"]
    comparisons = []
    for case, phase in [(case, "initial") for case in CASES[1:]] + [("default_identity", "final")]:
        candidate = observations[case][phase]
        changed = [key for key in reference["groups"] if reference["groups"][key] != candidate["groups"][key]]
        if candidate["file_sha256"] != reference["file_sha256"]:
            detail = ", ".join(changed) if changed else "raw bytes/step geometry not represented by summary groups"
            raise CheckpointError(f"{case}/{phase} differs from default_identity/initial: {detail}; "
                                  f"{candidate['file_sha256']} != {reference['file_sha256']}")
        comparisons.append({"case": case, "phase": phase, "byte_identical": True})
    return {"schema_version": 1, "checkpoint_identity_verified": True,
            "reference_sha256": reference["file_sha256"], "comparisons": comparisons,
            "observations": observations, "repaired_finals_required_identical": False,
            "native_inputs_authenticated": False, "physical_pin_join_authenticated": False,
            "usage_ledger_reconciliation_verified": False, "physical_acceptance": False,
            "scope": "Exact native snapshot identity and internal ID/coarse-pin census only"}


def bundle_paths(root: Path) -> dict:
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise CheckpointError("bundle root must be a regular directory")
    paths = {}
    for case in CASES:
        replay = root/case/"replay"
        if (root/case).is_symlink() or replay.is_symlink():
            raise CheckpointError("symlink case/replay directory")
        stages = list(replay.glob("*-openroad-globalrouting"))
        if len(stages) != 1 or not stages[0].is_dir() or stages[0].is_symlink():
            raise CheckpointError(f"{case}: require exactly one native routing stage")
        paths[case] = {}
        for phase in PHASES:
            directory = stages[0]/("corridor-" + phase)
            if not directory.is_dir() or directory.is_symlink() or {p.name for p in directory.iterdir()} != {"native-corridor.tsv"}:
                raise CheckpointError(f"{case}/{phase}: invalid export inventory")
            paths[case][phase] = directory/"native-corridor.tsv"
    return paths


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit(bundle_paths(args.bundle))
    except (CheckpointError, native.FormatError, OSError) as exc:
        parser.exit(2, f"native checkpoint audit: {exc}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
