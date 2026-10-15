#!/usr/bin/env python3
"""Fault-injection (mutation) campaign, phase 4 (VERIFICATION.md): plant one realistic bug at a
time in a throwaway copy of the repository and run the checks that should catch it. A mutant is
"killed" only when its expected executed check rejects the planted behavior. Survivors are findings: either a gap in the checks or an
equivalent mutant (explained in the report).

Usage: scripts/mutation.py [names...]      Output: build/mutation/results.json and REPORT.md
Needs: the project venv, the OSS CAD Suite, a fetched tile library (WARP_TILES), SymbiYosys.
"""
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "build" / "mutation"

# Checks deliberately include excluded cocotb cases. Only these explicit names
# may skip; every expected case must actually execute in both control/mutant.
CHIP_CASES = {
    "test_reset_state", "test_read_id", "test_load_run_stop", "test_wrong_arch_version",
    "test_bad_crc", "test_length_mismatch", "test_bad_sync_word", "test_empty_load_rejected",
    "test_bad_commands_change_nothing", "test_aborted_transaction_keeps_whole_words",
    "test_reload_from_loaded", "test_host_channel_overflow", "test_user_inputs_do_not_affect_parking",
}
LOADED_CASES = {
    "test_counter4", "test_two_bitstreams", "test_logic4", "test_host_channel", "test_prims",
    "test_uart", "test_spi_ctrl", "test_i2c_ctrl", "test_board_loader", "test_board_examples_spi",
    "test_board_examples_i2c", "test_ws2812", "test_onewire", "test_swd",
    "test_corrupt_load_over_running_design", "test_uart_input_phase", "test_showcase_protocol_switching",
}


def expectation(command):
    if "sby" in command:
        return {"formal": "formal/f1_isolation", "required": set(), "skips": set()}
    if "test_internal/uvm" in command:
        return {"xml": "test_internal/uvm/results.xml", "required": {"ShellRandomTest"}, "skips": set()}
    if "test_internal" in command:
        return {"xml": "test_internal/results.xml", "required": {"test_timer_matches_model", "test_shift_matches_model"}, "skips": set()}
    if "COCOTB_TEST_FILTER=" in command:
        selected = command.split("COCOTB_TEST_FILTER=", 1)[1].split()[0]
        return {"xml": "test/results.xml", "required": {selected}, "skips": (CHIP_CASES | LOADED_CASES) - {selected}}
    return {"xml": "test/results.xml", "required": CHIP_CASES, "skips": LOADED_CASES}


def classify(repo, command, code, output, timed_out=False):
    """Return pass/rejected/error; only an explicit behavioral rejection kills."""
    if timed_out or code < 0:
        return "error", "timeout or terminated process"
    if re.search(r'ModuleNotFoundError|ImportError|FileNotFoundError|SyntaxError|command not found|Unable to import module', output):
        return "error", "tool or harness setup exception in command output"
    spec = expectation(command)
    if "formal" in spec:
        status = repo / spec["formal"] / "status"
        if not status.is_file():
            return "error", "missing formal status"
        observed = re.fullmatch(r'(PASS|FAIL)(?:\s+\d+\s+\d+)?', status.read_text().strip())
        value = observed[1] if observed else None
        if value == "PASS" and code == 0 and "DONE (PASS" in output:
            return "pass", "explicit formal PASS"
        engines = sorted((repo / spec["formal"]).glob('engine_*/logfile*.txt'))
        text = '\n'.join(path.read_text() for path in engines if path.is_file())
        if value == "FAIL" and code != 0 and "DONE (FAIL" in output and "Assert failed" in text:
            return "rejected", "formal property assertion failed"
        return "error", "formal failure lacks explicit property rejection"
    try:
        root = ET.parse(repo / spec["xml"]).getroot()
        cases = list(root.iter("testcase"))
        names = [case.get("name") for case in cases]
        if root.tag not in ("testsuite", "testsuites") or not cases or len(names) != len(set(names)):
            raise ValueError("missing, duplicate or malformed testcase census")
        if set(names) != spec["required"] | spec["skips"]:
            raise ValueError("unexpected testcase census")
        if list(root.iter("error")):
            raise ValueError("harness/error testcase")
        failed = set()
        for case in cases:
            name = case.get("name")
            if sum(case.find(tag) is not None for tag in ("skipped", "failure", "error")) > 1:
                raise ValueError("contradictory testcase outcomes")
            if case.find("skipped") is not None:
                if name not in spec["skips"]:
                    raise ValueError("required test skipped")
            elif case.find("failure") is not None:
                if name not in spec["required"]:
                    raise ValueError("unexpected non-target failure")
                failed.add(name)
        for suite in root.iter():
            if suite.tag in ("testsuite", "testsuites"):
                for field in ("failures", "errors", "skipped"):
                    if field in suite.attrib and (not suite.attrib[field].isdigit()):
                        raise ValueError("malformed suite counter")
                    tags = {"failures": "failure", "errors": "error", "skipped": "skipped"}
                    if field in suite.attrib and int(suite.attrib[field]) != len(list(suite.iter(tags[field]))):
                        raise ValueError("contradictory suite counter")
                if int(suite.get("errors", "0")):
                    raise ValueError("nonzero suite error count")
        if failed and code != 0 and "AssertionError" in output:
            return "rejected", "executed expected test assertion failed: " + ",".join(sorted(failed))
        if failed or code != 0:
            raise ValueError("command failure is not an identified test assertion")
        return "pass", "expected tests executed and passed"
    except (OSError, ValueError, ET.ParseError) as exc:
        return "error", str(exc)


