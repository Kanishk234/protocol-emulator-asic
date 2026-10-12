"""Read-only worst min/max path through each actual delay cell; no repair removal."""
import json
from pathlib import Path
import tarfile
from decimal import Decimal
import cloud_cfg_fanout as cfg
import cloud_hotspot_padding as guards
from audit_hold_repair import audit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "build/reset_combined"
OUT = ROOT / "build/hold_allocation"
PATCH = ROOT / "patches/sta_hold_allocation.tcl"
EXPECTED = {"config.json": "75758f19231f582e22a5fd73b55564ee114e2e493c99f859fbfd204fc25cdb1c",
    "padded.odb": "6b64454b7fe1148063162dcb22be6b77580ee1790623f73f6af828f0d6469e4e",
    "padded.nl.v": "3e3e9fd0a7632c1669858c99ff968aebcd671550488736f4c51c8d2222722136",
    "after.tsv": "3d8a7d032a84720fa1b4e5a243cccadde5678630f0067d846f25352ba4905aa3",
    "geometry_after.tsv": "c2317b8ffbb2c2f008b85bb8a0ee910075b4db37a3df84a4776cfa9fb688652f"}


def parse_queries(text, names):
    rows = text.splitlines()
    if not rows or rows[0] != "CELL\tMODE\tSTATE\tSLACK_NS\tSTART\tEND":
        raise ValueError("Missing native query header")
    records = {}
    for line in rows[1:]:
        fields = line.split("\t")
        if len(fields) != 6: raise ValueError("Malformed native path record")
        cell, mode, state, slack, start, end = fields
        key = cell, mode
        if cell not in names or mode not in ("min", "max") or key in records:
            raise ValueError("Unknown/duplicate path query")
        if state == "CONSTRAINED":
            value = Decimal(slack)
            if not value.is_finite() or start == "NA" or end == "NA":
                raise ValueError("Missing/nonfinite constrained path")
        elif state == "NO_CONSTRAINED_PATH":
            if (slack, start, end) != ("NA", "NA", "NA"):
                raise ValueError("Unexpected unconstrained path values")
        else: raise ValueError("Unknown native query state")
        records[key] = {"state": state, "slack_ns": slack, "start": start, "end": end}
    if set(records) != {(name, mode) for name in names for mode in ("min", "max")}:
        raise ValueError("Incomplete delay query census")
    return {mode: {name: records[name, mode] for name in sorted(names)} for mode in ("min", "max")}


def main():
    OUT.mkdir(exist_ok=False)
    result = {"observation_complete": False, "physical_acceptance": False,
              "delay_removal_justified": False, "source_run": 38167697696, "corners": {}}
    def save(): (OUT / "result.json").write_text(json.dumps(result, indent=2)+"\n")
    save()
    try:
        for name, digest in EXPECTED.items():
            if cfg.sha(SOURCE / name) != digest: raise ValueError("Producer view differs: " + name)
        archive = ROOT / "build/fanout-preflight-source.tar.gz"
        if cfg.sha(archive) != cfg.SOURCE_SHA: raise ValueError("Source archive differs")
        unpack = SOURCE / "original_source"
        unpack.mkdir(exist_ok=False)
        with tarfile.open(archive) as tf: tf.extractall(unpack, filter="data")
        bundle = unpack / "fanout_source"
        manifest = json.loads((bundle / "manifest.json").read_text())
        if manifest["source_odb_sdc_nl"] != cfg.EXPECTED: raise ValueError("Original manifest differs")
        for name, digest in manifest["files"].items():
            path = (bundle / name).resolve()
            if not path.is_relative_to(bundle.resolve()) or cfg.sha(path) != digest:
                raise ValueError("Original payload differs")
        config = json.loads((SOURCE / "config.json").read_text())
        if config.get("STA_EXTRA_CORNER_TCL_FILE") is not None:
            raise ValueError("Existing STA hook cannot be replaced")
        config["STA_EXTRA_CORNER_TCL_FILE"] = str(PATCH)
        allocation = audit(SOURCE / "after.tsv", SOURCE / "geometry_after.tsv")
        instances, _ = cfg.parse_census((SOURCE / "after.tsv").read_text())
        names = {name for name, row in instances.items() if row[0] == allocation["delay_master"]}
        if len(names) != 590: raise ValueError("Wrong delay census")
        result["allocation"] = allocation
        result["observer_patch_sha256"] = cfg.sha(PATCH)
        guards.OUT = OUT
        sdc = SOURCE / "padded_sta_nom_typ_1p20V_25C/final/sdc/tt_um_warp.sdc"
        if cfg.sha(sdc) != "2fd4e213532d83ee258899b6fc1ed48c4e5d91ddb0ccbe21eea0226cc90fd56e":
            raise ValueError("SDC differs")
        for corner in config["STA_CORNERS"]:
            label = "observed_" + corner
            guard = guards.sta(config, label, SOURCE / "padded.odb", SOURCE / "padded.nl.v", sdc, corner)
            stage, = (OUT / label).glob("*-openroad-stamidpnr")
            resolved = json.loads((stage / "config.json").read_text())
            if resolved.get("STA_EXTRA_CORNER_TCL_FILE") != str(PATCH):
                raise ValueError("Native STA hook missing or replaced")
            records = parse_queries((stage / "delay-paths.tsv").read_text(), names)
            result["corners"][corner] = {"unchanged_electrical_timing_guards": guard,
                "query_sha256": cfg.sha(stage / "delay-paths.tsv"), "queries": records}
            save()
        for name, digest in EXPECTED.items():
            if cfg.sha(SOURCE / name) != digest: raise ValueError("Source modified during observation")
        result["observation_complete"] = True
    except Exception as exc:
        result["error"] = str(exc)
        raise
    finally: save()


if __name__ == "__main__": main()
