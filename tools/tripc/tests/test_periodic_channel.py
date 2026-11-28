import pytest

import tripc
from tripc.periodic_channel import (
    analyze_compiled_channel, analyze_compiled_pipeline, analyze_periodic_channel,
)


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

    image, _ = tripc.compile_text("""program scheduled
connect L0.I0 <- HOST_IN
connect L1.I0 <- HOST_IN tap
""")
    schedules = [(period, phase) for period in range(1, 15) for phase in range(period)]
    for (arrivals, arrival_phase), (service, service_phase) in product(schedules, repeat=2):
        fabric = Fabric()
        producer = fabric.producer('HOST_IN')
        consumer = fabric.port('L0.I0')
        fabric.port('L1.I0')
        for port, source, mode, accept in image['connect']:
            fabric.connect(port, source, mode, accept)
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

        actual = analyze_compiled_channel(image, {
            'consumer': 'L0.I0', 'arrival_period': arrivals, 'arrival_phase': arrival_phase,
            'service_period': service, 'service_phase': service_phase,
        })
        assert actual.pop('producer') == 'HOST_IN'
        assert actual.pop('consumer') == 'L0.I0'
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


def test_two_stage_pipeline_against_compiled_chip():
    from itertools import product
    from math import lcm

    from tripsim import Chip

    image, _ = tripc.compile_text("""program scheduled
connect L0.I0 <- HOST_IN
connect HOST_OUT <- L0.O0
lane L0:
    slot urgent: do MOV O0 <- I0, deq
""")
    schedules = [(period, phase) for period in range(1, 7) for phase in range(period)]
    observed = set()
    for (arrivals, arrival_phase), (service, service_phase), cadence in product(
            schedules, schedules, (1, 2)):
        chip = Chip(fire_period=cadence)
        tripc.load(chip, image)
        source = chip.fabric.producers['HOST_IN']
        first_overrun = None
        # The reduced pipeline has three Boolean state bits at each combined
        # phase boundary. Nine periods suffice to repeat or observe an overrun.
        for clock in range(9 * lcm(arrivals, service, cadence)):
            if clock % arrivals == arrival_phase:
                if not source.free():
                    first_overrun = clock
                    break
                source.load(0, clock)
            chip.host_fifo_depth = int(clock % service == service_phase)
            chip.step()
            chip.host_out.clear()
        actual = analyze_compiled_pipeline(image, {
            'lane': 'L0', 'arrival_period': arrivals, 'service_period': service,
            'arrival_phase': arrival_phase, 'service_phase': service_phase, 'fire_period': cadence,
        })
        assert actual.pop('lane') == 'L0'
        assert actual.pop('input') == 'L0.I0'
        assert actual.pop('output') == 'L0.O0'
        observed.add(actual['status'])
        if first_overrun is None:
            assert actual['status'] == 'no_overrun'
        else:
            assert actual == {'status': 'overrun', 'clock': first_overrun}
    assert observed == {'overrun', 'no_overrun'}


@pytest.mark.parametrize('arrival,expected_exit,status', [(4, 0, 'no_overrun'), (1, 2, 'overrun')])
def test_pipeline_schedule_cli(tmp_path, monkeypatch, capsys, arrival, expected_exit, status):
    import json
    import sys

    from tripc.__main__ import main

    program = tmp_path / 'pipeline.trw'
    program.write_text("""program pipeline
connect L0.I1 <- HOST_IN
connect HOST_OUT <- L0.O1
lane L0:
    slot urgent: do MOV O1 <- I1, deq
""")
    schedule = tmp_path / 'schedule.json'
    schedule.write_text(json.dumps({'lane': 'L0', 'arrival_period': arrival, 'service_period': 1}))
    monkeypatch.setattr(sys, 'argv', ['tripc', str(program), '--pipeline-schedule', str(schedule)])
    assert main() == expected_exit
    output = capsys.readouterr().out
    assert 'Declared pipeline schedule' in output
    assert f'"status": "{status}"' in output
    assert '"input": "L0.I1"' in output
    assert '"output": "L0.O1"' in output


