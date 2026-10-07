import pytest

from host.capture import decode_capture


def test_wrap_is_relative_and_requires_a_short_gap():
    interval, = decode_capture([60, 4], max_gap_clocks=20)
    assert (interval.delta_ticks, interval.minimum_clocks, interval.maximum_clocks) == (8, 8, 8)
    with pytest.raises(ValueError, match="max_gap"):
        decode_capture([0, 0], max_gap_clocks=64)


def test_prescaling_covers_every_counter_phase_and_known_gap():
    # Independent clock observation: timestamps come from floor(time/quantum).
    for shift in (0, 2):
        quantum = 1 << shift
        maximum_gap = 63 * quantum
        for first in range(64 * quantum):
            for gap in (0, 1, 13, 32, maximum_gap):
                stamps = [(first // quantum) % 64, ((first + gap) // quantum) % 64]
                interval, = decode_capture(stamps, stamp_shift=shift, max_gap_clocks=maximum_gap)
                assert interval.minimum_clocks <= gap <= interval.maximum_clocks


def test_reject_loss_mixed_stream_and_contradictory_bound():
    with pytest.raises(ValueError, match="overflow"):
        decode_capture([1, 2], max_gap_clocks=10, overflow=True)
    with pytest.raises(ValueError, match="capture byte"):
        decode_capture([1, 128], max_gap_clocks=10)
    with pytest.raises(ValueError, match="contradicts"):
        decode_capture([1, 32], max_gap_clocks=10)


def test_prescaler_wrap_cannot_hide_inside_the_bound():
    # Gap253 at phase3 yields a complete64-tick wrap despite being <256 clocks.
    with pytest.raises(ValueError, match="max_gap"):
        decode_capture([0, 0], stamp_shift=2, max_gap_clocks=253)


def test_empty_and_single_sample_have_no_interval():
    assert decode_capture([], max_gap_clocks=10) == []
    assert decode_capture([63], max_gap_clocks=10) == []
