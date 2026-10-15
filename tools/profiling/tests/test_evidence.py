"""Reject partial and nonconserving synthesis evidence without running EDA."""
import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "test_internal"))
import cloud_profile_evidence as evidence


def profile():
    return {design: {variant: {"luts": 3, "ffs": 2,
                    "lut_by_fn": {"counter": 1, "shared": 2}, "ff_by_fn": {"control": 2}}
                    for variant in evidence.VARIANTS} for design in evidence.DESIGNS}


def test_complete_approved_profile_conserves_attribution():
    summary = evidence.validate_profile(profile())
    assert summary["trials"] == 24
    assert summary["lut4_total"] == 12
    assert summary["lut4_by_function"] == {"counter": 4, "shared": 8}


@pytest.mark.parametrize("kind", ["workload", "variant", "lut_missing", "ff_duplicate", "unknown_role", "negative", "float", "bool"])
def test_partial_or_contradictory_profile_rejects(kind):
    data = profile()
    row = data["uart"]["LUT4"]
    if kind == "workload":
        data["unapproved"] = data.pop("uart")
    elif kind == "variant":
        data["uart"].pop("LUT3")
    elif kind == "lut_missing":
        row["lut_by_fn"].pop("counter")
    elif kind == "ff_duplicate":
        row["ff_by_fn"]["storage"] = 2
    elif kind == "unknown_role":
        row["lut_by_fn"]["unapproved"] = row["lut_by_fn"].pop("counter")
    elif kind == "negative":
        row["lut_by_fn"] = {"counter": -1, "shared": 4}
    elif kind == "float":
        row["luts"] = 3.0
    else:
        row["ffs"] = True
    with pytest.raises(ValueError):
        evidence.validate_profile(copy.deepcopy(data))
