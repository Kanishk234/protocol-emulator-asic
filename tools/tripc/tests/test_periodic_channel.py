import pytest

from tripc.periodic_channel import analyze_periodic_channel


@pytest.mark.parametrize('arrival_phase,service_phase,expected', [
    (0, 1, {'status': 'no_overrun', 'clocks_checked': 3}),
    (1, 0, {'status': 'no_overrun', 'clocks_checked': 6}),
    (0, 0, {'status': 'overrun', 'clock': 3}),
])
def test_phase_alignment_at_equal_token_rates(arrival_phase, service_phase, expected):
    assert analyze_periodic_channel(
        3, 3, arrival_phase=arrival_phase, service_phase=service_phase
    ) == expected


def test_faster_producer_eventually_overruns():
    assert analyze_periodic_channel(2, 3, service_phase=1) == {
        'status': 'overrun', 'clock': 4,
    }


def test_uncertified_when_limit_precedes_repeat():
    assert analyze_periodic_channel(101, 103, max_cycle=20) == {
        'status': 'unknown', 'clocks_checked': 20,
    }


@pytest.mark.parametrize('period,phase', [(0, 0), (1, 1), (2, -1), (True, 0)])
def test_invalid_schedule(period, phase):
    with pytest.raises(ValueError):
        analyze_periodic_channel(period, 1, arrival_phase=phase)


def test_all_short_schedules_against_fabric():
    from itertools import product
    from math import lcm

    from tripsim.fabric import Fabric

    schedules = [(period, phase) for period in range(1, 8) for phase in range(period)]
    for (arrivals, arrival_phase), (service, service_phase) in product(schedules, repeat=2):
        fabric = Fabric()
        producer = fabric.producer('producer')
        consumer = fabric.port('consumer')
        fabric.connect('consumer', 'producer')
        first_overrun = None
        for clock in range(2 * lcm(arrivals, service)):
            if clock % arrivals == arrival_phase:
                if not producer.free():
                    first_overrun = clock
                    break
                producer.load(0, clock)
            if clock % service == service_phase and consumer.avail():
                consumer.take()
            fabric.commit()

        actual = analyze_periodic_channel(
            arrivals, service, arrival_phase=arrival_phase, service_phase=service_phase
        )
        if first_overrun is None:
            assert actual['status'] == 'no_overrun'
        else:
            assert actual == {'status': 'overrun', 'clock': first_overrun}
