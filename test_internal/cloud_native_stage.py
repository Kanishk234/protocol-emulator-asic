"""Isolate original C2 synthesis/final netlists against a passing native control.

Functional diagnostic with the unchanged D-023 routing harness. Copied physical
views do not qualify any substituted netlist; no configured timing acceptance.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/native_stage_evidence"
INPUT = ROOT / "build/native_stage_input"
C2 = "LUT4x8_ha_C2"
ARCHIVE_SHA = "addc14251bafe63eb19cda6dcb5e0dcf2afc81d9a7bdb8d67f6a92f9d4120d7f"
SYNTHESIS_SHA = "2c9faa6dc332004212c2719a8ca740b902d8c720f5f7da664007d3df7eedf6d9"
FINAL_SHA = "e0aef98643db5a98650e7bc6401de5db72731e89457aae3fd9962ae39b6c6f8c"
PASSING_SHAS = {
    "LUT4x8_ha": "4425946a3e9f56218b04e1af883573df59fe8654f4333941190d61e576ffc8fc",
    C2: "03c21b8e400e1774390e67b0939422959d37e26849adca18fa082f492cf5cdaf",
    "LUT4x8_ha_C3": "b0309fa92157ba537a669b04281f7c7a482d5461c151b66c57267f79cf47895f",
    "LUT4x8_ha_C4": "b76ddf0c19dae3494f7db35d678a85e81550d35ebf05e678b2c37a7afad2a8b9",
    "LUT4x8_ha_C5": "6553e1c9c307956a2780161ef8d67fadb8c1baaa91427876c9f16e6f088577c0",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xml_status(path):
    if not path.is_file():
        return {"passed": False, "error": "missing XML"}
    try:
        tree = ET.parse(path).getroot()
        cases = tree.findall(".//testcase")
        counts = {tag: len(tree.findall(".//" + tag)) for tag in ("failure", "error", "skipped")}
        return {"passed": len(cases) == 1 and cases[0].get("name") == "load_uart_through_shell"
                and not any(counts.values()), "cases": len(cases), **counts, "sha256": sha(path)}
    except (ET.ParseError, OSError) as exc:
        return {"passed": False, "error": str(exc)}


def unpack_stage_archive(archive, destination):
    if sha(archive) != ARCHIVE_SHA:
        raise ValueError("synthesis-stage archive hash mismatch")
    names = {C2 + ".synthesis.nl.v", "manifest.json", "LICENSE", "ATTRIBUTION.txt"}
    with tarfile.open(archive, "r:gz") as tf:
        members = tf.getmembers()
        if len(members) != len(names) or {member.name for member in members} != names:
            raise ValueError("unexpected or duplicate stage archive members")
        if any(not member.isfile() or member.size > 2_000_000 for member in members):
            raise ValueError("unsafe stage archive member")
        destination.mkdir(exist_ok=False)
        for member in members:
            (destination / member.name).write_bytes(tf.extractfile(member).read())
    manifest = json.loads((destination / "manifest.json").read_text())
    if manifest.get("tile") != C2 or manifest.get("synthesis_sha256") != SYNTHESIS_SHA:
        raise ValueError("synthesis-stage manifest mismatch")
    if sha(destination / (C2 + ".synthesis.nl.v")) != SYNTHESIS_SHA:
        raise ValueError("synthesis-stage netlist hash mismatch")


def relocate(work, original):
    # Relocate scratch path references before restoring exact authenticated NLs.
    for path in work.rglob("*"):
        if path.is_file() and path.suffix in (".v", ".json", ".tcl", ".ys", ".csv", ".yaml", ".lef", ".sdc"):
            text = path.read_text()
            if str(original) in text:
                path.write_text(text.replace(str(original), str(work)))


def native_paths(work):
    return {path.name: path for path in (work / "fabulous-tiles/tiles/tiny").glob(
        "*/macro/ihp-sg13cmos5l/nl/*.nl.v")}


def main():
    OUT.mkdir(exist_ok=False)
    result = {"scope": "C2 first-divergence functional diagnostic; no physical/timing acceptance",
              "control_run": "37659171115", "archive_sha256": ARCHIVE_SHA,
              "configuration_tied_to_constants": False, "original_inputs_edited": False,
              "harness": "unchanged D-023 data-routing X hold/pulse; no configuration/user-state force",
              "stages": {}, "passed": False}

    def save():
        (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    save()
    try:
        details = json.loads((ROOT / "build/cloud_input/materialized.json").read_text())
        original = Path(details["native_work"])
        control = INPUT / "passing_control"
        manifest = json.loads((control / "manifest.json").read_text())
        observed = {record["tile"]: record["variant_sha256"] for record in manifest["tiles"]}
        if (manifest.get("implementation") != "original_control" or observed != PASSING_SHAS
                or len(manifest["tiles"]) != len(PASSING_SHAS)
                or manifest.get("configuration_tied_to_constants") is not False):
            raise ValueError("passing-control manifest mismatch")
        if json.loads((control / "result.json").read_text()) != {
                "rtl_control": 0, "native_candidate": 0, "native_user_reset": 0}:
            raise ValueError("passing control did not record all three successful cases")
        for name in ("rtl_control", "native_candidate", "native_user_reset"):
            if not xml_status(control / (name + "_results.xml"))["passed"]:
                raise ValueError("passing-control XML missing/failed: " + name)
        for tile, expected in PASSING_SHAS.items():
            if sha(control / (tile + ".nl.v")) != expected:
                raise ValueError("passing tile hash mismatch: " + tile)
        original_final = native_paths(original)[C2 + ".nl.v"]
        if sha(original_final) != FINAL_SHA:
            raise ValueError("checkpoint final C2 hash mismatch")
        stage_input = INPUT / "unpacked_stage"
        unpack_stage_archive(INPUT / "native-stage-c2.tar.gz", stage_input)
        shutil.copyfile(control / "manifest.json", OUT / "passing_control_manifest.json")
        for name in ("manifest.json", "LICENSE", "ATTRIBUTION.txt"):
            shutil.copyfile(stage_input / name, OUT / ("synthesis_" + name))
        result["simulation_sources"] = {str(path.relative_to(ROOT)): sha(path) for path in (
            ROOT / "spikes/compact_edges/simulate.py", ROOT / "spikes/compact_edges/test_shell.py",
            ROOT / "test_internal/compact_gate_probe.py", Path(details["words"]))}
        env = dict(os.environ, WARP_COMPACT_UART_STRESS="edge_patterns", WARP_COMPACT_DIAG="1",
                   WARP_COMPACT_SHADOW_RTL="0")
        for stage, replacement in (("passing_original_control", None),
                                   ("original_synthesis_c2", stage_input / (C2 + ".synthesis.nl.v")),
                                   ("original_final_c2", original_final)):
            work = ROOT / "build" / ("native_stage_" + stage)
            shutil.copytree(original, work)
            relocate(work, original)
            # Never inherit XML/build/trace outputs from the checkpoint's workdir.
            for previous in work.glob("simulation*"):
                if previous.is_dir():
                    shutil.rmtree(previous)
            tiles = native_paths(work)
            for tile in PASSING_SHAS:
                shutil.copyfile(control / (tile + ".nl.v"), tiles[tile + ".nl.v"])
            baseline = {name: sha(path) for name, path in tiles.items()}
            if replacement:
                shutil.copyfile(replacement, tiles[C2 + ".nl.v"])
            final = {name: sha(path) for name, path in tiles.items()}
            changed = sorted(name for name in baseline if baseline[name] != final[name])
            if changed != ([] if replacement is None else [C2 + ".nl.v"]):
                raise ValueError("stage changes exceed the single C2 substitution")
            entry = {"tile_sha256": final, "changed_tiles": changed, "cases": {}}
            result["stages"][stage] = entry
            save()
            stage_out = OUT / stage
            stage_out.mkdir()
            cone = stage_out / "matched_native_cone.json"
            top = next((work / "macro/nl").glob("*.nl.v")).stem.removesuffix(".nl")
            macro_netlist = work / "macro/nl" / (top + ".nl.v")
            liberty = Path(os.environ["PDK_ROOT"]) / (
                "ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_slow_1p08V_125C.lib")
            with (stage_out / "matched_native_cone.log").open("w") as log:
                try:
                    parsed = subprocess.run(["yosys", "-Q", "-T", "-p",
                        f"read_liberty -lib {liberty}; read_verilog {' '.join(map(str, tiles.values()))} {macro_netlist}; "
                        f"hierarchy -check -top {top}; write_json {cone}"],
                        stdout=log, stderr=subprocess.STDOUT, timeout=120)
                    cone_failed = bool(parsed.returncode)
                except subprocess.TimeoutExpired:
                    cone_failed = True
            if cone_failed:
                entry["cone_error"] = "matched native parsing failed"
                entry["cases"] = {name: {"passed": False, "setup_error": entry["cone_error"]}
                                  for name in ("native_loaded", "native_user_reset")}
                save()
                continue
            from compact_gate_probe import constant_x_config_aliases_without_loads
            graph = json.loads(cone.read_text())
            graph["warp_native_input_provenance"] = {
                name.removesuffix(".nl.v"): {"path": str(path), "sha256": sha(path),
                    "unloaded_constant_x_config_aliases": sorted(
                        constant_x_config_aliases_without_loads(path.read_text()))}
                for name, path in tiles.items()}
            cone.write_text(json.dumps(graph) + "\n")
            entry["matched_cone_sha256"] = sha(cone)
            stage_env = dict(env, WARP_COMPACT_FABRIC_CONE_JSON=str(cone), WARP_COMPACT_FABRIC_TOP=top)
            for case, extra in (("native_loaded", []), ("native_user_reset", ["--reset-probe"])):
                destination = OUT / stage / case
                destination.mkdir(parents=True)
                args = [sys.executable, str(ROOT / "spikes/compact_edges/simulate.py"),
                        "--work", str(work), "--words", details["words"],
                        "--chip-dir", "chip_shared_crc_cfgbranches", "--mapped-fabric", *extra]
                start = time.monotonic()
                record = {"command": args, "timeout_seconds": 300}
                entry["cases"][case] = record
                save()
                print(f"START {stage}/{case}", flush=True)
                try:
                    with (destination / "runner.log").open("w") as log:
                        proc = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT,
                                                env=stage_env, start_new_session=True)
                        try:
                            record["exit_code"] = proc.wait(timeout=300)
                        except subprocess.TimeoutExpired:
                            os.killpg(proc.pid, signal.SIGKILL)
                            record["exit_code"] = proc.wait()
                            record["timed_out"] = True
                except OSError as exc:
                    record["launch_error"] = str(exc)
                    record["exit_code"] = None
                suffix = "_reset_probe" if extra else ""
                sim = work / ("simulation_chip_shared_crc_cfgbranches_mapped_fabric" + suffix)
                xml = sim / "results.xml"
                record["xml"] = xml_status(xml)
                record["passed"] = record["exit_code"] == 0 and record["xml"]["passed"]
                record["seconds"] = round(time.monotonic() - start, 2)
                for filename in ("results.xml", "test.log", "build.log", "native_lut_snapshot.json", "tb.v"):
                    if (sim / filename).is_file():
                        shutil.copyfile(sim / filename, destination / filename)
                save()
                print(f"END {stage}/{case}: passed={record['passed']}", flush=True)
        result["passed"] = all(case["passed"] for stage in result["stages"].values()
                               for case in stage["cases"].values())
        if not result["passed"]:
            raise RuntimeError("one or more diagnostic stages failed; retained all six case outcomes")
    except Exception as exc:
        result["error"] = str(exc)
        raise
    finally:
        save()


if __name__ == "__main__":
    main()
