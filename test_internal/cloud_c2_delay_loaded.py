"""Authenticate the actual eight-delay routed C2 and load it through the shell.

No physical re-run, configuration forcing, timing or full-chip promotion.
Other tile types remain the original passing regenerated controls.
"""
import json
import os
from pathlib import Path
import re

import cloud_native_final_tile as native
from cloud_tile_harden import PHYSICAL_GATES
from cloud_native_stage import sha

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "build/c2_delay_loaded_input"
OUT = ROOT / "build/c2_delay_loaded"
PHYSICAL_RUN = 38114298036
FILES = {
    "result.json": "61e0a7ebc13fca49b0b1eb0c91ad7288031628edd3c43a428104023b0de42512",
    "input_change.json": "c078464eb1f1b1cc6eef8dc7e063b03b53a74fded56df7b0bf0ac6b6a20163f4",
    "last_completed/metrics.json": "0e89d954fb8f51d8ca95df7b34c864e7b9cf5fb0ebff141f74a3261918a81cfa",
    "final_pin_inventory.json": "e4fe52ec667bf54d95bc4db23d874505ca8a1e789eca4b6a65c9891590bb3efc",
    "reference_pin_inventory.json": "c05b64c5e31b274c5c6ac926c0646b5e980c515c4fb5af1b015edb2c76658ea4",
    "last_completed/nl/LUT4x8_ha_C2.nl.v": "a986a0864ab51f09f6157422ba7dff935585b6456e6accc7b64ac8228725e882",
}


def audit_physical(path):
    for name, expected in FILES.items():
        if sha(path / name) != expected:
            raise ValueError("Actual delay physical evidence differs: " + name)
    result = json.loads((path / "result.json").read_text())
    change = json.loads((path / "input_change.json").read_text())
    metrics = json.loads((path / "last_completed/metrics.json").read_text())
    final = json.loads((path / "final_pin_inventory.json").read_text())
    reference = json.loads((path / "reference_pin_inventory.json").read_text())
    if final != reference or len(final["pins"]) - len(final["power_types"]) != 306 or not final["power_types"]:
        raise ValueError("Native signal/power interfaces do not match")
    gates = {name: metrics.get(name) for name in PHYSICAL_GATES}
    if any(value != 0 for value in gates.values()):
        raise ValueError("Native physical gate missing or nonzero")
    expected = {"wp_diag_hold_delay_" + str(i) for i in range(8)}
    text = (path / "last_completed/nl/LUT4x8_ha_C2.nl.v").read_text()
    observed = re.findall(r"\bsg13cmos5l_dlygate4sd1_1\s+(\w+)\s*\(", text)
    if len(observed) != 8 or set(observed) != expected or set(result["retained_delay_instances"]) != expected:
        raise ValueError("Eight actual retained delay cells required")
    if (change["identity_contraction_exact"] is not True or len(change["added_cells"]) != 8
            or result["underlying_flow_passed"] is not False or result["physical_acceptance"] is not False
            or "Setup violations" not in result["underlying_flow_error"]):
        raise ValueError("Original candidate/failure provenance differs")
    return {"source_run": PHYSICAL_RUN, "authenticated_files": FILES,
            "native_physical_gates": gates, "native_interfaces_exact": True,
            "retained_delay_instances": sorted(expected), "physical_or_timing_qualified": False,
            "source_virtual_clock_setup_failure_retained": True,
            "report_serialization_failure_retained": result["physical_retention_error"]}


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise ValueError("Loaded simulation runs only on the GitHub runner")
    audit = audit_physical(INPUT / "hardened")
    # Existing harness validates original control, uses real SPI configuration,
    # checks all actual latches and executes normal/USER_RESET UART cases.
    try:
        native.main(final_sha=FILES["last_completed/nl/LUT4x8_ha_C2.nl.v"],
                    source_hardening_run=PHYSICAL_RUN, input_dir=INPUT, out_dir=OUT,
                    control_run=int(os.environ["GITHUB_RUN_ID"]))
    finally:
        if OUT.is_dir():
            (OUT / "physical_input_audit.json").write_text(json.dumps(audit, indent=2) + "\n")


if __name__ == "__main__":
    main()