def test_pipeline_rejects_conditional_lane():
    image, _ = tripc.compile_text("""program guarded
connect L0.I0 <- HOST_IN
connect HOST_OUT <- L0.O0
lane L0:
    slot urgent: when I0 is DATA do MOV O0 <- I0, deq
""")
    with pytest.raises(ValueError, match='unconditional forwarding slot'):
        analyze_compiled_pipeline(image, {'lane': 'L0', 'arrival_period': 4, 'service_period': 1})


def test_two_lane_chain_against_compiled_chip():
    from itertools import product
    from math import lcm

    from tripsim import Chip

    image, _ = tripc.compile_text("""program chain
connect L0.I0 <- HOST_IN
connect L1.I0 <- L0.O1
connect HOST_OUT <- L1.O0
lane L0:
    slot urgent: do MOV O1 <- I0, deq
lane L1:
    slot urgent: do MOV O0 <- I0, deq
""")
    schedules = [(period, phase) for period in range(1, 7) for phase in range(period)]
    observed = set()
    for (arrivals, arrival_phase), (service, service_phase), cadence in product(
            schedules, schedules, (1, 2)):
        actual = analyze_compiled_pipeline(image, {
            'lanes': ['L0', 'L1'], 'arrival_period': arrivals, 'service_period': service,
            'arrival_phase': arrival_phase, 'service_phase': service_phase, 'fire_period': cadence,
        })
        assert actual.pop('lanes') == ['L0', 'L1']
        assert actual.pop('inputs') == ['L0.I0', 'L1.I0']
        assert actual.pop('outputs') == ['L0.O1', 'L1.O0']
        chip = Chip(fire_period=cadence)
        tripc.load(chip, image)
        source = chip.fabric.producers['HOST_IN']
        first_overrun = None
        # Five Boolean state bits bound the number of distinct boundary states.
        for clock in range(33 * lcm(arrivals, service, cadence)):
            if clock % arrivals == arrival_phase:
                if not source.free():
                    first_overrun = clock
                    break
                source.load(0, clock)
            chip.host_fifo_depth = int(clock % service == service_phase)
            chip.step()
            chip.host_out.clear()
        observed.add(actual['status'])
        if first_overrun is None:
            assert actual['status'] == 'no_overrun'
        else:
            assert actual == {'status': 'overrun', 'clock': first_overrun}
    assert observed == {'overrun', 'no_overrun'}
    with pytest.raises(ValueError, match='HOST_IN to lane'):
        analyze_compiled_pipeline(image, {
            'lanes': ['L1', 'L0'], 'arrival_period': 4, 'service_period': 1,
        })


