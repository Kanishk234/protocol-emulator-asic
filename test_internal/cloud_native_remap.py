"""One-tile combinational remapping diagnostic, with state-cut binary proof.

Original configuration/user storage and official simulation models remain.
Matching hardened views, sequential boot, four-state equivalence and timing
are outside this diagnostic's acceptance scope.
"""
import copy
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time

from cloud_native_stage import (C2, PASSING_SHAS, SYNTHESIS_SHA, sha, xml_status,
                                unpack_stage_archive, relocate, native_paths)
from compact_gate_probe import constant_x_config_aliases_without_loads

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/native_remap_evidence"
INPUT = ROOT / "build/native_remap_input"
STATE_TYPES = {"sg13cmos5l_dlhq_1", "sg13cmos5l_dfrbpq_1"}


def state_inventory(module):
    return {name: cell for name, cell in module["cells"].items() if cell["type"] in STATE_TYPES}


def verify_storage(original, candidate):
    """Require exact instance/type/ports, resolving connectivity by retained names."""
    old, new = state_inventory(original), state_inventory(candidate)
    if set(old) != set(new):
        raise ValueError("state instances changed")
    counts = {kind: sum(cell["type"] == kind for cell in old.values()) for kind in STATE_TYPES}
    if counts != {"sg13cmos5l_dlhq_1": 529, "sg13cmos5l_dfrbpq_1": 8}:
        raise ValueError("unexpected original storage inventory")
    aliases = {}
    for name, net in original["netnames"].items():
        for index, bit in enumerate(net["bits"]):
            if isinstance(bit, int):
                aliases.setdefault(bit, []).append((name, index))
    for name, cell in old.items():
        peer = new[name]
        if (cell["type"] != peer["type"] or cell["port_directions"] != peer["port_directions"]
                or cell.get("parameters", {}) != peer.get("parameters", {})):
            raise ValueError("state type or ports changed")
        for port, bits in cell["connections"].items():
            other = peer["connections"][port]
            if len(bits) != len(other):
                raise ValueError("state pin width changed")
            for bit, changed in zip(bits, other):
                if isinstance(bit, str):
                    if bit != changed:
                        raise ValueError("state pin constant changed")
                elif not any(alias in candidate["netnames"]
                    and len(candidate["netnames"][alias]["bits"]) > index
                    and candidate["netnames"][alias]["bits"][index] == changed
                    for alias, index in aliases.get(bit, ())):
                    raise ValueError("state pin lost original signal binding: " + name + "." + port)
    for name, port in original["ports"].items():
        peer = candidate["ports"].get(name)
        if not peer or any(port.get(key, 0) != peer.get(key, 0)
                           for key in ("direction", "offset", "upto")) or len(port["bits"]) != len(peer["bits"]):
            raise ValueError("tile/frame interface changed: " + name)
    return counts


def state_cut(module, name):
    """Expose every storage Q as an arbitrary shared input and D/control as outputs."""
    cut = copy.deepcopy(module)
    for index, (instance, cell) in enumerate(sorted(state_inventory(cut).items())):
        for port, bits in cell["connections"].items():
            if cell["port_directions"][port] == "output":
                if any(not isinstance(bit, int) for bit in bits):
                    raise ValueError("storage output is not a live net")
                direction = "input"
            else:
                direction = "output"
            cut["ports"][f"wp_state_{index}_{port}"] = {"direction": direction, "bits": bits}
        del cut["cells"][instance]
    cut["attributes"].pop("top", None)
    return {"modules": {name: cut}, "creator": "WARP original/candidate binary combinational state-cut diagnostic"}


