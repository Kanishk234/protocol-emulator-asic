#!/usr/bin/env python3
"""Reproduce scratch CRC checks without changing frozen chip sources."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from cocotb_tools.runner import get_runner
from prepare import ROOT, DEFAULT_WORK
from prepare_chip import prepare_chip


def check_xml(path):
    results = ET.parse(path).getroot()
    if (len(results.findall(".//testcase")) != 1 or
            any(results.findall(".//" + tag) for tag in ("failure", "error", "skipped"))):
        raise RuntimeError(f"Expected one passing test: {path}")


def unit(out):
    runner = get_runner("icarus")
    runner.build(sources=[ROOT / "src/wp_crc32.v",
                          ROOT / "spikes/compact_edges/wp_crc32_shared_word.v",
                          ROOT / "test_internal/tb_shared_crc.v"],
                 hdl_toplevel="tb_shared_crc", build_dir=out / "build",
                 build_args=["-g2005"], log_file=out / "build.log")
    runner.test(test_module="test_shared_crc", hdl_toplevel="tb_shared_crc",
                test_dir=ROOT / "test_internal", results_xml=str(out / "results.xml"),
                log_file=out / "test.log")
    check_xml(out / "results.xml")


def formal_config(shell, out):
    text = (ROOT / "formal/f2_loader.sby").read_text()
    text = text.replace("../src/wp_shell.v", "wp_shell.v " + str(shell))
    text = text.replace("../src/wp_crc32.v", "wp_crc32.v " +
                        str(ROOT / "spikes/compact_edges/wp_crc32_shared_word.v"))
    text = text.replace("../src/", str(ROOT / "src") + "/")
    path = out / "f2_shared_crc.sby"
    path.write_text(text)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--out", type=Path, required=True,
                        help="Fresh ignored output directory; existing results are not overwritten")
    parser.add_argument("--unit-only", action="store_true")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    unit(out)
    if not args.unit_only:
        chip_dir = "chip_shared_crc_verify"
        prepare_chip(args.work, 15.12, True, 3.78, chip_dir, True, True)
        env = dict(os.environ)
        env["PATH"] = env.get("PATH", "") + os.pathsep + str(Path.home() / "oss-cad-suite/bin")
        path = formal_config(args.work.resolve() / chip_dir / "wp_shell.v", out)
        with (out / "formal.log").open("w") as log:
            subprocess.run(["sby", "-f", str(path)], cwd=ROOT, env=env,
                           check=True, stdout=log, stderr=subprocess.STDOUT)
        # Import after the unit run so simulation and source selection match
        # the standard compact-shell test driver.
        from simulate import simulate
        simulate(args.work, ROOT / "build/arch_explore/compiled_structural/uart_words.hex",
                 chip_dir=chip_dir)
    (out / "summary.json").write_text(json.dumps({
        "unit": "PASS", "formal_f2": "not run" if args.unit_only else "PASS, BMC 84 / cover 60",
        "spi_uart_stop": "not run" if args.unit_only else "PASS",
        "physical": "not checked by this script",
    }, indent=2) + "\n")
