#!/usr/bin/env python3
"""Apply the measured LUT switch-choice manifest to a disposable macro copy.

This reproduces the 2026-09-28 screen; it does not select or endorse an
architecture. Input files are never edited.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from route_prune_common import parse_fasm_pips, parse_lut_tiles


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pips", type=Path, required=True, help="input .FABulous/pips.txt")
    parser.add_argument("--bel", type=Path, required=True, help="input .FABulous/bel.txt")
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("removed_pips.csv"))
    parser.add_argument("--fasm", type=Path, nargs="+", required=True, help="routes that must remain selectable")
    parser.add_argument("--output", type=Path, required=True, help="new output PIPs file")
    args = parser.parse_args()

    removed_choices = {
        (row["source"], row["destination"])
        for row in csv.DictReader(args.manifest.open(newline=""))
    }
    if not removed_choices:
        raise ValueError(f"empty removal manifest: {args.manifest}")
    if args.output.resolve() == args.pips.resolve():
        raise ValueError("output must not overwrite the input PIPs file")

    lut_tiles = parse_lut_tiles(args.bel)
    active = parse_fasm_pips(args.fasm)
    conflicts = sorted(
        (tile, source, destination)
        for tile, source, destination in active
        if tile in lut_tiles and (source, destination) in removed_choices
    )
    if conflicts:
        raise ValueError(f"manifest removes {len(conflicts)} routed LUT-tile choices; first: {conflicts[0]}")

    lines = args.pips.read_text().splitlines()
    output: list[str] = []
    removed_per_tile = {tile: 0 for tile in lut_tiles}
    for line in lines:
        fields = line.split(",")
        if len(fields) == 6:
            tile, source, dst_tile, destination = fields[:4]
            if (
                tile == dst_tile
                and tile in lut_tiles
                and (source, destination) in removed_choices
            ):
                removed_per_tile[tile] += 1
                continue
        output.append(line)

    if any(count != len(removed_choices) for count in removed_per_tile.values()):
        raise ValueError(f"manifest does not match every LUT tile: {removed_per_tile}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(output) + "\n")
    print(f"LUT tiles: {len(lut_tiles)}")
    print(f"Manifest choices per tile: {len(removed_choices)}")
    print(f"Removed internal PIPs: {sum(removed_per_tile.values())}")
    print(f"Preserved FASM files checked: {len(args.fasm)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
