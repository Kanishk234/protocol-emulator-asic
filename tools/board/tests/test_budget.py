"""Service budget boundary/error tests; no measured hardware assumptions."""
import pytest
from board.budget import plan


def test_status_framing_and_channel_asymmetry():
    read = plan(8_000_000, 1_000_000, 1000)
    write = plan(8_000_000, 1_000_000, 1000, direction='write')
    assert read['service_interval_us'] == 28
    assert write['service_interval_us'] == 36
    assert read['wire_bytes_per_payload_byte'] == 3
    assert write['wire_bytes_per_payload_byte'] == 4


def test_blackout_can_overflow_even_with_low_average_rate():
    report = plan(8_000_000, 1_000_000, 1000, blackout_us=2000)
    assert report['strict_service_margin']
    assert report['required_queue_bytes'] == 4
    assert not report['queue_sufficient_under_model']


def test_exact_capacity_has_no_strict_margin():
    report = plan(8_000_000, 1_000_000, '250000/7')
    assert report['utilization'] == 1
    assert not report['strict_service_margin']


def test_zero_arrival_and_burst_boundary():
    assert plan(8_000_000, 1_000_000, 0, burst_bytes=2)['queue_sufficient_under_model']
    assert not plan(8_000_000, 1_000_000, 0, burst_bytes=3)['queue_sufficient_under_model']


@pytest.mark.parametrize('kwargs', [dict(sck_hz=1_000_001), dict(clock_hz=0),
    dict(arrival_bytes_s='nan'), dict(overhead_us=-1), dict(blackout_us=True),
    dict(queue_bytes=1.5), dict(burst_bytes=True), dict(direction='duplex')])
def test_invalid_budget_rejected(kwargs):
    values = dict(clock_hz=8_000_000, sck_hz=1_000_000, arrival_bytes_s=1000)
    values.update(kwargs)
    with pytest.raises(ValueError):
        plan(**values)
