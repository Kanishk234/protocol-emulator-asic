"""Run README quick-start commands on a fresh hosted checkout, retaining strict evidence.

Invoke only after scripts/setup_venv.sh and source .venv/bin/activate.
This does not harden hardware or establish post-layout timing.
"""
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "clean_reproduction"
README_COMMANDS = (
    "scripts/setup_venv.sh && source .venv/bin/activate",
    "bash scripts/fetch_nextpnr.sh",
    "scripts/check_all.sh",
    "scripts/build_test_bitstreams.sh --check",
    "cd tools && python -m compile.compile --pins ../protocols/uart/pins.yaml -o ../build/uart ../protocols/uart/*.v",
    "cd .. && make -C test WARP_FABRIC=rtl",
    "make -C test_internal/cosim",
)


def readme_provenance():
    readme = (ROOT / "README.md").read_text()
    lines = readme.splitlines()
    evidence = []
    for command in README_COMMANDS:
        matches = [number for number, line in enumerate(lines, 1) if line.startswith(command)]
        if len(matches) != 1:
            raise ValueError(f"README reproduction command missing or ambiguous: {command}")
        evidence.append({"command": command, "readme_line": matches[0]})
    return {"sha256": hashlib.sha256(readme.encode()).hexdigest(), "commands": evidence}


def tool_evidence():
    evidence = {"python": sys.version, "executable": sys.executable, "tools": {}, "packages": {}}
    if sys.version_info < (3, 12):
        raise ValueError("README requires Python >= 3.12")
    for name, args, expected in (("iverilog", ["-V"], "Icarus Verilog version 12.0"),
                                 ("verilator", ["--version"], "Verilator 5.020"),
                                 ("yosys", ["-V"], "e74db6dea"),
                                 ("sigrok-cli", ["--version"], None)):
        text = subprocess.check_output([name, *args], cwd=ROOT, text=True,
                                       stderr=subprocess.STDOUT, timeout=30)
        evidence["tools"][name] = {"path": shutil.which(name), "version_output": text}
        if expected and expected not in text:
            raise ValueError(f"unexpected pinned {name} version: {text}")
    for name, expected in (("FABulous-FPGA", "2.2.0"), ("fabulous-bit-gen", "0.3.1"),
                           ("fabulous-fasm", "0.2.0"), ("cocotb", "2.0.1"),
                           ("pytest", "8.4.2"), ("pyuvm", "5.0.0")):
        evidence["packages"][name] = metadata.version(name)
        if evidence["packages"][name] != expected:
            raise ValueError(f"unexpected pinned {name} version")
    evidence["pip_freeze"] = subprocess.check_output(
        [sys.executable, "-m", "pip", "freeze"], text=True, timeout=30).splitlines()
    return evidence


