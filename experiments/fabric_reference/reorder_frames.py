"""Reorder complete frame records without changing their address or payload.

Experimental loading-order screen for the pinned reference fabric only.
Successful final-image equivalence does not establish safe transitions.
"""

import argparse
import hashlib
import json
from pathlib import Path

from frame_snapshot import COLS, FRAMES, HEADER, RECORD_BYTES, decode

ORDERS = ("reverse", "reverse-frames", "reverse-columns", "frame-major")


def permutation(order: str) -> list[int]:
    if order == "reverse":
        return list(reversed(range(COLS * FRAMES)))
    if order == "reverse-frames":
        return [col * FRAMES + frame for col in range(COLS) for frame in reversed(range(FRAMES))]
    if order == "reverse-columns":
        return [col * FRAMES + frame for col in reversed(range(COLS)) for frame in range(FRAMES)]
    if order == "frame-major":
        return [col * FRAMES + frame for frame in range(FRAMES) for col in range(COLS)]
    raise ValueError(f"Unknown ordering: {order}")


def reorder(data: bytes, order: str) -> bytes:
    decode(data)  # Reject malformed or already-reordered inputs.
    indices = permutation(order)
    if sorted(indices) != list(range(COLS * FRAMES)):
        raise ValueError("Order must include each frame exactly once")
    records = [data[len(HEADER) + i * RECORD_BYTES : len(HEADER) + (i + 1) * RECORD_BYTES] for i in indices]
    return HEADER + b"".join(records) + data[-4:]


def clear_columns() -> bytes:
    """Write zero to all 20 frames at once, one column at a time.

    Uses the stock loader's multi-bit FrameStrobe mask. Unlike the prior-art
    direct-fabric helper, this does not assert all columns simultaneously.
    """
    records = [((col << 27) | ((1 << FRAMES) - 1)).to_bytes(4, "big") + bytes(RECORD_BYTES - 4)
               for col in reversed(range(COLS))]
    return HEADER + b"".join(records) + bytes.fromhex("00100000")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("order", choices=(*ORDERS, "clear-columns"))
    args = parser.parse_args()
    original = args.input.read_bytes()
    decode(original)
    clearing = args.order == "clear-columns"
    result = clear_columns() if clearing else reorder(original, args.order)
    args.output.write_bytes(result)
    args.output.with_suffix(".hex").write_text(
        "".join(f"{byte:02x}\n" for byte in result.ljust(16384, b"\x00")), encoding="ascii"
    )
    manifest = {
        "order": args.order,
        "input_sha256": hashlib.sha256(original).hexdigest(),
        "output_sha256": hashlib.sha256(result).hexdigest(),
        "record_count": COLS if clearing else COLS * FRAMES,
        "records": [
            {"offset": len(HEADER) + n * RECORD_BYTES, "column": i // FRAMES, "frame": i % FRAMES}
            for n, i in enumerate(permutation(args.order))
        ] if not clearing else [
            {"offset": len(HEADER) + n * RECORD_BYTES, "column": col, "frame_mask": (1 << FRAMES) - 1}
            for n, col in enumerate(reversed(range(COLS)))
        ],
    }
    args.output.with_suffix(".json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    action = "all-frame zero writes, columns descending" if clearing else "all addressed payloads preserved"
    print(f"{args.order}: {len(result)} bytes; {action}")


if __name__ == "__main__":
    main()
