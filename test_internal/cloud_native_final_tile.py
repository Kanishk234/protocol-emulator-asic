"""Real-loaded final C2 functional diagnostic; no physical/timing acceptance.

The source hardening job failed deferred timing. Only its exact final netlist
is substituted; the unchanged D-023 interface loads actual configuration.
"""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from cloud_native_stage import (C2, PASSING_SHAS, sha, xml_status, relocate, native_paths)
from compact_gate_probe import constant_x_config_aliases_without_loads

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/native_final_tile_evidence"
INPUT = ROOT / "build/native_final_tile_input"
FINAL_SHA = "13cac0eabdbdcaf000b1e57c521fc9d417aac957be18a68c5808f8c920529e7c"


def semantic_evidence(text, reset):
    return {"actual_configuration_known_and_image_matched":
            "CONFIG CELL TOTAL: 9164 actual latches, 0 unknown, 0 image mismatches" in text,
            "real_loaded_uart_stress_and_stop":
            "28 UART TX/28 RX bytes and STOP parking pass" in text,
            "user_reset_observed": not reset or "after USER_RESET" in text}


def main():
    OUT.mkdir(exist_ok=False)
    result = {"scope": "actual hardened-final C2 loaded functionality only; source timing job FAILED; no physical/timing acceptance",
              "control_run": "37659171115", "source_hardening_run": "37814078650",
              "source_final_c2_sha256": FINAL_SHA, "physical_or_timing_qualified": False,
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
        final_tile = INPUT / "hardened/last_completed/nl" / (C2 + ".nl.v")
        if sha(final_tile) != FINAL_SHA:
            raise ValueError("actual final hardened C2 hash mismatch")
        source_result = INPUT / "hardened/result.json"
        result["source_hardening_outcome"] = json.loads(source_result.read_text())
        result["source_hardening_result_sha256"] = sha(source_result)
        shutil.copyfile(source_result, OUT / "source_hardening_result.json")
        shutil.copyfile(final_tile, OUT / "source_final_c2.nl.v")
        for name in ("LICENSE", "ATTRIBUTION.md", "manifest.json"):
            shutil.copyfile(INPUT / "hardened/source" / name, OUT / ("source_" + name))
        shutil.copyfile(control / "manifest.json", OUT / "passing_control_manifest.json")
        result["simulation_sources"] = {str(path.relative_to(ROOT)): sha(path) for path in (
            ROOT / "spikes/compact_edges/simulate.py", ROOT / "spikes/compact_edges/test_shell.py",
            ROOT / "test_internal/compact_gate_probe.py", Path(details["words"]))}
        env = dict(os.environ, WARP_COMPACT_UART_STRESS="edge_patterns", WARP_COMPACT_DIAG="1",
                   WARP_COMPACT_SHADOW_RTL="0")
        for stage, replacement in (("passing_original_control", None),
                                   ("hardened_final_c2", final_tile)):
            work = ROOT / "build" / ("native_final_tile_" + stage)
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
                text = (sim / "test.log").read_text() if (sim / "test.log").is_file() else ""
                record["semantic_evidence"] = semantic_evidence(text, bool(extra))
                record["passed"] = (record["exit_code"] == 0 and record["xml"]["passed"]
                    and not record.get("timed_out", False) and all(record["semantic_evidence"].values()))
                record["seconds"] = round(time.monotonic() - start, 2)
                for filename in ("results.xml", "test.log", "build.log", "native_lut_snapshot.json", "tb.v"):
                    if (sim / filename).is_file():
                        shutil.copyfile(sim / filename, destination / filename)
                save()
                print(f"END {stage}/{case}: passed={record['passed']}", flush=True)
        if sha(final_tile) != FINAL_SHA or any(sha(control / (tile + ".nl.v")) != expected
                                             for tile, expected in PASSING_SHAS.items()):
            raise ValueError("Authenticated source netlists changed during diagnostic")
        result["passed"] = len(result["stages"]) == 2 and all(len(stage["cases"]) == 2 for stage in result["stages"].values()) and all(case["passed"] for stage in result["stages"].values()
                               for case in stage["cases"].values())
        if not result["passed"]:
            raise RuntimeError("one or more diagnostic stages failed; retained all four case outcomes")
    except Exception as exc:
        result["error"] = str(exc)
        raise
    finally:
        save()


if __name__ == "__main__":
    main()