def xml_evidence(path, destination, required=(), allow_skips=False):
    """Reject missing, empty or unsuccessful suites, then preserve their actual XML."""
    root = ET.parse(path).getroot()
    cases = root.findall(".//testcase")
    if not cases or root.findall(".//failure") or root.findall(".//error"):
        raise ValueError(f"missing or unsuccessful test cases: {path}")
    if not allow_skips and root.findall(".//skipped"):
        raise ValueError(f"unexpected skipped tests: {path}")
    passed = {case.get("name") for case in cases if case.find("skipped") is None}
    missing = set(required) - passed
    if missing:
        raise ValueError(f"required tests did not pass in {path}: {sorted(missing)}")
    shutil.copy2(path, destination)
    return {"path": str(path.relative_to(ROOT)), "cases": len(cases),
            "skipped": len(root.findall(".//skipped")),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        raise RuntimeError("run in the project venv")
    if OUT.exists():
        raise RuntimeError("fresh reproduction requires an absent output directory")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise RuntimeError("fresh reproduction requires a clean checkout")
    # Tool downloads may be cached; compiled designs and simulation outputs may not.
    for path in (ROOT / "build", ROOT / "test" / "sim_build",
                 ROOT / "test_internal" / "sim_build",
                 ROOT / "test_internal" / "cosim" / "sim_build"):
        if path.exists():
            raise RuntimeError(f"unexpected prior build output: {path}")
    OUT.mkdir(parents=True)
    result = {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"],
              cwd=ROOT, text=True).strip(), "run_id": os.environ.get("GITHUB_RUN_ID"),
              "scope": "README source/compile/RTL reproduction; no physical signoff",
              "readme": readme_provenance(),
              "stages": [], "xml": [], "passed": False}

    def save():
        (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    def run(name, args, minutes, cwd=ROOT):
        stage = {"name": name, "command": args,
                 "cwd": str(cwd.relative_to(ROOT)) or ".", "limit_minutes": minutes}
        result["stages"].append(stage)
        save()
        start = time.monotonic()
        print(f"START {name}: {minutes} minute bound", flush=True)
        with (OUT / f"{name}.log").open("w") as log:
            proc = subprocess.Popen(args, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                                    start_new_session=True)
            try:
                code = proc.wait(timeout=minutes * 60)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                stage["timed_out"] = True
                stage["seconds"] = round(time.monotonic() - start, 2)
                save()
                raise RuntimeError(f"{name} exceeded its bounded runtime")
        stage.update(exit_code=code, seconds=round(time.monotonic() - start, 2))
        save()
        print(f"END {name}: exit {code}, {stage['seconds']} seconds", flush=True)
        if code:
            raise RuntimeError(f"{name} failed; see retained log")

    try:
        result["environment"] = tool_evidence()
        save()
        run("fetch_nextpnr", ["bash", "scripts/fetch_nextpnr.sh"], 10)
        run("check_all", ["scripts/check_all.sh"], 40)
        paths = [ROOT / "test" / "results.xml", ROOT / "test_internal" / "results.xml",
                 ROOT / "test_internal" / "uvm" / "results.xml"]
        paths += [mk.parent / "results.xml" for mk in sorted(ROOT.glob("protocols/*/test/Makefile"))]
        for index, path in enumerate(paths):
            # README's default UART configuration and idle fabric intentionally skip
            # runtime-divider and loaded-image tests; the loaded suite below cannot skip.
            result["xml"].append(xml_evidence(path, OUT / f"check_all_{index}.xml",
                allow_skips=path in (ROOT / "test/results.xml", ROOT / "protocols/uart/test/results.xml")))
        run("rebuild_bitstreams", ["scripts/build_test_bitstreams.sh", "--check"], 35)
        run("compile_uart", [sys.executable, "-m", "compile.compile", "--pins",
            "../protocols/uart/pins.yaml", "-o", "../build/uart",
            *["../" + str(path.relative_to(ROOT))
              for path in sorted(ROOT.glob("protocols/uart/*.v"))]], 5, ROOT / "tools")
        run("audit_uart", [sys.executable, "-m", "compile.audit", "../build/uart/report.json"],
            1, ROOT / "tools")
        run("loaded_fabric", ["make", "-C", "test", "WARP_FABRIC=rtl"], 75)
        required = ("test_two_bitstreams", "test_prims", "test_uart", "test_spi_ctrl",
                    "test_i2c_ctrl", "test_board_loader", "test_corrupt_load_over_running_design",
                    "test_uart_input_phase", "test_showcase_protocol_switching")
        result["xml"].append(xml_evidence(ROOT / "test/results.xml", OUT / "loaded_fabric.xml",
                                           required=required))
        run("cosim", ["make", "-C", "test_internal/cosim"], 10)
        result["xml"].append(xml_evidence(ROOT / "test_internal/cosim/results.xml",
            OUT / "cosim.xml", required=("test_uart_rtl_vs_fabric",)))
        if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"],
                                   cwd=ROOT).strip():
            raise RuntimeError("README commands changed tracked source files")
        result["passed"] = True
    except Exception as exc:
        result["error"] = str(exc)
        raise
    finally:
        save()


if __name__ == "__main__":
    main()