def test_filtered_schedule_against_fabric():
    from itertools import product
    from math import lcm

    from tripsim.fabric import Fabric

    image, _ = tripc.compile_text(
        'program filtered\nconnect L0.I0 <- HOST_IN accept=DATA\n'
    )
    port, source, mode, accept = image['connect'][0]
    for arrivals, service, tags in product(range(1, 5), range(1, 5), product(range(4), repeat=2)):
        for arrival_phase, service_phase in product(range(arrivals), range(service)):
            schedule = {
                'consumer': port, 'arrival_period': arrivals, 'service_period': service,
                'arrival_phase': arrival_phase, 'service_phase': service_phase,
                'arrival_tags': list(tags),
            }
            result = analyze_compiled_channel(image, schedule)
            assert result['status'] in ('no_overrun', 'overrun')
            fabric = Fabric()
            producer = fabric.producer(source)
            consumer = fabric.port(port)
            fabric.connect(port, source, mode, accept)
            first_overrun = None
            stop = (result['clock'] + 1 if result['status'] == 'overrun'
                    else result['clocks_checked'] + lcm(arrivals * len(tags), service))
            for clock in range(stop):
                if clock % arrivals == arrival_phase:
                    if not producer.free():
                        first_overrun = clock
                        break
                    producer.load(tags[(clock - arrival_phase) // arrivals % len(tags)], clock)
                if clock % service == service_phase and consumer.avail():
                    consumer.take()
                fabric.commit()
            assert first_overrun == result.get('clock'), schedule


@pytest.mark.parametrize('tags', [[], '01', [True], [-1], [4]])
def test_invalid_arrival_tags(tags):
    with pytest.raises(ValueError, match='Arrival tags'):
        analyze_periodic_channel(2, 3, arrival_tags=tags)


def test_multicast_declared_service_matches_fabric():
    from itertools import product
    from math import lcm

    from tripsim.fabric import Fabric

    image, _ = tripc.compile_text("""program multicast
connect L0.I0 <- HOST_IN accept=DATA
connect L1.I0 <- HOST_IN accept=EVENT
connect L0.I1 <- HOST_IN tap
""")
    services = [(period, phase) for period in range(1, 5) for phase in range(period)]
    tags = [0, 2]
    for (arrivals, offset), first, second in product(services, repeat=3):
        consumers = {
            port: dict(service_period=period, service_phase=phase)
            for port, (period, phase) in zip(('L0.I0', 'L1.I0'), (first, second))
        }
        result = analyze_compiled_channel(image, dict(
            consumers=consumers, arrival_period=arrivals, arrival_phase=offset, arrival_tags=tags,
        ))
        fabric = Fabric()
        producer = fabric.producer('HOST_IN')
        for port, source, mode, accept in image['connect']:
            fabric.port(port)
            fabric.connect(port, source, mode, accept)
        assert result['status'] in ('overrun', 'no_overrun')
        expected = result.get('clock')
        stop = expected + 1 if expected is not None else (
            max(row['clocks_checked'] for row in result['consumers'].values())
            + lcm(arrivals * len(tags), first[0], second[0])
        )
        observed = None
        for clock in range(stop):
            if clock % arrivals == offset:
                if not producer.free():
                    observed = clock
                    break
                producer.load(tags[clock // arrivals % len(tags)], clock)
            for port, config in consumers.items():
                sink = fabric.ports[port]
                if clock % config['service_period'] == config['service_phase'] and sink.avail():
                    sink.take()
            fabric.commit()
        assert observed == expected, (arrivals, offset, consumers, result)


def test_multicast_requires_service_for_entire_blocking_set():
    image, _ = tripc.compile_text("""program incomplete
connect L0.I0 <- HOST_IN
connect L1.I0 <- HOST_IN
""")
    with pytest.raises(ValueError, match='all blocking consumers'):
        analyze_compiled_channel(image, {
            'consumers': {'L0.I0': {'service_period': 3}},
            'arrival_period': 3,
        })


def test_multicast_cli_reports_first_overrun(tmp_path, monkeypatch, capsys):
    import json
    import sys

    from tripc.__main__ import main

    source = tmp_path / 'multicast.trw'
    source.write_text('program multicast\nconnect L0.I0 <- HOST_IN\nconnect L1.I0 <- HOST_IN\n')
    schedule = tmp_path / 'schedule.json'
    schedule.write_text(json.dumps({
        'arrival_period': 3,
        'consumers': {'L0.I0': {'service_period': 3, 'service_phase': 1},
                      'L1.I0': {'service_period': 3}},
    }))
    monkeypatch.setattr(sys, 'argv', ['tripc', str(source), '--channel-schedule', str(schedule)])
    assert main() == 2
    result = json.loads(capsys.readouterr().out.split('```json\n')[-1].split('```')[0])['result']
    assert result['producer'] == 'HOST_IN'
    assert (result['status'], result['clock']) == ('overrun', 3)
