"""WARP bitstream generator: FASM + FABulous bitstream spec -> configuration words.

The FABulous frame format (as fabulous_bit_gen 0.3.1 writes it, and as the shell's ConfigFSM
reads it): the sync word 0xFAB0FAB1; for each column, for each frame, a frame-select word
(column << (32 - FRAME_SELECT_WIDTH) | 1 << frame) followed by one data word per fabric row,
bottom row first; then a desync word (1 << DESYNC_BIT). Data word bit i of a tile's frame f is
the spec's tile bit 32*f + i.

Why not fabulous_bit_gen itself (BUGS #13): it drops every FASM feature whose name contains
"CLK", which silently loses the tile library's global-clock mux selects (`...GCLK_BEG0`); a design
whose clock is routed through any GBUF but the first then never gets a clock. It also leaves
out the edge rows unless the spec asks for them, which ours need. tools/compile/tests check that
this generator matches fabulous_bit_gen word for word on every other feature.
"""

import pickle
from typing import Dict, Iterable, List

from fasm import fasm_tuple_to_string, parse_fasm_filename, parse_fasm_string, set_feature_to_str

SYNC_WORD = 0xFAB0FAB1
FRAME_SELECT_WIDTH = 5
DESYNC_BIT = 20


class BitgenError(Exception):
    pass


def fasm_features(fasm_file) -> List[str]:
    """Canonical feature strings (multi-bit features like INIT[15:0] split into single bits),
    parsed the same way fabulous_bit_gen does."""
    canon = fasm_tuple_to_string(parse_fasm_filename(str(fasm_file)), True)
    return [set_feature_to_str(line.set_feature) for line in parse_fasm_string(canon)
            if line.set_feature]


def load_spec(spec_file) -> dict:
    with open(spec_file, "rb") as f:
        return pickle.load(f)


def tile_bits(features: Iterable[str], spec: dict) -> Dict[str, List[int]]:
    arch = spec["ArchSpecs"]
    total = arch["MaxFramesPerCol"] * arch["FrameBitsPerRow"]
    bits = {tile: [0] * total for tile in spec["TileMap"]}
    for feat in features:
        parts = feat.split(".")
        if len(parts) != 3:
            raise BitgenError(f"feature {feat!r}: expected tile.a.b")
        tile, name = parts[0], f"{parts[1]}.{parts[2]}"
        specs = spec["TileSpecs"].get(tile)
        if specs is None:
            raise BitgenError(f"feature {feat!r}: tile {tile} not in the bitstream spec")
        if name not in specs:
            raise BitgenError(f"feature {feat!r}: not in the spec of {spec['TileMap'][tile]}")
        for idx, val in specs[name].items():
            bits[tile][idx] = int(val)
    return bits


def words(features: Iterable[str], spec: dict) -> List[int]:
    arch = spec["ArchSpecs"]
    fbits, nframes = arch["FrameBitsPerRow"], arch["MaxFramesPerCol"]
    if fbits != 32:
        raise BitgenError("only 32-bit frames are supported")
    bits = tile_bits(features, spec)
    cols = 1 + max(int(t[1:].split("Y")[0]) for t in spec["TileMap"])
    rows = 1 + max(int(t.split("Y")[1]) for t in spec["TileMap"])
    if cols > 1 << FRAME_SELECT_WIDTH or nframes > DESYNC_BIT:
        raise BitgenError("fabric too large for the frame-select word")
    out = [SYNC_WORD]
    for x in range(cols):
        for f in range(nframes):
            out.append(x << (32 - FRAME_SELECT_WIDTH) | 1 << f)
            for y in range(rows - 1, -1, -1):
                tile = f"X{x}Y{y}"
                if spec["TileMap"].get(tile, "NULL") == "NULL":
                    out.append(0)
                    continue
                b = bits[tile][fbits * f: fbits * (f + 1)]
                out.append(sum(v << i for i, v in enumerate(b)))
    out.append(1 << DESYNC_BIT)
    return out


def gen_words(fasm_file, spec_file) -> List[int]:
    return words(fasm_features(fasm_file), load_spec(spec_file))
