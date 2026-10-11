"""Paired native GRT/hotspot replay of proven fixed-original ten buffers.

No new physical change: exact run38101405271 candidate against cluster8.
Inherited strict native failures remain in result.json; collection success is
separately identified by diagnostic.json and never physical/timing acceptance.
"""
import json
import math
from pathlib import Path

import cloud_congestion_map as mapping
import cloud_fanout_grt as paired
from cloud_cfg_fanout_local import verify_immobility

OUT = paired.ROOT / "build/fanout_local_grt"
INPUT = paired.ROOT / "build/fanout_local_grt_input"
SOURCE_RUN = 38101405271
RESULT_SHA = "48356d3f108dfba2be701220fb1ca7e6ded0aff2e11ea48b18deaa98a5457a72"
BUFFERED = dict(paired.BUFFERED,
    odb="0d2e6ea8666c9336e4447018be9325275f9366f58cb785cf6b70b616734b84e9")
CORNERS = ("nom_fast_1p32V_m40C", "nom_slow_1p08V_125C", "nom_typ_1p20V_25C")


def validate_candidate(directory):
    path = directory / "result.json"
    if paired.sha(path) != RESULT_SHA:
        raise ValueError("Fixed-original measured result authentication failed")
    result = json.loads(path.read_text())
    if result.get("passed") is not True or result.get("source_run") != 37811985079:
        raise ValueError("Candidate is not the exact successful cluster8 counterfactual")
    if result.get("buffered_sha256") != {key: BUFFERED[key] for key in ("odb", "nl")}:
        raise ValueError("Wrong successful fixed-original views")
    if result.get("derived_sha256") != paired.DERIVED or result.get("measurement_corners") != list(CORNERS):
        raise ValueError("Wrong original views or measured corners")
    evidence = verify_immobility((directory / "before.tsv").read_text(), (directory / "after.tsv").read_text())
    if evidence != result.get("connectivity"):
        raise ValueError("Measured connectivity/immobility evidence differs")
    for prefix, expected_fanout, odb in (("baseline", 5, paired.DERIVED["odb"]), ("buffered", 0, BUFFERED["odb"])):
        for corner in CORNERS:
            case = result.get(prefix + "_sta_" + corner, {})
            if case.get("corner") != corner or case.get("odb_sha256") != odb or case.get("sdc_sha256") != paired.DERIVED["sdc"]:
                raise ValueError("Corner measured different source views")
            metrics = case.get("metrics", {})
            for stem, expected in (("max_fanout", expected_fanout), ("max_slew", 0), ("max_cap", 0)):
                key = f"design__{stem}_violation__count__corner:{corner}"
                if metrics.get(key) != expected:
                    raise ValueError("Actual single-corner electrical evidence differs: " + key)
            for kind in ("setup", "hold"):
                key = f"timing__{kind}__ws__corner:{corner}"
                value = metrics.get(key)
                if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                    raise ValueError("Actual corner lacks positive shell timing: " + key)
    return evidence


def main():
    evidence = validate_candidate(INPUT / "ten_buffers")
    original_main = paired.main

    def measured_pair(iterations):
        if iterations != 50:
            raise ValueError("This replay preserves original50 native policy")
        try:
            return original_main(iterations)
        finally:
            path = OUT / "result.json"
            if path.exists():
                result = json.loads(path.read_text())
                result["source_runs"] = {"cluster8": 37811985079, "ten_buffers": SOURCE_RUN}
                result["candidate_source_result_sha256"] = RESULT_SHA
                result["candidate_immobility"] = evidence
                result["scope"] = "paired GRT-only unchanged-original ten-buffer replay"
                path.write_text(json.dumps(result, indent=2) + "\n")

    paired.INPUT = INPUT
    paired.BUFFERED = BUFFERED
    paired.verify_connections = verify_immobility
    paired.main = measured_pair
    mapping.OUT = OUT
    try:
        mapping.main()
    finally:
        paired.main = original_main


if __name__ == "__main__":
    main()
