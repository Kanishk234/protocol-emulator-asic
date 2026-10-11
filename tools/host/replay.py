"""Plan relative event replay windows from a loss-free timestamp capture.

This produces a schedule specification, not a pin waveform or hardware driver.
Timestamp capture records event times, not event values or absolute time.
"""
import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Sequence

from .capture import _integer, decode_capture


@dataclass(frozen=True)
class ReplayEvent:
    observed_index: int
    timestamp: int
    earliest_clock: int
    latest_clock: int


def plan_replay(samples: Sequence[int], *, max_gap_clocks: int,
                stamp_bits: int = 6, stamp_shift: int = 0,
                overflow: bool = False, start_event: int = 0,
                event_count: int | None = None) -> list[ReplayEvent]:
    """Return relative timing windows, preserving original event indices.

    Validate the entire trace before selecting a window: trimming cannot hide
    loss or ambiguous wraps. Each output time is relative to the first selected
    event. Windows share counter phase and are correlated; selecting arbitrary
    independent times inside them is not a certified replay. No edge polarity,
    payload, pin latency, throughput or absolute clock frequency is inferred.
    """
    samples = list(samples)
    intervals = decode_capture(samples, stamp_bits=stamp_bits,
        stamp_shift=stamp_shift, max_gap_clocks=max_gap_clocks, overflow=overflow)
    _integer(start_event, "start_event", 0, max(0, len(samples) - 1))
    if event_count is not None:
        _integer(event_count, "event_count", 1, max(1, len(samples)))
        if start_event + event_count > len(samples):
            raise ValueError("selected events extend beyond the capture")
    stop = len(samples) if event_count is None else start_event + event_count
    if start_event != 0 or stop != len(samples):
        # Check cumulative contradictions outside the requested replay slice
        # as well; a convenient trigger must not hide an invalid session.
        plan_replay(samples, max_gap_clocks=max_gap_clocks,
            stamp_bits=stamp_bits, stamp_shift=stamp_shift, overflow=overflow)
    selected = samples[start_event:stop]
    if not selected:
        return []
    result = [ReplayEvent(start_event, selected[0], 0, 0)]
    ticks = minimum = maximum = 0
    quantum = 1 << stamp_shift
    for index in range(start_event + 1, stop):
        interval = intervals[index - 1]
        ticks += interval.delta_ticks
        minimum += interval.minimum_clocks
        maximum += interval.maximum_clocks
        # Total phase uncertainty remains q-1, rather than growing once per
        # event. The independent gap bounds may tighten it further.
        earliest = max(minimum, ticks * quantum - (quantum - 1), 0)
        latest = min(maximum, ticks * quantum + (quantum - 1))
        if earliest > latest:
            raise ValueError("trace has no consistent cumulative timing window")
        result.append(ReplayEvent(index, samples[index], earliest, latest))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON array of capture bytes only")
    parser.add_argument("--max-gap-clocks", type=int, required=True)
    parser.add_argument("--stamp-bits", type=int, default=6)
    parser.add_argument("--stamp-shift", type=int, default=0)
    parser.add_argument("--overflow", action="store_true")
    parser.add_argument("--start-event", type=int, default=0)
    parser.add_argument("--event-count", type=int)
    args = parser.parse_args()
    try:
        samples = json.loads(args.input.read_text())
        if not isinstance(samples, list):
            raise ValueError("input must be a JSON array")
        events = plan_replay(samples, max_gap_clocks=args.max_gap_clocks,
            stamp_bits=args.stamp_bits, stamp_shift=args.stamp_shift,
            overflow=args.overflow, start_event=args.start_event,
            event_count=args.event_count)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps({"scope": "relative_observed_event_windows_only",
        "assumed_max_gap_clocks": args.max_gap_clocks,
        "stamp_bits": args.stamp_bits, "stamp_shift": args.stamp_shift,
        "windows_correlated": True, "event_values_known": False,
        "events": [asdict(event) for event in events]}, indent=2))


if __name__ == "__main__":
    main()
