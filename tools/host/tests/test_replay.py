import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from host.replay import plan_replay


def test_multiple_wraps_unwrap_relative_observed_events():
    events = plan_replay([60, 4, 40, 2], max_gap_clocks=40)
    assert [event.earliest_clock for event in events] == [0, 8, 44, 70]
    assert [event.latest_clock for event in events] == [0, 8, 44, 70]


def test_quantization_uncertainty_does_not_accumulate_per_event():
    events = plan_replay([60, 61, 62, 63, 0], stamp_shift=2, max_gap_clocks=12)
    assert (events[-1].earliest_clock, events[-1].latest_clock) == (13, 19)


def test_independent_clock_observations_are_inside_all_windows():
    # Generate clocks first; do not construct observations using the planner.
    for shift in range(4):
        quantum = 1 << shift
        for first in range(64 * quantum):
            gaps = [0, 1, quantum - 1, 13, 63 * quantum]
            clocks = [first]
            for gap in gaps:
                clocks.append(clocks[-1] + gap)
            stamps = [(clock // quantum) % 64 for clock in clocks]
            for start in (0, 2):
                events = plan_replay(stamps, stamp_shift=shift,
                    max_gap_clocks=63 * quantum, start_event=start)
                for event in events:
                    actual = clocks[event.observed_index] - clocks[start]
                    assert event.earliest_clock <= actual <= event.latest_clock


def test_selection_rebases_and_keeps_original_indices():
    events = plan_replay([50, 60, 4, 8], max_gap_clocks=20,
                         start_event=1, event_count=2)
    assert [(e.observed_index, e.earliest_clock, e.latest_clock) for e in events] == [
        (1, 0, 0), (2, 8, 8)]


@pytest.mark.parametrize("kwargs, message", [
    ({"overflow": True}, "overflow"),
    ({"max_gap_clocks": 64}, "max_gap"),
    ({"start_event": True}, "start_event"),
    ({"start_event": 2}, "start_event"),
    ({"event_count": 0}, "event_count"),
    ({"start_event": 1, "event_count": 2}, "extend"),
])
def test_loss_wrap_and_invalid_selection_rejected(kwargs, message):
    with pytest.raises(ValueError, match=message):
        plan_replay([1, 2], **({"max_gap_clocks": 10} | kwargs))


def test_trimming_does_not_hide_invalid_capture():
    with pytest.raises(ValueError, match="contradicts"):
        plan_replay([0, 32, 33], max_gap_clocks=10, start_event=1)
    # Each individual one-tick change can occur in one clock at a boundary,
    # but two consecutive four-clock tick changes cannot both do so.
    with pytest.raises(ValueError, match="cumulative"):
        plan_replay([0, 1, 2], max_gap_clocks=1, stamp_shift=2, start_event=2)
    assert plan_replay([], max_gap_clocks=10) == []
    assert plan_replay([5], max_gap_clocks=10)[0].latest_clock == 0


def test_cli_emits_scoped_windows_and_rejects_loss(tmp_path):
    trace = tmp_path / "trace.json"
    trace.write_text("[60, 4]")
    env = os.environ | {"PYTHONPATH": str(Path(__file__).resolve().parents[2])}
    command = [sys.executable, "-m", "host.replay", str(trace), "--max-gap-clocks", "20"]
    run = subprocess.run(command, env=env, capture_output=True, text=True)
    assert run.returncode == 0
    result = json.loads(run.stdout)
    assert result["events"][1]["earliest_clock"] == 8
    assert result["windows_correlated"] is True
    assert result["event_values_known"] is False
    lost = subprocess.run(command + ["--overflow"], env=env, capture_output=True, text=True)
    assert lost.returncode != 0
    assert "capture overflow" in lost.stderr
