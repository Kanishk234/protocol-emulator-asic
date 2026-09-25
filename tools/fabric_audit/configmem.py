"""Audit a FABulous ConfigMem CSV without importing the generator.

This counts mapped configuration bits and frame padding, NOT physical area.
The upstream bits_used_in_frame column can contain the frame width even when
the mask contains padding. Count mask ones and validate the actual bit mapping.
"""

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path


def indices(value: str) -> list[int]:
    value = re.sub(r"\s", "", value)
    if value == "NULL":
        return []
    if re.fullmatch(r"\d+:\d+", value):
        start, end = map(int, value.split(":"))
        step = 1 if start <= end else -1
        return list(range(start, end + step, step))
    if re.fullmatch(r"\d+(;\d+)*", value):
        return [int(item) for item in value.split(";")]
    raise ValueError(f"invalid ConfigBits_ranges: {value!r}")


def audit(data: str, *, frame_width: int, frames: int,
          expected_bits: int | None = None) -> dict:
    if frame_width < 1 or frames < 1:
        raise ValueError("frame width and frame count must be positive")
    if expected_bits is not None and expected_bits < 0:
        raise ValueError("expected bits must be nonnegative")
    rows = list(csv.DictReader(io.StringIO(data)))
    if len(rows) != frames:
        raise ValueError(f"expected {frames} frame rows, found {len(rows)}")
    seen_frames: set[int] = set()
    seen_bits: set[int] = set()
    counts = []
    for row in rows:
        try:
            frame = int(row["frame_index"])
            mask = row["used_bits_mask"].replace("_", "").strip()
            bit_ids = indices(row["ConfigBits_ranges"])
        except (KeyError, TypeError) as exc:
            raise ValueError("missing configuration mapping columns/values") from exc
        if frame in seen_frames or not 0 <= frame < frames:
            raise ValueError(f"duplicate or out-of-range frame index: {frame}")
        seen_frames.add(frame)
        if len(mask) != frame_width or set(mask) - {"0", "1"}:
            raise ValueError(f"frame {frame}: invalid {frame_width}-bit mask")
        if mask.count("1") != len(bit_ids):
            raise ValueError(f"frame {frame}: mask/mapping bit count mismatch")
        for bit in bit_ids:
            if bit in seen_bits:
                raise ValueError(f"configuration bit {bit} mapped more than once")
            seen_bits.add(bit)
        counts.append({"frame": frame, "mapped_bits": len(bit_ids)})
    bit_count = len(seen_bits)
    if seen_bits != set(range(bit_count)):
        raise ValueError("configuration indices must cover 0 through N-1 without holes")
    if expected_bits is not None and bit_count != expected_bits:
        raise ValueError(f"expected {expected_bits} configuration bits, found {bit_count}")
    capacity = frames * frame_width
    return {
        "frame_width": frame_width,
        "frames": frames,
        "frame_capacity_bits": capacity,
        "mapped_config_bits": bit_count,
        "padding_bits": capacity - bit_count,
        "per_frame": sorted(counts, key=lambda item: item["frame"]),
        "scope": "configuration mapping only; not physical area or bitstream size",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--frame-width", type=int, required=True)
    parser.add_argument("--frames", type=int, required=True)
    parser.add_argument("--expected-bits", type=int)
    args = parser.parse_args()
    try:
        raw = args.csv_file.read_bytes()
        result = audit(raw.decode("utf-8-sig"), frame_width=args.frame_width,
                       frames=args.frames, expected_bits=args.expected_bits)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(2, f"configuration audit failed: {exc}\n")
    result["source_sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
