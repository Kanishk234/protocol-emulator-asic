#!/usr/bin/env python3
"""Stage the complete shell and real configuration path around the compact macro."""

import argparse
import hashlib
import json
from pathlib import Path
import re

from prepare import DEFAULT_WORK, NAME, ROOT


def prepare_chip(work: Path, y: float, local_decode: bool = False,
                 vertical_halo: float = 10.0, chip_dir: str | None = None,
                 mask_unused_strobes: bool = False,
                 shared_word_crc: bool = False) -> None:
    work = work.resolve()
    macro = work / "macro"
    metrics = json.loads((macro / "metrics.json").read_text())
    if metrics.get("klayout__drc_error__count") != 0:
        raise ValueError("Stitched macro must have an explicit zero KLayout DRC result")
    lef = macro / "lef" / f"{NAME}.lef"
    text = lef.read_text()
    match = re.search(r"\bSIZE\s+([\d.]+)\s+BY\s+([\d.]+)\s*;", text)
    width, height = map(float, match.groups())
    manifest = json.loads((work / "manifest.json").read_text())
    if (abs(width - manifest["expected_width_um"]) > 0.001 or
            abs(height - manifest["expected_height_um"]) > 0.001):
        raise ValueError(f"Unexpected compact fabric size: {width} x {height}")
    if y < 3.78 or y + height > 706.861:
        raise ValueError("Placement extends beyond the TT core")
    chip = work / (chip_dir or ("chip_local_decode" if local_decode else "chip"))
    chip.mkdir(exist_ok=True)
    # Block all signal layers over the hard fabric, including Metal4. Power
    # column access is retained in its original PIN geometry. This deliberately
    # requires the shell to route in the space outside the real fabric.
    obs = "  OBS\n" + "".join(
        f"    LAYER Metal{layer} ;\n      RECT 0 0 {width:.2f} {height:.2f} ;\n"
        for layer in range(1, 5)
    ) + "  END"
    if not re.search(r"(?m)^\s*OBS\s*$", text):
        raise ValueError("Expected an OBS block in the extracted macro LEF")
    text = re.sub(r"(?ms)^\s*OBS\s*\n.*?^\s*END\s*$", obs, text, count=1)
    routed_lef = chip / f"{NAME}.lef"
    routed_lef.write_text(text)
    old = ROOT / "build/arch_explore/chip_5x3_phase_aligned"
    old_name = "warp_g1_prune_clock_primpruned_5x3_phase_aligned"
    rtl = chip / "tt_um_warp_candidate.v"
    chip_rtl = (old / "tt_um_warp_candidate.v").read_text().replace(old_name, NAME)
    if mask_unused_strobes:
        usage = json.loads((work / "input_usage_summary.json").read_text())
        if usage["workdir"] != str(work):
            raise ValueError("Input trace belongs to a different work directory")
        for path, sha in usage["source_sha256"].items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != sha:
                raise ValueError(f"Stale input trace: {path}")
        port = usage["ports"]["FrameStrobe"]
        if port["width"] != 140:
            raise ValueError("Expected 140 frame-strobe macro inputs")
        mask = sum(1 << i for i in port["used"])
        declaration = "    wire [20*COLS-1:0] frame_strobe;"
        if chip_rtl.count(declaration) != 1 or chip_rtl.count(".FrameStrobe (frame_strobe)") != 1:
            raise ValueError("Unexpected candidate configuration wiring")
        chip_rtl = chip_rtl.replace(declaration, declaration +
            "\n    // Only macro inputs proven unconsumed by the generated fabric are masked."
            "\n    // Actual configuration storage and all consumed strobes remain live."
            "\n    wire [20*COLS-1:0] frame_strobe_live;"
            f"\n    assign frame_strobe_live = frame_strobe & 140'h{mask:035x};")
        chip_rtl = chip_rtl.replace(".FrameStrobe (frame_strobe)", ".FrameStrobe (frame_strobe_live)")
    rtl.write_text(chip_rtl)
    blackbox = chip / f"{NAME}.v"
    blackbox.write_text((old / "fabric_blackbox.v").read_text().replace(old_name, NAME))
    config = json.loads((old / "config.json").read_text())
    config["MACROS"] = {NAME: {
        "instances": {"u_fabric": {"location": [121.44, y], "orientation": "N"}},
        "gds": [str(macro / "gds" / f"{NAME}.gds")],
        "lef": [str(routed_lef)], "nl": [str(blackbox)],
    }}
    config["VERILOG_FILES"][0] = str(rtl)
    if shared_word_crc:
        shell = (ROOT / "src/wp_shell.v").read_text()
        if shell.count("wp_crc32 u_crc") != 1:
            raise ValueError("Unexpected shell CRC instantiation")
        shell_path = chip / "wp_shell.v"
        connection = ".word_valid(word_done), .word(word),"
        if shell.count(connection) != 1:
            raise ValueError("Unexpected CRC word connection")
        shell_path.write_text(shell.replace("wp_crc32 u_crc", "wp_crc32_shared_word u_crc")
                              .replace(connection, ".word_valid(word_done), .word(cfg_word),"))
        config["VERILOG_FILES"] = [str(shell_path) if Path(path).name == "wp_shell.v"
                                    else path for path in config["VERILOG_FILES"]
                                    if Path(path).name != "wp_crc32.v"]
        config["VERILOG_FILES"].append(str(ROOT / "spikes/compact_edges/wp_crc32_shared_word.v"))
    config["MAGIC_EXT_ABSTRACT_CELLS"] = [NAME]
    config["FP_OBSTRUCTIONS"] = []
    config["PL_ROUTABILITY_DRIVEN"] = False
    config["PL_TARGET_DENSITY_PCT"] = 95
    config["PL_MAX_DISPLACEMENT_X"] = 1280
    config["PL_MAX_DISPLACEMENT_Y"] = 704
    config["FP_MACRO_VERTICAL_HALO"] = vertical_halo
    if local_decode:
        # Map each module before flattening. Keeping modules in the final
        # netlist fails the stock unmapped-cell gate; deferred flattening uses
        # the supported flow and yields an ordinary standard-cell netlist.
        config["SYNTH_HIERARCHY_MODE"] = "deferred_flatten"
    config["PDN_CFG"] = str(ROOT / "src/pdn_cfg.tcl")
    config["RUN_KLAYOUT_DRC"] = 1
    (chip / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    print(f"{chip}: real shell/loader; macro {width:.2f} x {height:.2f} at (121.44, {y:.2f})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--y", type=float, default=15.12)
    parser.add_argument("--local-decode", action="store_true")
    parser.add_argument("--vertical-halo", type=float, default=10.0,
                        help="Macro clearance in um; 3.78 retains bottom cell rows")
    parser.add_argument("--chip-dir", help="Isolated chip subdirectory for placement sweeps")
    parser.add_argument("--mask-unused-strobes", action="store_true",
                        help="Requires a fresh input_usage.py trace; affects unconsumed macro inputs only")
    parser.add_argument("--shared-word-crc", action="store_true",
                        help="Scratch shell experiment; CRC reuses the stable shell word")
    args = parser.parse_args()
    prepare_chip(args.work, args.y, args.local_decode, args.vertical_halo,
                 args.chip_dir, args.mask_unused_strobes, args.shared_word_crc)
