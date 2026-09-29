"""Shared parsing helpers for the disposable route-pruning experiment."""

from pathlib import Path
import re

_FASM_PIP = re.compile(r"^(X\d+Y\d+)\.([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)$")


def parse_lut_tiles(bel_file: Path) -> set[str]:
    tiles = {
        fields[0]
        for line in bel_file.read_text().splitlines()
        if len(fields := line.split(",")) > 4 and fields[4] == "FABULOUS_LC"
    }
    if not tiles:
        raise ValueError(f"no FABULOUS_LC tile entries in {bel_file}")
    return tiles


def parse_fasm_pips(fasm_files: list[Path]) -> set[tuple[str, str, str]]:
    active: set[tuple[str, str, str]] = set()
    for fasm_file in fasm_files:
        for line in fasm_file.read_text().splitlines():
            match = _FASM_PIP.fullmatch(line.strip())
            if match:
                active.add(match.groups())
    return active
