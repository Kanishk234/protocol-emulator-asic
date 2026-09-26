"""Decode only the pinned 10-column/14-row FABulous reference image format.

Emit static EMULATION parameters for a frame-boundary snapshot. This is a
white-box diagnostic, not a replacement for loading the live fabric in tests.
No pickle/spec deserialization or external package dependencies are needed.
"""

import argparse
import re
from pathlib import Path

HEADER = bytes.fromhex("00aaff01000000010000000000000000fab0fab1")
ROWS, COLS, FRAMES = 14, 10, 20
RECORD_BYTES = 4 * (1 + ROWS)


def decode(data: bytes) -> list[tuple[int, int, tuple[int, ...]]]:
    if len(data) != len(HEADER) + COLS * FRAMES * RECORD_BYTES + 4:
        raise ValueError("Expected an unpadded 12024-byte reference image")
    if not data.startswith(HEADER) or data[-4:] != bytes.fromhex("00100000"):
        raise ValueError("Bad reference sync header or desync word")
    records = []
    for index in range(COLS * FRAMES):
        start = len(HEADER) + index * RECORD_BYTES
        col, frame = divmod(index, FRAMES)
        address = int.from_bytes(data[start : start + 4], "big")
        if address != (col << 27) | (1 << frame):
            raise ValueError(f"Unexpected frame-select word at byte {start}")
        words = tuple(
            int.from_bytes(data[pos : pos + 4], "big")
            for pos in range(start + 4, start + RECORD_BYTES, 4)
        )
        records.append((col, frame, words))
    return records


def snapshot(old: bytes, new: bytes, frames_written: int) -> dict[tuple[int, int], int]:
    if not 0 <= frames_written <= COLS * FRAMES:
        raise ValueError("frames_written must be between 0 and 200 inclusive")
    before, after = decode(old), decode(new)
    values = {(x, y): 0 for x in range(COLS) for y in range(1, ROWS + 1)}
    for col, frame, words in after[:frames_written] + before[frames_written:]:
        for row, word in zip(range(ROWS, 0, -1), words):
            values[col, row] |= word << (32 * frame)
    return values


def emit(values: dict[tuple[int, int], int]) -> str:
    return "".join(
        f"`define Tile_X{x}Y{y}_Emulate_Bitstream 640'h{bits:0160x}\n"
        for (x, y), bits in sorted(values.items())
    )


def validate_header(data: bytes, text: str) -> int:
    """Cross-check row/bit order against the independently generated tool header."""
    values = snapshot(data, data, 0)
    macros = re.findall(r"`define Tile_X(\d+)Y(\d+)_Emulate_Bitstream 640'b([01]{640})", text)
    if not macros:
        raise ValueError("No reference emulation macros found")
    seen = set()
    for x, y, bits in macros:
        key = int(x), int(y)
        if key in seen or key not in values or values[key] != int(bits, 2):
            raise ValueError(f"Emulation-header mismatch/duplicate at {key}")
        seen.add(key)
    if any(value != 0 for key, value in values.items() if key not in seen):
        raise ValueError("Header omits nonzero tile configuration")
    return len(seen)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("frames_written", type=int)
    parser.add_argument("output", type=Path)
    parser.add_argument("--validate-final-header", type=Path)
    args = parser.parse_args()
    if args.validate_final_header:
        count = validate_header(args.new.read_bytes(), args.validate_final_header.read_text())
        print(f"Binary row/bit order matches all {count} tool-generated emulation macros")
    args.output.write_text(
        emit(snapshot(args.old.read_bytes(), args.new.read_bytes(), args.frames_written)),
        encoding="ascii",
    )
    if args.frames_written:
        col, frame = divmod(args.frames_written - 1, FRAMES)
        end = len(HEADER) + args.frames_written * RECORD_BYTES
        print(f"Snapshot through column {col}, frame {frame}; last word bytes {end-4}..{end-1}")


if __name__ == "__main__":
    main()
