"""Prepare/run an 84-cycle compact RUN configuration-gate diagnostic.

Instrumented copies only. Existing F2 assertions/assumptions remain enabled.
The fabric outputs are arbitrary, as in F1; its storage is not modeled/proven.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "tt_um_warp_candidate.v": "391c146c47c4a7af16432a33656666dab01527a65a2a8dc59864319cd0cf5143",
    "wp_fabric_cfg.v": "37cb6da9e94b2cb22754f6b773a1c7f190adc1f6c7a110fde2cb8ee1916d22ec",
    "wp_shell.v": "96d2a648e04830de0ef25292b089b17fb5511a108b918a6f4e023fa397afba57",
    "wp_spi_target.v": "1805aa809d4cc50e5fe6493c25f3c7dad9e2446375af4c57280baf090d5adb49",
    "wp_sync.v": "7f63da354577972d707ef295625fb04051901131e64d0e4ba80a8fee01caeb3f",
    "wp_fifo.v": "c82de771d9c46c818384d0b5532b828cbec6ea81d2cb8ef0c01bb032ccc5af09",
    "wp_frame_select.v": "3d69b68396460de489f5290b25c5072f33045a7c80f03ac7542f1411e95bf08a",
    "ConfigFSM.v": "ef05899e196333ab9297ff7213a0c1358bc4dad441e1595370bf22b0f8bfe4e2",
    "Frame_Data_Reg.v": "6434b9d0d1be876a8ff49409f15ad34e4e42254436b8da151ebe0fcfc3150b81",
    "wp_crc32_shared_word.v": "0e741405d41fdeb2226c922fb59cb7d0ac5d52a7d9ddf0e297262b2a69cf3757",
}
PROPERTY = r'''
    // Only environmental reset initialization is assumed here. RUN, writes,
    // words, frame data and frame strobes are never constrained by this checker.
    reg [3:0] f_cfg_age = 0;
    always @(posedge clk)
        if (f_cfg_age != 15) f_cfg_age <= f_cfg_age + 1'b1;
    always @(*) if (f_cfg_age < 4) assume (!rst_n);
    always @(posedge clk) begin
        if (f_cfg_age >= 6 && rst_s_n && rst_cfg_n) begin
            if (running) begin
                assert (!cfg_strobe);
                assert (!cfg_restart);
                assert (frame_strobe == 140'd0);
                assert (frame_strobe_live == 140'd0);
            end
            if (running && $past(running) && $past(rst_s_n) && $past(rst_cfg_n)) begin
                assert ($stable(cfg_word));
                assert ($stable(frame_data));
            end
        end
        cover (f_cfg_age >= 6 && rst_s_n && rst_cfg_n && running);
    end
'''


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def task_passed(returncode, status):
    # The pinned SBY status includes exit code and elapsed seconds. Accept
    # exactly the documented successful token/metadata, never PASS prefixes.
    return returncode == 0 and re.fullmatch(r"PASS(?: 0 \d+(?:\.\d+)?)?", status) is not None


def instrument_top(text):
    pattern = r"    warp_g1_prune_clock_primpruned_5x3_compact_edges u_fabric \(.*?\n    \);"
    matches = list(re.finditer(pattern, text, re.S))
    if (len(matches) != 1 or text.count("endmodule") != 1
            or text.count("wire [35:0] cell_val, cell_en;") != 1):
        raise ValueError("unexpected authenticated wrapper structure")
    replacement = """    // Formal abstraction only: all user-fabric responses arbitrary.
    (* anyseq *) reg [35:0] f_cell_val, f_cell_en;
    assign cell_val = f_cell_val;
    assign cell_en = f_cell_en;"""
    text = re.sub(pattern, replacement, text, count=1, flags=re.S)
    return text.replace("endmodule", PROPERTY + "\nendmodule")


def prepare(materialized, out):
    info = json.loads(materialized.read_text())
    work = Path(info["native_work"])
    config = json.loads((work / "chip_shared_crc_cfgbranches/config.json").read_text())
    files = [Path(name) for name in config["VERILOG_FILES"]]
    if len(files) != len(EXPECTED) or {p.name for p in files} != set(EXPECTED):
        raise ValueError("unexpected compact source inventory")
    for path in files:
        if digest(path) != EXPECTED[path.name]:
            raise ValueError("actual compact source hash mismatch: " + path.name)
    shell = next(p for p in files if p.name == "wp_shell.v").read_text()
    if "`ifdef FORMAL_F2" not in shell or "assume (!(rx_valid && crc_busy));" not in shell:
        raise ValueError("missing original F2 property/assumption")
    out.mkdir(parents=True, exist_ok=False)
    for path in files:
        text = path.read_text()
        if path.name == "tt_um_warp_candidate.v":
            text = instrument_top(text)
        (out / path.name).write_text(text)
    names = " ".join(EXPECTED)
    sby = f'''[tasks]
bmc
cover
[options]
bmc: mode bmc
bmc: depth 84
cover: mode cover
cover: depth 84
[engines]
bmc: abc bmc3
cover: smtbmc yices
[script]
read -formal -DFORMAL_F2 {names}
prep -top tt_um_warp
cutpoint wp_spi_target
flatten
async2sync
dffunmap
[files]
''' + "\n".join(EXPECTED) + "\n"
    (out / "run_config.sby").write_text(sby)
    return {"scope": "84-cycle bounded RUN configuration-gate premise; not mapped-latch equivalence or timing",
            "source_sha256": EXPECTED, "generated_top_sha256": digest(out / "tt_um_warp_candidate.v"),
            "sby_sha256": digest(out / "run_config.sby"), "depth": 84,
            "environment": ["raw reset low for first four cycles", "existing F2 first-cycle shell reset",
                            "existing F2 no rx_valid while crc_busy"],
            "abstraction": ["SPI receiver outputs arbitrary", "fabric response outputs arbitrary"],
            "formal_transformations": ["async2sync", "dffunmap"],
            "reset_scope": "clock-cycle model; not analog reset or pulse-width safety",
            "required": ["bmc PASS", "cover PASS including reachable RUN"],
            "cover_semantics": "SymbiYosys cover PASS requires all instantiated covers, including the new wrapper RUN cover",
            "passed": False, "source_inputs_edited": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--materialized", type=Path, default=ROOT / "build/cloud_input/materialized.json")
    parser.add_argument("--out", type=Path, default=ROOT / "build/run_config_property_evidence")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    result = prepare(args.materialized, args.out)
    result["status"] = "prepared_not_proven"
    try:
        if not args.prepare_only:
            versions = subprocess.run(["yosys", "-V"], capture_output=True, text=True, check=True)
            result["yosys_version"] = versions.stdout.strip()
            result["tasks"] = {}
            for task in ("bmc", "cover"):
                try:
                    with (args.out / (task + ".log")).open("w") as log:
                        completed = subprocess.run(["sby", "-f", "run_config.sby", task],
                                                   cwd=args.out, stdout=log, stderr=subprocess.STDOUT,
                                                   timeout=900)
                    status_path = args.out / ("run_config_" + task) / "status"
                    status = status_path.read_text().strip() if status_path.is_file() else "MISSING"
                    result["tasks"][task] = {"returncode": completed.returncode, "status": status,
                                              "passed": task_passed(completed.returncode, status)}
                except subprocess.TimeoutExpired:
                    result["tasks"][task] = {"passed": False, "status": "TIMEOUT"}
            result["passed"] = all(v["passed"] for v in result["tasks"].values())
            result["status"] = "bounded_pass" if result["passed"] else "failed"
    finally:
        (args.out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return 0 if args.prepare_only or result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
