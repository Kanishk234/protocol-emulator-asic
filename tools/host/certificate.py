"""Combine audited compiler evidence and an analytical host service budget.

The artifact is a planning certificate, not timing signoff or measured rate
certification. Compiler timing, resource fit and host service are separate.
"""
import argparse
import csv
from fractions import Fraction
import hashlib
import io
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


def _metadata(report):
    """Validate metadata exposed to users; do not infer missing fields."""
    for pin, roles in report["pins"].items():
        if (not isinstance(pin, str) or not pin or not isinstance(roles, dict)
                or not roles or any(role not in ("i", "o", "oe")
                or not isinstance(port, str) or not port for role, port in roles.items())):
            raise ValueError("malformed compiler pin mapping")
    params = report.get("params")
    if not isinstance(params, dict) or any(not isinstance(key, str) or not key
            or not isinstance(value, (str, int, float, bool))
            or isinstance(value, float) and not math.isfinite(value)
            for key, value in params.items()):
        raise ValueError("malformed compiler parameters")
    versions = report.get("tools")
    if not isinstance(versions, dict) or any(not isinstance(key, str) or not key
            or not isinstance(value, str) or not value for key, value in versions.items()):
        raise ValueError("malformed compiler tool versions")
    if not isinstance(report.get("build_options"), dict):
        raise ValueError("missing compiler build options")
    for key in ("unmapped_inputs_tied_0", "unmapped_outputs_open"):
        ports = report.get(key)
        if not isinstance(ports, list) or any(not isinstance(port, str) or not port for port in ports):
            raise ValueError("malformed compiler " + key)


def _pinout(architecture_path, inputs, mapped_pins):
    """Crosscheck user-facing pins against the hashed architecture pin table."""
    pin_path = architecture_path.with_name("pins.csv")
    pin_bytes = pin_path.read_bytes()
    pin_hash = hashlib.sha256(pin_bytes).hexdigest()
    if not any(Path(entry["path"]).resolve() == pin_path.resolve()
               and entry["sha256"] == pin_hash for entry in inputs):
        raise ValueError("architecture pins.csv is not a hashed compiler input")
    reader = csv.DictReader(io.StringIO(pin_bytes.decode("utf-8")))
    if not reader.fieldnames or not {"pin", "bel", "direction", "chip_pin"}.issubset(reader.fieldnames):
        raise ValueError("architecture pin table has missing columns")
    directions = {"clock": {"i"}, "in": {"i"}, "out": {"o"},
                  "out_en": {"oe"}, "inout": {"i", "o", "oe"}}
    table = {}
    for row in reader:
        if (any(not isinstance(row.get(key), str) or not row[key]
                for key in ("pin", "bel", "direction", "chip_pin"))
                or row["pin"] in table or row["direction"] not in directions):
            raise ValueError("architecture pin table has malformed or duplicate pins")
        table[row["pin"]] = row
    pinout = {}
    for pin, roles in mapped_pins.items():
        if pin not in table:
            raise ValueError("compiler maps an unknown architecture pin: " + pin)
        row = table[pin]
        if not set(roles).issubset(directions[row["direction"]]):
            raise ValueError("compiler pin role contradicts architecture direction: " + pin)
        pinout[pin] = {"ports": roles, "direction": row["direction"],
                       "bel": row["bel"], "chip_pin": row["chip_pin"]}
    return pinout, pin_hash


def certificate(report_path, architecture_path, budget_inputs):
    """Generate a self-consistency artifact using current compiler schema.

    Paths in compiler provenance use its existing working-directory convention.
    Hash agreement is not independent authentication of compiler assertions.
    """
    report_path, architecture_path = Path(report_path), Path(architecture_path)
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes)
    architecture_bytes = architecture_path.read_bytes()
    try:
        architecture = yaml.safe_load(architecture_bytes)
    except yaml.YAMLError as exc:
        raise ValueError("malformed architecture YAML") from exc
    if not isinstance(architecture, dict) or not isinstance(report, dict):
        raise ValueError("report and architecture must be objects")
    if not isinstance(report.get("design"), str) or not report["design"]:
        raise ValueError("missing compiler design identity")
    if not isinstance(report.get("pins"), dict):
        raise ValueError("missing compiler pin mapping")
    _metadata(report)
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
    pinout, pin_hash = _pinout(architecture_path, inputs, report["pins"])
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
        "architecture_pins_sha256": pin_hash,
        "image_sha256": report["provenance"]["bitfile_sha256"],
        "design": report.get("design"), "architecture": report["arch"],
        "params": report.get("params"), "tools": report.get("tools"),
        "build_options": report.get("build_options"),
        "compile_provenance_scope": report["provenance"].get("scope"),
        "arch_version": report["arch_version"], "resources": resources,
        "pins": report.get("pins"),
        "pinout": pinout,
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


def operating_summary(result):
    """Readable presentation of an already generated planning artifact."""
    estimate = result["compiler_estimate"]
    within = estimate["requested_clock_within_estimate"]
    clock_status = "unknown" if within is None else "within estimate" if within else "exceeds estimate"
    frequency = "unknown" if estimate["fmax_mhz"] is None else f"{estimate['fmax_mhz']} MHz"
    budget = result["host_budget"]
    lines = [f"Design: {result['design']} ({result['architecture']} {result['arch_version']})",
        "Physical timing: unverified. Board rate: unmeasured.",
        f"Compiler clock estimate: {frequency}; requested clock {clock_status}.",
        f"Host model ({budget['direction']}): service margin {budget['strict_service_margin']}; "
        f"queue sufficient {budget['queue_sufficient_under_model']} "
        f"({budget['required_queue_bytes']} required, {budget['queue_bytes']} available).",
        "Parameters: " + json.dumps(result["params"], sort_keys=True),
        "Resources: " + ", ".join(f"{name} {value['used']}/{value['available']}"
            for name, value in sorted(result["resources"].items())), "Pin mapping:"]
    for pin, roles in sorted(result["pins"].items()):
        for role, port in sorted(roles.items()):
            pinout = result.get("pinout", {}).get(pin)
            label = "" if pinout is None else f" [{pinout['chip_pin']}]"
            lines.append(f"  {pin}.{role}: {port}{label}")
    lines.extend(["Inputs tied zero: " + json.dumps(result["unmapped_inputs_tied_0"]),
        "Outputs open: " + json.dumps(result["unmapped_outputs_open"]),
        "Tool versions: " + json.dumps(result["tools"], sort_keys=True),
        "Report SHA256: " + result["compile_report_sha256"],
        "Scope: " + result["scope"]])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("architecture", type=Path)
    parser.add_argument("budget", type=Path, help="JSON arguments for board.budget.plan")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args()
    try:
        result = certificate(args.report, args.architecture, json.loads(args.budget.read_text()))
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))
    if args.format == "text":
        print(operating_summary(result), end="")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
