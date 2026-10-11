"""Bounded cloud compiler seed audit of frozen G1 and design-set inputs only.

Nine fresh builds: UART/SPI controller/I2C controller, seeds0..2. Retain all
failures; no best-seed selection, timing acceptance or new protocol tuning.
Run in the project venv. --self-test executes no synthesis or P&R.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import unittest
from unittest.mock import MagicMock, Mock, patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from compile.compile import cell_estimate, tool, tool_versions

FROZEN = "3047dea08566bedaed9d061c0ce2313c92f4a193"
DESIGNS = ("uart", "spi_ctrl", "i2c_ctrl")
SEEDS = (0, 1, 2)
EXPECTED_PARAMS = {"uart": {"DIV": 434, "RUNTIME_DIV": 0, "PRIMS": 1},
                   "spi_ctrl": {"CPOL": 0, "CPHA": 0, "HALF": 25, "PRIMS": 1},
                   "i2c_ctrl": {"Q": 125, "PRIMS": 1}}
OUT = ROOT / "build/seed_robustness"


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def validate_report(report, design, seed, versions):
    if report["arch"] != "warp_g1" or report["arch_version"] != "0x0003":
        raise ValueError("Unexpected architecture identity")
    if report["params"] != EXPECTED_PARAMS[design] or report["build_options"]["seed"] != seed:
        raise ValueError("Changed parameters or seed")
    if report["tools"] != versions or report["timing_corner"] != "nom_slow_1p08V_125C":
        raise ValueError("Changed tool versions or model corner")
    if report["build_options"]["strict_ports"] is not False:
        raise ValueError("Changed intentional existing pin handling")
    if report["words"] <= 0 or not report["provenance"]["inputs"]:
        raise ValueError("Incomplete successful compile evidence")


def bounded_compile(command, output):
    # A timed-out Python compiler can leave Yosys/nextpnr children. Bound the
    # whole dedicated process group, never other CI processes or workloads.
    with (output / "compile.log").open("w") as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True,
                                   env=dict(os.environ, PYTHONPATH=str(ROOT / "tools")))
        try:
            return process.wait(timeout=90), False
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            # The parent may exit before a child that ignored SIGTERM. Always
            # finish cleanup of this dedicated group, even after parent exit.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            return process.returncode, True


def validate_matrix(rows):
    planned = {(design, seed) for design in DESIGNS for seed in SEEDS}
    actual = [(row["design"], row["seed"]) for row in rows]
    if len(actual) != len(planned) or set(actual) != planned:
        raise ValueError("Incomplete, duplicated or unplanned seed matrix")
    return all(row["fits"] for row in rows)


def run():
    OUT.mkdir(parents=True, exist_ok=False)
    summary = {"passed": False, "asic_timing_acceptance": False,
               "loaded_functional_acceptance": False, "designs": DESIGNS,
               "seeds": SEEDS, "trials": [], "trial_timeout_seconds": 90}
    def save():
        (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    save()
    try:
        if git("rev-parse", "hw-freeze") != FROZEN:
            raise ValueError("Unexpected frozen architecture tag")
        frozen_paths = ("arch/warp_g1", "macro/warp_g1", "arch/prims")
        if git("diff", "--name-only", FROZEN, "--", *frozen_paths):
            raise ValueError("Frozen G1 hardware/views differ")
        tracked = git("ls-files", "--", *frozen_paths, "tools/compile", "scripts/fetch_nextpnr.sh",
                      "scripts/fetch_tiles.sh", "requirements-dev.txt").splitlines()
        source_files = {}
        for design in DESIGNS:
            directory = ROOT / "protocols" / design
            pins = directory / "pins.yaml"
            spec = yaml.safe_load(pins.read_text())
            if spec.get("params") != EXPECTED_PARAMS[design]:
                raise ValueError("Design-set parameters changed: " + design)
            sources = sorted(directory.glob("*.v"))
            if not sources:
                raise ValueError("Missing design-set sources")
            source_files[design] = sources
            tracked += [str(p.relative_to(ROOT)) for p in [pins, *sources]]
        tracked += [str(Path(__file__).resolve().relative_to(ROOT))]
        snapshots = {name: sha(ROOT / name) for name in sorted(set(tracked))}
        versions = tool_versions()
        if not versions["yosys"].startswith("Yosys 0.66+179") or "nextpnr-0.11.1-34-gc4fbb55a" not in versions["nextpnr-generic"]:
            raise ValueError("Unpinned compiler tools")
        tiles = Path(os.environ["WARP_TILES"])
        tile_head = subprocess.check_output(["git", "-C", str(tiles), "rev-parse", "HEAD"], text=True).strip()
        if not tile_head.startswith("7999e5a") or subprocess.check_output(["git", "-C", str(tiles), "status", "--porcelain"], text=True).strip():
            raise ValueError("Tile library changed")
        tile_files = subprocess.check_output(["git", "-C", str(tiles), "ls-files"], text=True).splitlines()
        summary.update({"commit": git("rev-parse", "HEAD"), "frozen_commit": FROZEN,
                        "input_sha256": snapshots, "tools": versions,
                        "tool_binary_sha256": {name: sha(tool(name)) for name in ("yosys", "nextpnr-generic")},
                        "tile_library_commit": tile_head,
                        "tile_library_sha256": {name: sha(tiles / name) for name in tile_files if (tiles / name).is_file()},
                        "parameters": EXPECTED_PARAMS})
        save()
        for design in DESIGNS:
            for seed in SEEDS:
                output = OUT / design / f"seed_{seed}"
                output.mkdir(parents=True, exist_ok=False)
                command = [sys.executable, "-m", "compile.compile", *map(str, source_files[design]),
                           "--pins", str(ROOT / "protocols" / design / "pins.yaml"),
                           "--arch", str(ROOT / "arch/warp_g1"), "--seed", str(seed), "-o", str(output)]
                started = time.monotonic()
                code, timed_out = bounded_compile(command, output)
                row = {"design": design, "seed": seed, "command": command, "returncode": code,
                       "timed_out": timed_out, "elapsed_seconds": time.monotonic() - started,
                       "fits": False, "status": "timeout" if timed_out else "compile_failure"}
                report_path = output / "report.json"
                if code == 0 and not timed_out:
                    report = json.loads(report_path.read_text())
                    validate_report(report, design, seed, versions)
                    image = Path(report["provenance"]["bitfile"])
                    if not image.is_relative_to(output) or sha(image) != report["provenance"]["bitfile_sha256"]:
                        raise ValueError("Wrong successful image or digest")
                    row.update({"fits": True, "status": "compiled", "report": report})
                elif report_path.exists() or list(output.glob("*.wbit")):
                    raise ValueError("Failed build retained success report/image")
                failure_path = output / "failure.json"
                if failure_path.exists():
                    row["failure"] = json.loads(failure_path.read_text())
                    failure = row["failure"]
                    if failure["seed"] != seed or failure["arch"] != "warp_g1" or failure["tools"] != versions:
                        raise ValueError("Failure diagnostic has different seed/architecture/tools")
                    row["status"] = "place_route_failure"
                if (output / "design.json").exists():
                    row["synthesized_resources"] = cell_estimate(output / "design.json", "warp_top")
                summary["trials"].append(row)
                if {name: sha(ROOT / name) for name in snapshots} != snapshots:
                    raise ValueError("Inputs changed across seeds")
                save()
        summary["inputs_unchanged"] = True
        summary["passed"] = validate_matrix(summary["trials"])
        summary["compiled_trials"] = sum(row["fits"] for row in summary["trials"])
        save()
        if not summary["passed"]:
            raise RuntimeError("Some planned seeds failed; retain every trial")
    except Exception as exc:
        summary["error"] = str(exc)
        raise
    finally:
        save()


class ReportChecks(unittest.TestCase):
    def test_complete_matrix_and_failure_retention(self):
        rows = [{"design": design, "seed": seed, "fits": True}
                for design in DESIGNS for seed in SEEDS]
        self.assertTrue(validate_matrix(rows))
        for bad in [rows[:-1], rows + [rows[0]], rows[:-1] + [rows[0]]]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_matrix(bad)
        rows[0]["fits"] = False
        self.assertFalse(validate_matrix(rows))
        self.assertEqual(len(rows), 9)

    def test_timeout_targets_only_dedicated_child_group(self):
        child = Mock(pid=123456, returncode=-9)
        child.wait.side_effect = [subprocess.TimeoutExpired("compile", 90),
                                  subprocess.TimeoutExpired("compile", 5), -9]
        output = MagicMock()
        with patch("subprocess.Popen", return_value=child) as spawn, patch("os.killpg") as kill:
            code, timeout = bounded_compile(["mock-compiler"], output)
        self.assertEqual((code, timeout), (-9, True))
        self.assertTrue(spawn.call_args.kwargs["start_new_session"])
        self.assertEqual(kill.call_args_list[0].args, (123456, signal.SIGTERM))
        self.assertEqual(kill.call_args_list[1].args, (123456, signal.SIGKILL))
        child.wait.side_effect = [subprocess.TimeoutExpired("compile", 90), -15, -15]
        with patch("subprocess.Popen", return_value=child), patch("os.killpg") as kill:
            bounded_compile(["mock-compiler"], output)
        self.assertEqual(kill.call_args_list[1].args, (123456, signal.SIGKILL))

    def test_report_contract(self):
        versions = {"yosys": "test", "nextpnr-generic": "test"}
        report = {"arch": "warp_g1", "arch_version": "0x0003", "params": EXPECTED_PARAMS["uart"],
                  "build_options": {"seed": 1, "strict_ports": False}, "tools": versions,
                  "timing_corner": "nom_slow_1p08V_125C", "words": 1, "provenance": {"inputs": [1]}}
        validate_report(report, "uart", 1, versions)
        for key, value in [("arch", "compact"), ("params", {"PRIMS": 0}), ("tools", {}),
                           ("timing_corner", "fast"), ("words", 0)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_report(dict(report, **{key: value}), "uart", 1, versions)
        with self.assertRaises(ValueError):
            validate_report(report, "uart", 2, versions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReportChecks)
        raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
    run()
