"""Decode the documented UART capture stream without inventing absolute time.

Input is capture bytes only, after draining the shell's previous stream. The
caller supplies a known upper bound between captured events, measured in chip
clocks. There is no wrap counter in the image; absent that bound, or after
overflow, interpreting modular differences as event intervals is unsafe.
"""
import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class CaptureInterval:
    previous: int
    current: int
    delta_ticks: int
    minimum_clocks: int
    maximum_clocks: int


def _integer(value, name, minimum, maximum):
    if not isinstance(value, int) or isinstance(value, bool) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in {minimum}..{maximum}")


def decode_capture(samples: Sequence[int], *, stamp_bits: int = 6,
                   stamp_shift: int = 0, max_gap_clocks: int,
                   overflow: bool = False) -> list[CaptureInterval]:
    """Bound intervals between *observed* events; not pin-arrival timestamps.

    A prescaled timestamp difference d represents d*q +/- (q-1) clocks.
    Require max_gap <= wrap-q so even the prescaler phase cannot conceal a
    complete timestamp wrap. The bound is an external assumption, not something
    this byte stream can verify. Overflow means missing events and is rejected.
    """
    _integer(stamp_bits, "stamp_bits", 1, 8)
    _integer(stamp_shift, "stamp_shift", 0, 31)
    modulus, quantum = 1 << stamp_bits, 1 << stamp_shift
    _integer(max_gap_clocks, "max_gap_clocks", 0, (modulus - 1) * quantum)
    if not isinstance(overflow, bool):
        raise ValueError("overflow must be a boolean")
    if overflow:
        raise ValueError("capture overflow: event intervals cannot describe a complete trace")
    for sample in samples:
        _integer(sample, "capture byte", 0, modulus - 1)
    intervals = []
    for previous, current in zip(samples, samples[1:]):
        delta = (current - previous) % modulus
        minimum = max(0, delta * quantum - (quantum - 1))
        maximum = min(max_gap_clocks, delta * quantum + (quantum - 1))
        if minimum > maximum:
            raise ValueError("capture interval contradicts the supplied maximum gap")
        intervals.append(CaptureInterval(previous, current, delta, minimum, maximum))
    return intervals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON array of capture bytes only")
    parser.add_argument("--stamp-bits", type=int, default=6)
    parser.add_argument("--stamp-shift", type=int, default=0)
    parser.add_argument("--max-gap-clocks", type=int, required=True)
    parser.add_argument("--overflow", action="store_true", help="sticky capture overflow observed")
    args = parser.parse_args()
    try:
        samples = json.loads(args.input.read_text())
        if not isinstance(samples, list):
            raise ValueError("input must be a JSON array")
        intervals = decode_capture(samples, stamp_bits=args.stamp_bits,
            stamp_shift=args.stamp_shift, max_gap_clocks=args.max_gap_clocks,
            overflow=args.overflow)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps({"stamp_bits": args.stamp_bits, "stamp_shift": args.stamp_shift,
        "assumed_max_gap_clocks": args.max_gap_clocks, "overflow": args.overflow,
        "scope": "observed_event_intervals_no_absolute_time_or_pin_latency_claim",
        "intervals": [asdict(interval) for interval in intervals]}, indent=2))


if __name__ == "__main__":
    main()
