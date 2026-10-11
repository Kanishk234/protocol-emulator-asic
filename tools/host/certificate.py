"""Combine audited compiler evidence and an analytical host service budget.

The artifact is a planning certificate, not timing signoff or measured rate
certification. Compiler timing, resource fit and host service are separate.
"""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

import yaml

from board.budget import plan
from compile.audit import audit


def _count(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(label + " must be a nonnegative integer")
    return value


def certificate(report_path, architecture_path, budget_inputs):
    """Generate a self-consistency artifact using current compiler schema.

    Paths in compiler provenance use its existing working-directory convention.
    Hash agreement is not independent authentication of compiler assertions.
    """
    report_path, architecture_path = Path(report_path), Path(architecture_path)
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes)
    architecture_bytes = architecture_path.read_bytes()
    architecture = yaml.safe_load(architecture_bytes)
    if not isinstance(architecture, dict) or not isinstance(report, dict):
        raise ValueError("report and architecture must be objects")
    if not isinstance(report.get("design"), str) or not report["design"]:
        raise ValueError("missing compiler design identity")
    if not isinstance(report.get("pins"), dict):
        raise ValueError("missing compiler pin mapping")
    try:
        problems = audit(report_path)
    except (KeyError, TypeError) as exc:
        raise ValueError("malformed compiler provenance") from exc
    if problems:
        raise ValueError("compile evidence audit failed: " + "; ".join(problems))
    if report_path.read_bytes() != report_bytes:
        raise ValueError("compiler report changed during audit")
    if report.get("arch") != architecture.get("name"):
        raise ValueError("architecture name disagrees with compile report")
    version = architecture.get("arch_version")
    _count(version, "architecture version")
    if report.get("arch_version") != f"0x{version:04X}":
        raise ValueError("architecture version disagrees with compile report")
    arch_hash = hashlib.sha256(architecture_bytes).hexdigest()
    inputs = report["provenance"]["inputs"]
    if not any(Path(entry["path"]).resolve() == architecture_path.resolve()
               and entry["sha256"] == arch_hash for entry in inputs):
        raise ValueError("selected architecture is not a hashed compiler input")
    resources = report.get("utilisation")
    if not isinstance(resources, dict) or "FABULOUS_LC" not in resources:
        raise ValueError("missing compiler resource utilisation")
    capacities = {"FABULOUS_LC": _count(architecture.get("luts"), "architecture LUTs")}
    primitives = architecture.get("primitives", {})
    if not isinstance(primitives, dict):
        raise ValueError("architecture primitives must be an object")
    capacities.update({key: _count(value, key + " capacity") for key, value in primitives.items()})
    for name, resource in resources.items():
        if not isinstance(resource, dict):
            raise ValueError("malformed resource " + name)
        used = _count(resource.get("used"), name + " used")
        available = _count(resource.get("available"), name + " available")
        if used > available:
            raise ValueError("resource over capacity: " + name)
        if name in capacities and available != capacities[name]:
            raise ValueError("resource capacity disagrees with architecture: " + name)
    if any(name not in resources for name in capacities):
        raise ValueError("missing architecture resource in compiler utilisation")
    fmax = report.get("fmax_mhz")
    if fmax is not None and (isinstance(fmax, bool) or not isinstance(fmax, (float, int))
                             or not math.isfinite(fmax) or fmax <= 0):
        raise ValueError("compiler fmax must be positive finite or null")
    if report.get("meets_50mhz") is not (fmax is not None and fmax >= 50):
        raise ValueError("compiler timing summary contradicts fmax")
    if not isinstance(budget_inputs, dict):
        raise ValueError("budget inputs must be an object")
    try:
        budget = plan(**budget_inputs)
    except TypeError as exc:
        raise ValueError("invalid or missing host budget arguments") from exc
    if budget["queue_bytes"] > 2:
        raise ValueError("baseline shell has only two queue entries per direction")
    requested_mhz = Fraction(str(budget_inputs["clock_hz"])) / 1000000
    estimated_clock_ok = None if fmax is None else requested_mhz <= Fraction(str(fmax))
    return {
        "schema": "warp_planning_certificate_v1",
        "scope": "audited local compile evidence plus analytical host model; not physical signoff or measured performance",
        "compile_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "architecture_sha256": arch_hash,
        "image_sha256": report["provenance"]["bitfile_sha256"],
        "design": report.get("design"), "architecture": report["arch"],
        "params": report.get("params"), "tools": report.get("tools"),
        "build_options": report.get("build_options"),
        "compile_provenance_scope": report["provenance"].get("scope"),
        "arch_version": report["arch_version"], "resources": resources,
        "pins": report.get("pins"),
        "unmapped_inputs_tied_0": report.get("unmapped_inputs_tied_0"),
        "unmapped_outputs_open": report.get("unmapped_outputs_open"),
        "compiler_estimate": {"fmax_mhz": fmax, "corner": report.get("timing_corner"),
            "requested_clock_within_estimate": estimated_clock_ok,
            "scope": "nextpnr model estimate; not extracted full-chip timing"},
        "host_budget_inputs": budget_inputs, "host_budget": budget,
        "physical_timing_verified": False, "board_rate_measured": False,
        "limits": ["Compile audit covers explicitly listed inputs, not recursive includes or tool binaries",
            "Resource assertions and model timing are compiler reports, not independent proofs",
            "Host model is single-direction; sharing bandwidth needs an explicit service guarantee",
            "Protocol logic timing, I/O, loading and full-chip physical signoff remain separate"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("architecture", type=Path)
    parser.add_argument("budget", type=Path, help="JSON arguments for board.budget.plan")
    args = parser.parse_args()
    try:
        result = certificate(args.report, args.architecture, json.loads(args.budget.read_text()))
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
