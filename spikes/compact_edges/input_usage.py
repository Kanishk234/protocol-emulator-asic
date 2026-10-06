#!/usr/bin/env python3
"""Trace consumed configuration inputs through the generated fabric, not a black box."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

from prepare import DEFAULT_WORK, NAME, ROOT


def fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(work: Path) -> None:
    work = work.resolve()
    library = work / "fabulous-tiles"
    tiles = set()
    inside = False
    for row in csv.reader((work / f"{NAME}.csv").open()):
        if row and row[0] == "FabricBegin":
            inside = True
        elif row and row[0] == "FabricEnd":
            break
        elif inside:
            tiles.update(x for x in row if x and x != "NULL")
    sources = [work / "macro/fabulous" / f"{NAME}.v", library / "models_pack.v"]
    for tile in sorted(tiles):
        sources += sorted((library / "tiles/tiny" / tile).glob("*.v"))
    for primitive in ("FABULOUS_LC", "IOBUF", "GBUF", "SYS_RESET"):
        sources.append(library / "primitives" / primitive / "fabulous" / f"{primitive}.v")
    sources += sorted((ROOT / "arch/prims").glob("*.v"))
    before = {str(p): fingerprint(p) for p in sources}
    script = work / "input_usage.ys"
    output = work / "input_usage.json"
    # Upstream IOBUF contains SV function arguments; our chip RTL is unaffected.
    script.write_text("read_verilog -sv " + " ".join(f'"{p}"' for p in sources) +
                      f"\nhierarchy -check -top {NAME}\nproc\nflatten\nopt_clean\n"
                      f'write_json "{output}"\n')
    with (work / "input_usage.log").open("w") as log:
        subprocess.run(["yosys", "-Q", "-T", "-s", str(script)],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    if any(fingerprint(Path(p)) != sha for p, sha in before.items()):
        raise RuntimeError("Fabric sources changed during input trace")
    module = json.loads(output.read_text())["modules"][NAME]
    consumed = set()
    for cell in module["cells"].values():
        for port, bits in cell["connections"].items():
            if cell["port_directions"].get(port) == "input":
                consumed.update(bits)
    for port in module["ports"].values():
        if port["direction"] == "output":
            consumed.update(port["bits"])
    summary = {"workdir": str(work), "source_sha256": before, "ports": {}}
    for name in ("FrameData", "FrameStrobe"):
        bits = module["ports"][name]["bits"]
        used = [i for i, bit in enumerate(bits) if bit in consumed]
        unused = [i for i, bit in enumerate(bits) if bit not in consumed]
        summary["ports"][name] = {"width": len(bits), "used": used, "unused": unused}
        print(f"{name}: {len(used)} used / {len(bits)} inputs; unused {unused}")
    (work / "input_usage_summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    inspect(parser.parse_args().work)
