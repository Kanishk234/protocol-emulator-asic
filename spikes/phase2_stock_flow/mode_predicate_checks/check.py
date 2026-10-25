"""Replay the source-bound configuration predicate proofs and phase tests.

Run with the project venv. BASE/src must be the prepared full stock candidate
before mode_predicate.patch; WORK must be a new scratch directory.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("work", type=Path)
    args = parser.parse_args()
    package = Path(__file__).resolve().parent.parent
    evidence = json.loads((package / "mode_predicate_evidence.json").read_text())
    baseline, work = args.baseline.resolve(), args.work.resolve()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(package / "mode_predicate.patch") == evidence["patch_sha256"]
    for name, digest in evidence["baseline_files"].items():
        assert sha(baseline / name) == digest, name
    work.mkdir(parents=True, exist_ok=False)
    shutil.copytree(baseline / "src", work / "src")
    before = {str(p.relative_to(work)): sha(p) for p in (work / "src").rglob("*") if p.is_file()}
    subprocess.run(["patch", "--batch", "--forward", "-p1", "-i", str(package / "mode_predicate.patch")], cwd=work, check=True)
    after = {str(p.relative_to(work)): sha(p) for p in (work / "src").rglob("*") if p.is_file()}
    assert after == {**before, **evidence["candidate_files"]}
    (work / "gold_pin_cfg.v").write_text((baseline / "src/trw_pin_cfg.v").read_text().replace("module trw_pin_cfg #", "module gold_pin_cfg #"))
    env = os.environ.copy()
    env["PATH"] += ":" + str(Path.home() / "oss-cad-suite/bin")

    def run(command, name, expect_failure=False):
        log = work / (name + ".log")
        with log.open("w") as stream:
            result = subprocess.run(command, cwd=work, env=env, stdout=stream, stderr=subprocess.STDOUT)
        text = log.read_text()
        if expect_failure:
            assert result.returncode != 0 and "proof did fail" in text, log
        else:
            assert result.returncode == 0, log
        return text

    receipts = []
    for mode in ("latch", "flop"):
        define = ["-DTRW_PIN_CFG_FLOPS"] if mode == "flop" else []
        for full in (0, 1):
            name = f"{mode}-{full}"
            binary = work / name
            run(["iverilog", "-g2012", *define, "-I" + str(work / "src"), "-s", "tb_cache", "-Ptb_cache.FULL=" + str(full), "-o", str(binary), str(package / "mode_predicate_checks/tb_cache.v"), str(work / "gold_pin_cfg.v"), str(work / "src/trw_pin_cfg.v")], name + "-compile")
            assert "PASS cache:" in run(["vvp", str(binary)], name + "-simulation")
            script = (f'read_verilog -formal {" ".join(define)} -Isrc "{work}/src/trw_pin_cfg.v" "{package}/mode_predicate_checks/contract.v"\n'
                      f"chparam -set FULL {full} mode_contract\n"
                      "prep -top mode_contract -flatten\nclk2fflogic\nopt -full\n"
                      "sat -tempinduct -seq 4 -maxsteps 20 -prove-asserts -set-assumes -verify\n")
            ys = work / (name + ".ys")
            ys.write_text(script)
            assert "SUCCESS!" in run(["yosys", "-Q", "-T", "-s", str(ys)], name + "-proof")
            receipts.append(name)
            if name == "latch-1":
                mutation = (work / "src/trw_pin_cfg.v").read_text().replace("wdata[`TRW_PC_TXMODE_MSB:`TRW_PC_TXMODE_LSB] == `TRW_PCE_TXMODE_BITSYNC", "wdata[`TRW_PC_TXMODE_MSB:`TRW_PC_TXMODE_LSB] == `TRW_PCE_TXMODE_SHIFT")
                assert mutation != (work / "src/trw_pin_cfg.v").read_text()
                (work / "wrong_mode.v").write_text(mutation)
                negative = work / "negative.ys"
                negative.write_text(script.replace(str(work / "src/trw_pin_cfg.v"), str(work / "wrong_mode.v")))
                run(["yosys", "-Q", "-T", "-s", str(negative)], "negative", expect_failure=True)
    receipt = dict(cases=receipts, negative_control="wrong-mode property rejected", patch_sha256=evidence["patch_sha256"], physical_qualification=False)
    (work / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
