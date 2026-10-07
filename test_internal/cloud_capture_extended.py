"""Compile and SPI-load a longer capture window on frozen G1, without hardening."""
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "build/cloud_capture_extended"
out.mkdir(parents=True, exist_ok=False)
queue_xml = ET.parse(ROOT / "protocols/uart_capture/test/results_extended.xml").getroot()
if len(queue_xml.findall(".//testcase")) != 1 or any(queue_xml.findall(".//" + tag)
                                                 for tag in ("failure", "error", "skipped")):
    raise RuntimeError("Missing or unsuccessful divide-by-eight source queue check")
env = dict(os.environ, PYTHONPATH=str(ROOT / "tools") + os.pathsep + str(ROOT / "test"))
build = out / "compiled"
command = [sys.executable, "-m", "compile.compile",
           str(ROOT / "protocols/uart_capture/uart_capture_top.v"),
           *map(str, sorted((ROOT / "protocols/uart").glob("*.v"))),
           "--pins", str(ROOT / "protocols/uart_capture/prescaled8.yaml"),
           "--arch", str(ROOT / "arch/warp_g1"), "--strict-ports", "-o", str(build)]
with (out / "compile.log").open("w") as log:
    subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
subprocess.run([sys.executable, "-m", "compile.audit", str(build / "report.json")],
               cwd=ROOT, env=env, check=True)
report = json.loads((build / "report.json").read_text())
if report["params"]["STAMP_BITS"] != 6 or report["params"]["STAMP_SHIFT"] != 3:
    raise RuntimeError("Wrong capture parameters compiled")
result = out / "loaded_results.xml"
case_env = dict(env, WARP_UART_CAPTURE_BITFILE=str(build / "prescaled8.wbit"),
                WARP_UART_CAPTURE_STAMP_SHIFT="3", PWD=str(ROOT / "test"))
with (out / "loaded.log").open("w") as log:
    subprocess.run(["make", "-C", str(ROOT / "test"), "WARP_FABRIC=rtl",
                    "COCOTB_TEST_MODULES=test_uart_capture", f"SIM_BUILD={out / 'sim'}",
                    f"COCOTB_RESULTS_FILE={result}"], cwd=ROOT / "test", env=case_env,
                   stdout=log, stderr=subprocess.STDOUT, check=True)
xml = ET.parse(result).getroot()
if len(xml.findall(".//testcase")) != 1 or any(xml.findall(".//" + tag)
                                           for tag in ("failure", "error", "skipped")):
    raise RuntimeError("Missing or unsuccessful SPI-loaded capture acceptance")
(out / "result.json").write_text(json.dumps({
    "scope": "frozen_G1_user_bitstream_RTL_loaded_function_only",
    "stamp_bits": 6, "stamp_shift": 3, "counter_period_clocks": 512,
    "decoder_maximum_known_gap_clocks": 504,
    "quantization_clocks": 8, "physical_or_gate_timing_acceptance": False,
    "utilisation": report["utilisation"], "compiler_fmax_mhz": report["fmax_mhz"],
}, indent=2) + "\n")
