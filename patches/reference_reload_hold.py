"""ANISH-D2: experimental LUT/carry isolation in a COPY of the reference RTL.

Not a production FABulous generator patch or a complete isolation solution.
Original license headers survive in copied sources; installed upstream code
and the original generated reference remain untouched.
"""

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil

EXPECTED = {
    "LUT4c_frame_config_dffesr.v": "bce67a382fc67d25f1844d01ab35a7ce6bcfffbb8bc6f7afc6376ff0d28eea78",
    "LUT4AB.v": "925d23434a0470c85cb8ac948382052675a20167dbf1101e271a68ae14dfe3c6",
    "eFPGA.v": "d7c51cc49e1644cfac0d1698eebab563e2f4c07ed1f4551411650ad45dcd4fd2",
    "eFPGA_top.v": "e5b9fa8c87ad4732a8753a177f0654b3084a4aecb741a14752d4d3b488906126",
}


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Expected exactly one anchor: {old!r}")
    return text.replace(old, new, 1)


def transform(name, text):
    if name == "LUT4c_frame_config_dffesr.v":
        text = replace_once(text, ") (\n", ") (\n    input wire ReloadHold,\n")
        text = replace_once(text, "    wire LUT_out;", "    wire LUT_out;\n    wire unmasked_O;\n    assign O = ReloadHold ? 1'b0 : unmasked_O;")
        text = replace_once(text, ".X (O)", ".X (unmasked_O)")
        text = replace_once(text, "assign Co = (Ci & I[1]) | (Ci & I[2]) | (I[1] & I[2]);",
                            "assign Co = ReloadHold ? 1'b0 : ((Ci & I[1]) | (Ci & I[2]) | (I[1] & I[2]));")
    else:
        header = re.match(r"\Amodule\s+\w+[\s\S]*?\n    \(\n", text)
        if header is None:
            raise ValueError(f"Missing module port header: {name}")
        text = text[:header.end()] + "        input ReloadHold,\n" + text[header.end():]
        if name == "LUT4AB.v":
            text, count = re.subn(r"(LUT4c_frame_config_dffesr Inst_L[A-H]_LUT4c_frame_config_dffesr \(\n)", r"\1    .ReloadHold(ReloadHold),\n", text)
            if count != 8:
                raise ValueError("Expected 8 LUT cells")
        elif name == "eFPGA.v":
            text, count = re.subn(r"(    Tile_X\d+Y\d+_LUT4AB\n    \(\n)", r"\1    .ReloadHold(ReloadHold),\n", text)
            if count != 84:
                raise ValueError(f"Expected 84 LUT tiles, got {count}")
        else:
            text = replace_once(text, "eFPGA eFPGA_inst (\n", "eFPGA eFPGA_inst (\n    .ReloadHold(ReloadHold),\n")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    # Validate every original before creating any output.
    for name, expected in EXPECTED.items():
        if hashlib.sha256((args.source / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Unsupported reference source: {name}")
    shutil.copytree(args.source, args.output)  # Refuses an existing destination.
    patches, manifest = [], {}
    for name in EXPECTED:
        before = (args.source / name).read_text()
        after = transform(name, before)
        (args.output / name).write_text(after)
        manifest[name] = {"original": EXPECTED[name], "patched": hashlib.sha256((args.output / name).read_bytes()).hexdigest()}
        patches.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile="original/" + name, tofile="candidate/" + name))
    (args.output.parent / "reload-hold.patch").write_text("".join(patches))
    (args.output.parent / "patch-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
