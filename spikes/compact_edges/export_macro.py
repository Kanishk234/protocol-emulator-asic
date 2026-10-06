#!/usr/bin/env python3
"""Export the stitched compact macro LEF and its IHP placement boundary."""

import argparse
from pathlib import Path
import re
import subprocess

from prepare import DEFAULT_WORK, NAME, ROOT


def export(work: Path) -> None:
    work = work.resolve()
    macro = work / "macro"
    lef = macro / "lef" / f"{NAME}.lef"
    lef.parent.mkdir(exist_ok=True)
    script = work / "export_lef.tcl"
    script.write_text(
        f"read_db {{{macro / 'odb' / (NAME + '.odb')}}}\n"
        f"write_abstract_lef -bloat_occupied_layers {{{lef}}}\n"
    )
    with (work / "lef.log").open("w") as log:
        subprocess.run(["openroad", "-exit", "-no_splash", str(script)],
                       check=True, stdout=log, stderr=subprocess.STDOUT)
    # Unused VIA definitions contain CUTSIZE, which the pinned FABulous
    # geometry reader mistakes for a macro SIZE. Keep any actually referenced.
    text = lef.read_text()
    used = set(re.findall(r"(?m)^\s+VIA\s+\S+\s+\S+\s+(\S+)", text))
    text = re.sub(
        r"(?ms)^VIA\s+(\S+)[^\n]*\n.*?^END\s+\1\s*$",
        lambda match: match[0] if match[1] in used else "", text,
    )
    lef.write_text(text)
    width, height = re.search(r"\bSIZE\s+([\d.]+)\s+BY\s+([\d.]+)", text).groups()
    gds = macro / "gds" / f"{NAME}.gds"
    with (work / "prboundary.log").open("w") as log:
        subprocess.run([
            "klayout", "-b", "-r", str(ROOT / "spikes/fabric_tiny/add_prboundary.py"),
            "-rd", f"gds={gds}", "-rd", f"out={gds}",
            "-rd", f"w={width}", "-rd", f"h={height}",
        ], check=True, stdout=log, stderr=subprocess.STDOUT)
    print(f"{NAME}: {width} x {height} um")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    args = parser.parse_args()
    export(args.work)
