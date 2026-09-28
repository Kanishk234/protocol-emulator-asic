#!/usr/bin/env python3
"""Fault-injection (mutation) campaign, phase 4 (VERIFICATION.md): plant one realistic bug at a
time in a throwaway copy of the repository and run the checks that should catch it. A mutant is
"killed" when its check fails. Survivors are findings: either a gap in the checks or an
equivalent mutant (explained in the report).

Usage: scripts/mutation.py [names...]      Output: docs/reports/mutation.md (and build/mutation/)
Needs: the project venv, the OSS CAD Suite, a fetched tile library (WARP_TILES), SymbiYosys.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "build" / "mutation"

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
    names = argv or list(MUTANTS)
    env = dict(os.environ)
    env.setdefault("WARP_TILES", subprocess.check_output([str(ROOT / "scripts/fetch_tiles.sh")], text=True).strip())
    old = WORK / "results.json"                  # keep earlier mutants' results when running a subset
    results = json.loads(old.read_text()) if argv and old.exists() else {}
    for name in names:
        desc, edits, cmd, catcher = MUTANTS[name]
        repo = WORK / name
        copy_repo(repo)
        detail = ""
        if edits == "BITSTREAM":
            detail = "`" + drop_config_bit(repo) + "`"
        else:
            for f, old, new in edits:
                p = repo / f
                s = p.read_text()
                assert s.count(old) == 1, f"{name}: mutation point not unique in {f}"
                p.write_text(s.replace(old, new))
        t0 = time.time()
        r = subprocess.run(["bash", "-c", cmd], cwd=repo, env=env, capture_output=True, text=True)
        out = r.stdout + r.stderr
        failed = r.returncode != 0 or "FAIL=0" not in out and "TESTS=" in out
        if "sby" in cmd:
            failed = "DONE (PASS" not in out
        results[name] = {"description": desc, "check": catcher, "command": cmd, "killed": failed,
                         "seconds": round(time.time() - t0), "detail": detail}
        print(f"{name}: {'KILLED' if failed else 'SURVIVED'} ({results[name]['seconds']} s)", flush=True)
        (WORK / f"{name}.log").write_text(out)
    (WORK / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    lines = ["# Mutation campaign (phase 4)", "",
             "Each mutant plants one realistic bug in a throwaway copy of the repository (`scripts/mutation.py`); the check listed must fail. Local run.", "",
             "| Mutant | Bug planted | Check that should catch it | Result |", "|---|---|---|---|"]
    for n, r in results.items():
        d = r["description"] + (f" ({r['detail']})" if r["detail"] else "")
        lines.append(f"| `{n}` | {d} | {r['check']} | {'**killed**' if r['killed'] else '**survived**'} |")
    report = ROOT / "docs/reports/mutation.md"
    notes = report.read_text().split("\n## Notes", 1) if report.exists() else []
    if len(notes) == 2:                          # the hand-written notes section is kept
        lines += ["", "## Notes" + notes[1].rstrip("\n")]
    report.write_text("\n".join(lines) + "\n")
    return 0 if all(r["killed"] for r in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
