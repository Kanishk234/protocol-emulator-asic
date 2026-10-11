"""Preserve authenticated experimental inputs before CI artifacts expire.

No EDA, source changes, raw logs, PDK libraries or promotion. The manifest
retains the original failed timing/congestion outcomes alongside passing tests.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
from cloud_native_stage import PASSING_SHAS

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "build/compact-proven-sources-20261009.tar.gz"
FINAL_NL = "13cac0eabdbdcaf000b1e57c521fc9d417aac957be18a68c5808f8c920529e7c"
FINAL_ODB = "ed22fd1da8caa0fc3386c85183110c3bcecca641192c80171f91f96a183720c9"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(path):
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        names = [m.name for m in members]
        if len(names) != len(set(names)) or any(not m.isfile() or
                Path(m.name).is_absolute() or ".." in Path(m.name).parts for m in members):
            raise ValueError("Unsafe, duplicate or non-file archive entry")
        manifest = json.load(archive.extractfile("manifest.json"))
        if set(names) != set(manifest["files"]) | {"manifest.json"}:
            raise ValueError("Archive inventory differs from manifest")
        for name, digest in manifest["files"].items():
            if sha(archive.extractfile(name).read()) != digest:
                raise ValueError("Source checksum mismatch: " + name)
        anchors = manifest["files"]
        if anchors.get("c2/nl/LUT4x8_ha_C2.nl.v") != FINAL_NL or anchors.get(
                "c2/odb/LUT4x8_ha_C2.odb") != FINAL_ODB:
            raise ValueError("Wrong actual hardened C2 anchors")
        if manifest.get("qualified_successor") is not False:
            raise ValueError("Experimental qualification scope changed")
        return manifest


def prepare():
    physical = ROOT / "build/cloud_tile_harden_37814078650/matched-c2-harden-37814078650/last_completed"
    loaded = json.loads((ROOT / "build/cloud_native_final_tile_37958116481/result.json").read_text())
    audit = json.loads((ROOT / "build/cloud_tile_audit_37958116371/result.json").read_text())
    if loaded.get("passed") is not True or loaded["source_final_c2_sha256"] != FINAL_NL:
        raise ValueError("Actual final-C2 loaded evidence missing")
    if audit.get("final_odb_sha256") != FINAL_ODB or audit.get("physical_gate_metrics_zero") is not True:
        raise ValueError("Actual retained physical evidence missing")
    if audit.get("original_strict_flow_failure_retained") is not True:
        raise ValueError("Original timing rejection must remain explicit")
    files = {"LICENSE": (ROOT / "LICENSE").read_bytes()}
    for path in physical.rglob("*"):
        if path.is_file() and path.relative_to(physical).parts[0] in {
                "nl", "pnl", "odb", "lef", "gds", "spef", "sdc", "sdf", "lib"}:
            files["c2/" + path.relative_to(physical).as_posix()] = path.read_bytes()
    files["c2/metrics.json"] = (physical / "metrics.json").read_bytes()
    control = ROOT / "build/cloud_uart_stress_control_37659171115"
    for name, expected in ((tile + ".nl.v", digest) for tile, digest in PASSING_SHAS.items()):
        if loaded["stages"]["passing_original_control"]["tile_sha256"][name] != expected:
            raise ValueError("Loaded control differs from passing source pin")
        data = (control / name).read_bytes()
        if sha(data) != expected:
            raise ValueError("Passing native control changed: " + name)
        files["passing_control/" + name] = data
    fanout = ROOT / "build/cloud_cfg_fanout_37956470190/compact-cfg-fanout-37956470190"
    result = json.loads((fanout / "result.json").read_text())
    if result.get("passed") is not True:
        raise ValueError("Estimated fanout source is not authenticated passing evidence")
    for kind, name in {"odb": "buffered.odb", "nl": "buffered.nl.v"}.items():
        data = (fanout / name).read_bytes()
        if sha(data) != result["buffered_sha256"][kind]:
            raise ValueError("Buffered source changed")
        files["fanout/" + name] = data
    for name in ("before.tsv", "after.tsv", "result.json"):
        files["fanout/" + name] = (fanout / name).read_bytes()
    files["fanout/tt_um_warp.sdc"] = (fanout / "buffered_sta_nom_typ_1p20V_25C/final/sdc/tt_um_warp.sdc").read_bytes()
    if sha(files["fanout/tt_um_warp.sdc"]) != result["derived_sha256"]["sdc"]:
        raise ValueError("Original fanout SDC changed")
    for name, data in (("native_loaded", loaded), ("physical_audit", audit)):
        files["evidence/" + name + ".json"] = (json.dumps(data, indent=2) + "\n").encode()
    files["ATTRIBUTION.md"] = (
        "# Experimental source attribution\n\n"
        "WARP generated native/physical views and metadata: project contributors, Apache-2.0 (LICENSE).\n"
        "FABulous tile sources: mole99/fabulous-tiles, attribution and pins in project docs/VERSIONS.md.\n"
        "Derived IHP geometry uses IHP-Open-PDK2bbec755dc67ca3db0261c3d6163e15735d66710; "
        "upstream notices/licenses: https://github.com/IHP-GmbH/IHP-Open-PDK/tree/2bbec755dc67ca3db0261c3d6163e15735d66710.\n"
        "Only generated tile Liberty/SDF models are included; no original PDK library files, secrets or raw logs. "
        "These sources are NOT qualified submission views.\n"
    ).encode()
    manifest = {"qualified_successor": False,
        "base_source": {**json.loads((ROOT / "spikes/cloud/checkpoint.json").read_text()),
                        "note": "Unchanged control tiles are in that existing archive"},
        "all_control_tile_sha256": loaded["stages"]["passing_original_control"]["tile_sha256"],
        "source_runs": {
        "control": 37659171115, "physical": 37814078650, "interface_audit": 37958116371,
        "loaded_final": 37958116481, "estimated_fanout": 37956470190},
        "remaining": ["tile fanout62", "configured timing", "other tiles physical qualification",
                      "shell congestion148/169 in37958932549", "complete fabric integration"],
        "files": {name: sha(data) for name, data in sorted(files.items())}}
    files["manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    import io
    with tarfile.open(OUTPUT, "w:gz") as archive:
        for name, data in sorted(files.items()):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))
    verify(OUTPUT)
    print(json.dumps({"archive": str(OUTPUT), "sha256": sha(OUTPUT.read_bytes()),
                      "files": len(files), "bytes": OUTPUT.stat().st_size}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "verify"))
    parser.add_argument("--archive", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        verify(args.archive)
        print("Exact archive inventory and source anchors PASS")
