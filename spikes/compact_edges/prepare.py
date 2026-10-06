#!/usr/bin/env python3
"""Stage a smaller boundary around the existing 5 x 3 scratch fabric.

The logic/primitive tiles and logical routing graph are reused unchanged. Each
changed edge tile must be hardened again before stitching. This script copies
the phase-aligned scratch library; it never changes its source or macro views.
"""

import argparse
import json
from pathlib import Path
import shutil

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "build/arch_explore/fabric_5x3_phase_aligned/fabulous-tiles"
DEFAULT_WORK = ROOT / "build/arch_explore/compact_edges"
NAME = "warp_g1_prune_clock_primpruned_5x3_compact_edges"
EDGE_TILES = (
    "N_IO", "N_IO_C2", "N_IO_C3", "N_IO_C4", "N_IO_C5",
    "S_IO2", "S_IO2_C2", "S_IO2_C3", "S_IO2_C4", "S_IO2_C5",
    "NW_term", "NE_term_wide", "SW_term", "SE_term_wide",
)


def prepare(source: Path, work: Path, north_height: float = 37.80,
            south_height: float = 49.14) -> None:
    for height in (north_height, south_height):
        if height < 7.56 or abs(height / 3.78 - round(height / 3.78)) > 0.00001:
            raise ValueError("Edge heights must align to the CMOS5L 3.78 um row")
    fabric_dir = source.absolute().parent
    source, work = source.resolve(), work.resolve()
    library = work / "fabulous-tiles"
    if source == library or source in work.parents or work in source.parents:
        raise ValueError("Source and experiment directories must be separate")
    if not (source / "tiles.py").is_file():
        raise FileNotFoundError(f"Missing phase-aligned tile driver: {source}")
    fabric_files = list(fabric_dir.glob("*_phase_aligned.csv"))
    if len(fabric_files) != 1:
        raise ValueError("Source directory must contain one phase-aligned fabric CSV")
    shutil.copytree(
        source, library, dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("macro", "runs", ".git", "__pycache__"),
    )
    for tile in (source / "tiles/tiny").iterdir():
        macro = tile / "macro"
        link = library / "tiles/tiny" / tile.name / "macro"
        if tile.is_dir() and tile.name not in EDGE_TILES and macro.is_dir():
            if not link.exists():
                link.symlink_to(macro, target_is_directory=True)

    # Runtime overrides keep the copied upstream driver intact. Heights align
    # to the CMOS5L 3.78 um row and 0.42 um horizontal routing pitch.
    (work / "run_tile.py").write_text('''#!/usr/bin/env python3
import importlib.util
import os
from pathlib import Path
import sys

library = Path(__file__).resolve().parent / "fabulous-tiles"
spec = importlib.util.spec_from_file_location("warp_tile_driver", library / "tiles.py")
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
sizes = driver.tile_sizes["tiny"]["ihp-sg13*"]
for tile, (width, height) in list(sizes.items()):
    if tile.startswith(("N_IO", "NW", "NE")) or tile == "N*":
        sizes[tile] = (width, NORTH_HEIGHT)
    elif tile.startswith(("S_IO2", "SW", "SE")) or tile == "S*":
        sizes[tile] = (width, SOUTH_HEIGHT)
driver.main(sys.argv[1], pdk="ihp-sg13cmos5l",
            pdk_root=os.environ["PDK_ROOT"], tile_library="tiny")
'''.replace("NORTH_HEIGHT", repr(north_height)).replace("SOUTH_HEIGHT", repr(south_height)))
    (work / f"{NAME}.csv").write_text(fabric_files[0].read_text())
    config = yaml.safe_load((fabric_dir / "config.yaml").read_text())
    config["DESIGN_NAME"] = NAME
    config["FABULOUS_FABRIC_CONFIG"] = f"dir::{NAME}.csv"
    config["FABULOUS_TILE_LIBRARY"] = "dir::fabulous-tiles/tiles/tiny/"
    (work / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False))
    manifest = {
        "source_library": str(source), "design_name": NAME,
        "north_height_um": north_height, "south_height_um": south_height,
        "expected_width_um": 1120.32,
        "expected_height_um": round(3 * 196.56 + north_height + south_height, 2),
        "logic_columns": 5, "logic_rows": 3,
        "reharden_tiles": list(EDGE_TILES),
        "limits": "Physical experiment; requires stitch and complete shell checks",
    }
    (work / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(work)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--north-height", type=float, default=37.80)
    parser.add_argument("--south-height", type=float, default=49.14)
    args = parser.parse_args()
    prepare(args.source, args.work, args.north_height, args.south_height)