def run_check(repo, command, env, log, timeout=600):
    """Bound the shell and all simulator/formal descendants as one process group."""
    started = time.monotonic()
    with log.open("w") as stream:
        child = subprocess.Popen(["bash", "-c", command], cwd=repo, env=env,
                                 stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        timed_out = False
        try:
            code = child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
            code = child.returncode
    verdict, detail = classify(repo, command, code, log.read_text(), timed_out)
    return {"verdict": verdict, "detail": detail, "returncode": code,
            "timed_out": timed_out, "seconds": round(time.monotonic()-started, 2)}

# name: (description, [(file, old, new)], command, what should catch it)
MUTANTS = {
    "timer_reload_off_by_one": (
        "timer reloads RELOAD - 1 at terminal count (period one clock short)",
        [("arch/prims/wp_timer.v", "                count <= reload;\n                armed <= !oneshot;",
          "                count <= reload - 16'd1;\n                armed <= !oneshot;")],
        "make -C test_internal", "white-box primitive tests vs the Python model"),
    "shift_wrong_end": (
        "shift register outputs the wrong end (MSB/LSB swapped)",
        [("arch/prims/wp_shift.v", "assign sout = msb_first ? sr[7] : sr[0];",
          "assign sout = msb_first ? sr[0] : sr[7];")],
        "make -C test_internal", "white-box primitive tests vs the Python model"),
    "fifo_drops_items": (
        "host channel FIFO silently drops every second push",
        [("src/wp_fifo.v", "wire do_push = push && !full;", "wire do_push = push && !full && !wp[0];")],
        "make -C test", "chip suite (black-box fabric): host channel tests"),
    "crc_check_disabled": (
        "loader accepts a bad CRC",
        [("src/wp_shell.v", "end else if (word != crc || crc_busy) begin", "end else if (1'b0) begin")],
        "make -C test", "chip suite: test_bad_crc"),
    "arch_check_disabled": (
        "loader accepts any architecture version",
        [("src/wp_shell.v", "if (pay[23:8] == ARCH_VERSION) begin", "if (1'b1) begin")],
        "make -C test", "chip suite: test_wrong_arch_version"),
    "inverted_output_enable": (
        "bidirectional pins' output enable inverted",
        [("src/tt_um_warp.v", "assign uio_oe  = io_oe_q  & {8{running}};",
          "assign uio_oe  = ~io_oe_q & {8{running}};")],
        "COCOTB_TEST_FILTER=test_counter4 make -C test WARP_FABRIC=rtl",
        "chip suite with a real bitstream (counter4 checks FAB_IO0's enable)"),
    "parking_gate_removed": (
        "fabric outputs reach the pins while not RUNNING",
        [("src/tt_um_warp.v", "assign uo_out  = {out_q & {6{running}}, host_irq, host_miso};",
          "assign uo_out  = {out_q, host_irq, host_miso};")],
        "cd formal && sby -f f1_isolation.sby", "F1 formal proof (output isolation)"),
    "config_bit_position": (
        "wrong configuration-bit position: a LUT's INIT shifted by one bit in logic4's bitstream",
        "BITSTREAM",
        "COCOTB_TEST_FILTER=test_logic4 make -C test WARP_FABRIC=rtl",
        "chip suite with the real bitstream (logic4 truth table)"),
    "bad_cmd_overwrites_error": (
        "a bad command overwrites a pending load error code (D-021: only when ERROR_CODE is 0)",
        [("src/wp_shell.v", "                        if (err == E_NONE)\n                            err <= E_BAD_COMMAND;",
          "                        if (1'b1)\n                            err <= E_BAD_COMMAND;")],
        "make -C test_internal/uvm RANDOM_SEED=1", "pyuvm shell environment vs the shell reference model"),
    "overflow_never_clears": (
        "ch_overflow is not cleared by READ_STATUS",
        [("src/wp_shell.v", "                                err <= E_NONE;\n                                ovf <= 1'b0;",
          "                                err <= E_NONE;")],
        "make -C test_internal/uvm RANDOM_SEED=1", "pyuvm shell environment vs the shell reference model"),
    "tx_ready_when_stopped": (
        "STATUS.tx_ready reported while not RUNNING (a CH_WRITE would be refused)",
        [("src/wp_shell.v", "{state, !rx_empty, running && !tx_full,", "{state, !rx_empty, !tx_full,")],
        "make -C test_internal/uvm RANDOM_SEED=1", "pyuvm shell environment vs the shell reference model"),
}


def copy_repo(dst):
    if dst.exists():
        shutil.rmtree(dst)
    ignore = shutil.ignore_patterns("build", ".venv", "sim_build", "__pycache__", "results.xml",
                                    "*.vcd", "*.fst", "runs", ".git", "f1_isolation", "f2_loader*",
                                    "f3_fifo*", "f4_prims*")
    shutil.copytree(ROOT, dst, ignore=ignore, symlinks=True)


def drop_config_bit(repo):
    """Wrong configuration-bit position: shift the first LUT INIT of logic4 by one bit, then
    rebuild its .wbit with WARP's bitgen."""
    sys.path.insert(0, str(ROOT / "tools"))
    from compile.bitgen import gen_words
    from compile.bitfile import BitFile
    fasm = (repo / "test/bitstreams/logic4.fasm").read_text().splitlines()
    idx = next(i for i, l in enumerate(fasm) if ".INIT[15:0] = 16'b" in l)
    head, bits = fasm[idx].split("16'b")
    fasm[idx] = head + "16'b" + bits[1:] + bits[0]
    dropped = f"{head.strip()} {bits} -> {bits[1:] + bits[0]}"
    (repo / "test/bitstreams/logic4.fasm").write_text("\n".join(fasm) + "\n")
    arch = (ROOT / "arch/CURRENT").read_text().strip()
    spec = ROOT / "macro" / arch / "fabulous" / "bitStreamSpec.bin"
    words = gen_words(repo / "test/bitstreams/logic4.fasm", spec)
    old = BitFile.load(repo / "test/bitstreams/logic4.wbit")
    BitFile(old.arch_version, words).save(repo / "test/bitstreams/logic4.wbit")
    return dropped


def main(argv):
    names = list(dict.fromkeys(argv or MUTANTS))
    if any(name not in MUTANTS for name in names):
        raise ValueError("Unknown mutant requested")
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        raise RuntimeError("Run mutation campaign in the project venv")
    # Never merge a subset with stale results from another source/campaign.
    WORK.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    # Do not inherit user filters or build-mode overrides into controls.
    for key in ("COCOTB_TESTCASE", "COCOTB_TEST_FILTER", "TESTCASE", "WARP_FABRIC",
                "COCOTB_TEST_MODULES", "COCOTB_RESULTS_FILE", "SIM_BUILD", "GATES"):
        env.pop(key, None)
    result = {"scope": "mutation checks; not hardened-tile equivalence or chip timing",
              "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "workflow_run": os.environ.get("GITHUB_RUN_ID"),
              "workflow_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
              "passed": False, "controls": {}, "mutants": {}}

    def save():
        (WORK / "results.json").write_text(json.dumps(result, indent=2) + "\n")
        lines = ["# Mutation evidence campaign", "", result["scope"], "",
                 "| Mutant | Outcome | Detail |", "|---|---|---|"]
        for name, row in result["mutants"].items():
            lines.append(f"| {name} | {row['outcome']} | {row.get('detail', '')} |")
        (WORK / "REPORT.md").write_text("\n".join(lines)+"\n")

    save()
    try:
        if not env.get("WARP_TILES"):
            env["WARP_TILES"] = subprocess.check_output(
                ["bash", str(ROOT / "scripts/fetch_tiles.sh")], text=True, timeout=120).strip()
        # Establish every distinct pristine check before planting any mutation.
        for name in names:
            command = MUTANTS[name][2]
            if command in result["controls"]:
                continue
            label = f"control_{len(result['controls'])}"
            repo = WORK / label
            copy_repo(repo)
            result["controls"][command] = run_check(repo, command, env, WORK / (label+".log"))
            save()
        for name in names:
            description, edits, command, catcher = MUTANTS[name]
            row = {"description": description, "command": command, "check": catcher,
                   "outcome": "error", "killed": False}
            result["mutants"][name] = row
            if result["controls"][command]["verdict"] != "pass":
                row["detail"] = "Pristine control did not pass; mutant not executed"
                save()
                continue
            try:
                repo = WORK / name
                copy_repo(repo)
                if edits == "BITSTREAM":
                    row["mutation"] = drop_config_bit(repo)
                else:
                    for filename, old, new in edits:
                        path = repo / filename
                        original = path.read_text()
                        if original.count(old) != 1:
                            raise ValueError(f"Mutation point is not unique: {filename}")
                        path.write_text(original.replace(old, new))
                row.update(run_check(repo, command, env, WORK / (name+".log")))
                row["outcome"] = {"pass": "survived", "rejected": "killed", "error": "error"}[row["verdict"]]
                row["killed"] = row["outcome"] == "killed"
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                row["detail"] = str(exc)
            save()
            print(f"{name}: {row['outcome'].upper()}", flush=True)
        result["passed"] = all(row["killed"] for row in result["mutants"].values())
    except Exception as exc:
        result["error"] = str(exc)
        raise
    finally:
        save()
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
