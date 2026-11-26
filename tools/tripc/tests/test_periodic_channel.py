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


@pytest.mark.parametrize('binding,other,error', [
    ('tap', '', 'unfiltered blocking consumer'),
    ('accept=DATA', '', 'unfiltered blocking consumer'),
    ('', 'connect L1.I0 <- HOST_IN', 'more than one blocking consumer'),
])
def test_compiled_binding_rejections(binding, other, error):
    import tripc
    from tripc.periodic_channel import analyze_compiled_channel

    image, _ = tripc.compile_text(f'program binding\nconnect L0.I0 <- HOST_IN {binding}\n{other}')
    with pytest.raises(ValueError, match=error):
        analyze_compiled_channel(image, {'consumer': 'L0.I0', 'arrival_period': 3, 'service_period': 3})


@pytest.mark.parametrize('phase,exit_code,result', [(1, 0, 'no_overrun'), (0, 2, 'overrun')])
def test_channel_schedule_cli(tmp_path, monkeypatch, capsys, phase, exit_code, result):
    import json
    import sys

    from tripc.__main__ import main

    program = tmp_path / 'pipe.trw'
    program.write_text('program pipe\nconnect L0.I0 <- HOST_IN\nconnect L1.I0 <- HOST_IN tap\n')
    schedule = tmp_path / 'schedule.json'
    schedule.write_text(json.dumps({
        'consumer': 'L0.I0', 'arrival_period': 3, 'service_period': 3, 'service_phase': phase,
    }))
    monkeypatch.setattr(sys, 'argv', ['tripc', str(program), '--channel-schedule', str(schedule)])
    assert main() == exit_code
    output = capsys.readouterr().out
    assert 'Declared channel schedule' in output
    assert f'"status": "{result}"' in output
    assert '"producer": "HOST_IN"' in output