def main():
    OUT.mkdir(exist_ok=False)
    result = {"scope": "one original-synthesis C2 combinational remap; binary state-cut proof only",
              "configuration_forced": False, "stock_models_changed": False,
              "physical_or_timing_qualified": False, "stages": {}, "passed": False}
    def save():
        (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    def yosys(name, script, seconds=180):
        path = OUT / (name + ".ys")
        path.write_text(script + "\n")
        with (OUT / (name + ".log")).open("w") as log:
            subprocess.run(["yosys", "-Q", "-T", "-s", str(path)], stdout=log,
                           stderr=subprocess.STDOUT, timeout=seconds, check=True)
    save()
    try:
        details = json.loads((ROOT / "build/cloud_input/materialized.json").read_text())
        original = Path(details["native_work"])
        result["words_sha256"] = sha(Path(details["words"]))
        result["harness_sources"] = {str(path.relative_to(ROOT)): sha(path) for path in (
            ROOT / "spikes/compact_edges/simulate.py", ROOT / "spikes/compact_edges/test_shell.py",
            ROOT / "test_internal/compact_gate_probe.py")}
        control = INPUT / "passing_control"
        observed = json.loads((control / "manifest.json").read_text())
        if observed["implementation"] != "original_control" or {
                item["tile"]: item["variant_sha256"] for item in observed["tiles"]} != PASSING_SHAS:
            raise ValueError("passing control manifest mismatch")
        for tile, expected in PASSING_SHAS.items():
            if sha(control / (tile + ".nl.v")) != expected:
                raise ValueError("passing control hash mismatch")
        for name in ("rtl_control", "native_candidate", "native_user_reset"):
            if not xml_status(control / (name + "_results.xml"))["passed"]:
                raise ValueError("passing input did not pass all original acceptance cases")
        unpack_stage_archive(INPUT / "native-stage-c2.tar.gz", INPUT / "unpacked")
        for name in ("LICENSE", "ATTRIBUTION.txt", "manifest.json"):
            shutil.copyfile(INPUT / "unpacked" / name, OUT / ("source_" + name))
        source = INPUT / "unpacked" / (C2 + ".synthesis.nl.v")
        result["original_c2_sha256"] = sha(source)
        if result["original_c2_sha256"] != SYNTHESIS_SHA:
            raise ValueError("synthesis input mismatch")
        liberty = Path(os.environ["PDK_ROOT"]) / "ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_slow_1p08V_125C.lib"
        result["liberty_sha256"] = sha(liberty)
        before_json = OUT / "original_c2.json"
        candidate_json = OUT / "candidate_c2.json"
        candidate = OUT / (C2 + ".remapped.nl.v")
        yosys("original_connectivity", f"read_liberty -lib {liberty}; read_verilog {source}; hierarchy -check -top {C2}; write_json {before_json}")
        old = json.loads(before_json.read_text())["modules"][C2]
        # Read actual Liberty functions, blackbox only storage, and flatten only
        # combinational logic. No sequential synthesis/reset/config transformation.
        yosys("remap", "\n".join([
            f"read_liberty -ignore_miss_func {liberty}",
            "blackbox sg13cmos5l_dlhq_1 sg13cmos5l_dfrbpq_1",
            f"read_verilog {source}", f"hierarchy -check -top {C2}",
            f"setattr -set keep 1 {C2}/t:sg13cmos5l_dlhq_1 {C2}/t:sg13cmos5l_dfrbpq_1",
            "flatten -wb", "techmap", "opt", f"abc -liberty {liberty}", "clean",
            "check -assert", f"write_verilog -noattr -noexpr {candidate}", f"write_json {candidate_json}",
        ]))
        new = json.loads(candidate_json.read_text())["modules"][C2]
        result["storage_inventory"] = verify_storage(old, new)
        result["candidate_c2_sha256"] = sha(candidate)
        if result["candidate_c2_sha256"] == result["original_c2_sha256"]:
            raise ValueError("remap did not produce a distinct candidate")
        for name, module in (("gold_cut", old), ("gate_cut", new)):
            (OUT / (name + ".json")).write_text(json.dumps(state_cut(module, name)) + "\n")
        # Compare all external outputs plus next-state/control pins for arbitrary
        # binary inputs/configuration/user-state Q. This is not a sequential proof.
        yosys("binary_state_cut_proof", "\n".join([
            f"read_liberty -ignore_miss_func {liberty}", f"read_json {OUT / 'gold_cut.json'}",
            "hierarchy -top gold_cut", "flatten -wb", "techmap", "opt", "design -stash gold",
            f"read_liberty -ignore_miss_func {liberty}", f"read_json {OUT / 'gate_cut.json'}",
            "hierarchy -top gate_cut", "flatten -wb", "techmap", "opt", "design -stash gate",
            "design -copy-from gold -as gold_cut gold_cut", "design -copy-from gate -as gate_cut gate_cut",
            "miter -equiv -flatten gold_cut gate_cut equiv", "hierarchy -top equiv", "opt_clean",
            "sat -verify -prove trigger 0 -timeout 180 equiv",
        ]), seconds=240)
        result["binary_state_cut_equivalence_passed"] = True
        save()
        for stage, replacement in (("passing_control", None), ("original_synthesis_negative", source),
                                    ("combinational_remap", candidate)):
            work = ROOT / "build" / ("native_remap_" + stage)
            shutil.copytree(original, work)
            relocate(work, original)
            for previous in work.glob("simulation*"):
                if previous.is_dir(): shutil.rmtree(previous)
            tiles = native_paths(work)
            for tile in PASSING_SHAS:
                shutil.copyfile(control / (tile + ".nl.v"), tiles[tile + ".nl.v"])
            baseline = {name: sha(path) for name, path in tiles.items()}
            if replacement: shutil.copyfile(replacement, tiles[C2 + ".nl.v"])
            hashes = {name: sha(path) for name, path in tiles.items()}
            changed = sorted(name for name in hashes if hashes[name] != baseline[name])
            if changed != ([] if replacement is None else [C2 + ".nl.v"]):
                raise ValueError("more than C2 changed")
            dest = OUT / stage
            dest.mkdir()
            cone = dest / "matched_native_cone.json"
            macro = next((work / "macro/nl").glob("*.nl.v"))
            top = macro.name.removesuffix(".nl.v")
            yosys(stage + "_connectivity", f"read_liberty -lib {liberty}; read_verilog {' '.join(map(str, tiles.values()))} {macro}; hierarchy -check -top {top}; write_json {cone}")
            graph = json.loads(cone.read_text())
            graph["warp_native_input_provenance"] = {name.removesuffix(".nl.v"):
                {"path": str(path), "sha256": sha(path), "unloaded_constant_x_config_aliases":
                 sorted(constant_x_config_aliases_without_loads(path.read_text()))} for name, path in tiles.items()}
            cone.write_text(json.dumps(graph) + "\n")
            entry = {"tile_sha256": hashes, "changed_tiles": changed, "cases": {}}
            result["stages"][stage] = entry
            env = dict(os.environ, WARP_COMPACT_UART_STRESS="edge_patterns", WARP_COMPACT_DIAG="1",
                       WARP_COMPACT_SHADOW_RTL="0", WARP_COMPACT_FABRIC_CONE_JSON=str(cone), WARP_COMPACT_FABRIC_TOP=top)
            for case, extra in (("native_loaded", []), ("native_user_reset", ["--reset-probe"])):
                case_dest = dest / case
                case_dest.mkdir()
                args = [sys.executable, str(ROOT / "spikes/compact_edges/simulate.py"), "--work", str(work),
                        "--words", details["words"], "--chip-dir", "chip_shared_crc_cfgbranches", "--mapped-fabric", *extra]
                start = time.monotonic()
                record = {"command": args}
                entry["cases"][case] = record
                save()
                print(f"START {stage}/{case}", flush=True)
                try:
                    with (case_dest / "runner.log").open("w") as log:
                        proc = subprocess.Popen(args, env=env, stdout=log, stderr=subprocess.STDOUT,
                                                start_new_session=True)
                        try:
                            record["exit_code"] = proc.wait(timeout=300)
                        except subprocess.TimeoutExpired:
                            os.killpg(proc.pid, signal.SIGKILL)
                            proc.wait()
                            raise
                except subprocess.TimeoutExpired:
                    record.update(exit_code=None, timed_out=True)
                suffix = "_reset_probe" if extra else ""
                sim = work / ("simulation_chip_shared_crc_cfgbranches_mapped_fabric" + suffix)
                record["xml"] = xml_status(sim / "results.xml")
                record["passed"] = record["exit_code"] == 0 and record["xml"]["passed"]
                record["seconds"] = round(time.monotonic() - start, 2)
                for filename in ("results.xml", "test.log", "build.log", "native_lut_snapshot.json", "tb.v"):
                    if (sim / filename).is_file(): shutil.copyfile(sim / filename, case_dest / filename)
                text = (sim / "test.log").read_text() if (sim / "test.log").is_file() else ""
                record["known_negative_uart_x"] = (not record["passed"] and record["exit_code"] not in (None, 0)
                    and record["xml"].get("cases") == 1 and record["xml"].get("failure") == 1
                    and record["xml"].get("error") == 0 and record["xml"].get("skipped") == 0
                    and "CONFIG CELL TOTAL: 9164 actual latches, 0 unknown, 0 image mismatches" in text
                    and "first UART X at clock edge" in text and "invalid literal for int() with base 10: 'X'" in text)
                save()
        result["passed"] = all(case["passed"] for stage in ("passing_control", "combinational_remap")
            for case in result["stages"][stage]["cases"].values()) and all(
            case["known_negative_uart_x"] for case in result["stages"]["original_synthesis_negative"]["cases"].values())
        if not result["passed"]: raise RuntimeError("remap experiment did not meet all explicit gates")
    except Exception as exc:
        result["error"] = str(exc)
        raise
    finally: save()


if __name__ == "__main__": main()
