"""Compare actual native routing before/after the measured combined reset placement."""
import json
import math
from pathlib import Path

import cloud_cfg_fanout as cfg
import cloud_hotspot_grt as paired
import cloud_fanout35_placement as combo
move = combo.trial
from cloud_fanout_local_grt import BUFFERED, CORNERS

ROOT = cfg.ROOT
INPUT = ROOT / "build/fanout35_grt_input"
OUT = ROOT / "build/fanout35_grt"
SOURCE_RUN = 38172225275
RESULT_SHA = "8824519638bb69333f432d9942fbc0f2bef50e3fb994664482b25cf42442d255"
CANDIDATE = dict(BUFFERED, odb="e0c18b2755930d9ff49c2e36fd7f8729d3e4c2e1989b15b14f9acd7111e0a536")


def validate_move(directory, baseline):
    if cfg.sha(directory / "result.json") != RESULT_SHA:
        raise ValueError("Actual combined producer identity differs")
    result = json.loads((directory / "result.json").read_text())
    if (result.get("passed") is not True or result.get("source_run") != 38101405271
            or result.get("scope") != "Combined reset placement plus one existing fanout35 relocation"
            or result.get("candidate_sha256") != {k: CANDIDATE[k] for k in ("odb", "nl")}):
        raise ValueError("Wrong measured endpoint move")
    if cfg.parse_census((directory / "before.tsv").read_text()) != cfg.parse_census((baseline / "after.tsv").read_text()):
        raise ValueError("Move did not start from exact baseline")
    measured = move.audit_move((directory / "before.tsv").read_text(),
        (directory / "after.tsv").read_text(), (directory / "geometry_before.tsv").read_text(),
        (directory / "geometry_after.tsv").read_text(), (directory / "selected.txt").read_text().splitlines())
    if json.loads(json.dumps(measured)) != result["placement"]:
        raise ValueError("Actual endpoint placement evidence differs")
    for label, views in (("baseline", BUFFERED), ("padded", CANDIDATE)):
        for corner in CORNERS:
            case = result[label + "_sta_" + corner]
            if (case["corner"] != corner or case["odb_sha256"] != views["odb"]
                    or case["nl_sha256"] != views["nl"] or case["sdc_sha256"] != views["sdc"]):
                raise ValueError("Measured electrical source differs")
            metrics = case["metrics"]
            for stem in ("max_fanout", "max_slew", "max_cap"):
                if metrics[f"design__{stem}_violation__count__corner:{corner}"] != 0:
                    raise ValueError("Electrical violation in measured producer")
            for stem in ("setup", "hold"):
                value = metrics[f"timing__{stem}__ws__corner:{corner}"]
                if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0 or metrics[f"timing__{stem}_vio__count__corner:{corner}"] != 0:
                    raise ValueError("Missing measured positive shell timing")
    return measured


def main():
    # Isolated copied-checkpoint experiment. The paired engine preserves both
    # actual native failures, original policies and independent marker reports.
    paired.INPUT, paired.OUT = INPUT, OUT
    paired.SOURCE_RUN, paired.RESULT_SHA, paired.PADDED = SOURCE_RUN, RESULT_SHA, CANDIDATE
    paired.validate_padding = validate_move
    try:
        paired.main()
    finally:
        path = OUT / "result.json"
        if path.is_file():
            result = json.loads(path.read_text())
            result["scope"] = "paired unchanged-policy GRT; combined reset placement plus fanout35 relocation"
            result["producer_result_sha256"] = result.pop("padding_result_sha256")
            result["source_runs"]["relocated"] = result["source_runs"].pop("padded")
            if "padded" in result["cases"]:
                result["cases"]["relocated"] = result["cases"].pop("padded")
            path.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
