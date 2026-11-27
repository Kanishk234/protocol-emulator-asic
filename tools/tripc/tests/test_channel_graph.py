import pytest

import tripc


def test_blocking_feedback_and_tap():
    source = """program feedback
connect L0.I0 <- L1.O1
connect L1.I0 <- L0.O1
"""
    _, blocking = tripc.compile_text(source)
    _, tap = tripc.compile_text(source.replace('L0.O1', 'L0.O1 tap'))
    assert 'Potential blocking feedback among L0, L1.' in blocking
    assert 'No blocking feedback found' in tap
    assert 'no deadlock or rate certificate' in tap


def test_final_binding_replaces_prior_blocking_edge():
    source = """program rewired
connect L0.I0 <- L1.O1
connect L1.I0 <- L0.O1
connect L1.I0 <- HOST_IN
"""
    _, report = tripc.compile_text(source)
    assert 'No blocking feedback found' in report
    assert 'Potential blocking feedback' not in report


def test_data_predicates_leave_service_unclassified():
    source = """program guarded
connect L0.I0 <- HOST_IN
connect HOST_OUT <- L0.O0
lane L0:
    slot urgent: when I0 is DATA do MOV O0 <- I0, deq
"""
    _, guarded = tripc.compile_text(source)
    _, unconditional = tripc.compile_text(source.replace('when I0 is DATA ', ''))
    assert 'non-forwarding slots: L0.' in guarded
    assert 'Service is unclassified' not in unconditional


def test_closed_forwarding_ring_cannot_start_empty():
    from tripsim import Chip

    source = """program closed
connect L0.I0 <- L1.O1
connect L1.I0 <- L0.O1
lane L0:
    slot urgent: do MOV O1 <- I0, deq
lane L1:
    slot urgent: do MOV O1 <- I0, deq
"""
    image, report = tripc.compile_text(source)
    assert 'No forwarding can start from empty channels in L0, L1' in report
    assert 'A fully occupied forwarding ring in L0, L1 cannot advance' in report
    chip = Chip(fire_period=1)
    tripc.load(chip, image)
    chip.host_push(1)
    chip.run_for(32)
    assert [lane.stats['fired'][0] for lane in chip.lanes] == [0, 0]

    # Exercise the assumption with a manually seeded channel in the model.
    # A host cannot inject this token through the ring's compiled bindings.
    chip.fabric.producers['L0.O1'].load(0, 1)
    chip.fabric.commit()
    chip.run_for(32)
    assert all(lane.stats['fired'][0] > 0 for lane in chip.lanes)

    full = Chip(fire_period=1)
    tripc.load(full, image)
    for lane in ('L0', 'L1'):
        full.fabric.producers[f'{lane}.O1'].load(0, 1)
    full.fabric.commit()
    full.run_for(32)
    assert [lane.stats['fired'][0] for lane in full.lanes] == [0, 0]
    assert all(not full.fabric.producers[f'{lane}.O1'].free() for lane in ('L0', 'L1'))

    _, rewired = tripc.compile_text(source.replace('L0.I0 <- L1.O1', 'L0.I0 <- HOST_IN'))
    assert 'No forwarding can start' not in rewired
    assert 'fully occupied forwarding ring' not in rewired


def test_accepted_tag_without_dequeuer_holds_producer():
    from tripsim import Chip
    from tripwire_spec import TAGS

    source = """program guarded
connect L0.I0 <- HOST_IN
connect HOST_OUT <- L0.O0
lane L0:
    slot urgent: when I0 is DATA do MOV O0 <- I0, deq
"""
    image, report = tripc.compile_text(source)
    warnings = [line for line in report.splitlines() if 'L0.I0 blocks its producer' in line]
    assert any('EVENT' in line for line in warnings)
    assert all('DATA' not in line for line in warnings)
    no_warning = [
        source.replace('HOST_IN', 'HOST_IN accept=DATA'),
        source.replace('HOST_IN', 'HOST_IN tap'),
        source + '    slot urgent: do MOV none <- I0, deq\n',
    ]
    for variant in no_warning:
        assert 'L0.I0 blocks its producer' not in tripc.compile_text(variant)[1]

    chip = Chip(fire_period=1)
    tripc.load(chip, image)
    producer = chip.fabric.producers['HOST_IN']
    producer.load(TAGS['EVENT'], 1)
    chip.fabric.commit()
    chip.run_for(16)
    assert not producer.free()

    filtered, _ = tripc.compile_text(no_warning[0])
    chip = Chip(fire_period=1)
    tripc.load(chip, filtered)
    producer = chip.fabric.producers['HOST_IN']
    producer.load(TAGS['EVENT'], 1)
    chip.fabric.commit()
    chip.run_for(16)
    assert producer.free()


def test_accepted_tag_warning_uses_compiled_producer_output():
    source = """program upstream
connect L0.I0 <- HOST_IN
connect L1.I0 <- L0.O1
lane L0:
    slot urgent: do MOV O1 <- I0, deq, tag DATA
    slot: do MOV O0 <- zero, tag EVENT
lane L1:
    slot urgent: when I0 is DATA do MOV none <- I0, deq
"""
    assert 'L1.I0 blocks its producer' not in tripc.compile_text(source)[1]
    for variant in (
        source.replace('deq, tag DATA', 'deq, tag EVENT'),
        source.replace('deq, tag DATA', 'deq, keep'),
    ):
        assert 'L1.I0 blocks its producer' in tripc.compile_text(variant)[1]
    guarded_keep = source.replace('do MOV O1 <- I0, deq, tag DATA',
                                  'when I0 is DATA do MOV O1 <- I0, deq, keep')
    assert 'L1.I0 blocks its producer' not in tripc.compile_text(guarded_keep)[1]
    control = source.replace('MOV O1 <- I0', 'MKCTL O1 <- I0')
    warning = next(line for line in tripc.compile_text(control)[1].splitlines()
                   if 'L1.I0 blocks its producer' in line)
    assert 'CTRL' in warning


def test_dequeue_guard_requires_reachable_state():
    from tripsim import Chip
    from tripwire_spec import TAGS

    source = """program guarded_state
connect L0.I0 <- HOST_IN accept=DATA
lane L0:
    states IDLE ACTIVE
    slot urgent: when ACTIVE do MOV none <- I0, deq
"""
    image, report = tripc.compile_text(source)
    assert 'STATE unreachable from reset' in report
    enabled = source + '    slot: when IDLE do MOV none <- zero then ACTIVE\n'
    enabled_image, report = tripc.compile_text(enabled)
    assert 'STATE unreachable from reset' not in report
    for candidate, releases in [(image, False), (enabled_image, True)]:
        chip = Chip(fire_period=1)
        tripc.load(chip, candidate)
        producer = chip.fabric.producers['HOST_IN']
        producer.load(TAGS['DATA'], 1)
        chip.fabric.commit()
        chip.run_for(16)
        assert producer.free() == releases


def test_held_tag_prevents_transition_to_dequeue_state():
    from tripsim import Chip
    from tripwire_spec import TAGS

    source = """program blocked_transition
connect L0.I0 <- HOST_IN accept=DATA|EVENT
lane L0:
    states IDLE ACTIVE
    slot urgent: when ACTIVE, I0 is DATA do MOV none <- I0, deq
    slot urgent: when IDLE, I0 is EVENT do MOV none <- I0, deq then ACTIVE
"""
    image, report = tripc.compile_text(source)
    assert 'held tag rules out the transitions' in report
    for tags in [['DATA'], ['EVENT', 'DATA']]:
        chip = Chip(fire_period=1)
        tripc.load(chip, image)
        producer = chip.fabric.producers['HOST_IN']
        for tag in tags:
            producer.load(TAGS[tag], 1)
            chip.fabric.commit()
            chip.run_for(16)
        assert producer.free() == (tags[0] == 'EVENT')


@pytest.mark.parametrize('forwarded', [False, True], ids=['direct', 'two-lane'])
def test_random_stateful_stall_warnings_match_model(forwarded):
    import random

    from tripc.channel_graph import undrainable_tags
    from tripsim import Chip
    from tripwire_spec import TAGS

    rng = random.Random(0x51A11)
    stalls = 0
    lane = 'L1' if forwarded else 'L0'
    upstream = 'L0.O1' if forwarded else 'HOST_IN'
    forwarding = [
        'connect L0.I0 <- HOST_IN',
        'lane L0:',
        '    slot urgent: do MOV O1 <- I0, deq, keep',
    ] if forwarded else []
    for _ in range(1000):
        tag = rng.choice(list(TAGS))
        states = [f'S{index}' for index in range(rng.randint(2, 6))]
        slots = []
        for state, target in zip(states, states[1:]):
            guard_tag = rng.choice([None, tag, rng.choice(list(TAGS))])
            guard = f', I0 is {guard_tag}' if guard_tag else ''
            operand = 'I0' if guard_tag else 'zero'
            slots.append(f'    slot: when {state}{guard} do MOV none <- {operand} then {target}')
        slots.append(f'    slot: when {states[-1]}, I0 is {tag} do MOV none <- I0, deq')
        source = '\n'.join([
            'program randomized_state',
            *forwarding,
            f'connect {lane}.I0 <- {upstream} accept={tag}',
            f'lane {lane}:',
            '    states ' + ' '.join(states),
            *slots,
        ])
        image, _ = tripc.compile_text(source)
        cadence = rng.choice([1, 2])
        chip = Chip(fire_period=cadence)
        tripc.load(chip, image)
        host = chip.fabric.producers['HOST_IN']
        host.load(TAGS[tag], rng.randrange(65536))
        chip.fabric.commit()
        chip.run_for((len(states) + 4) * cadence)
        producer = chip.fabric.producers[upstream]
        assert producer.loads == 1, source
        stalled = not producer.free()
        stalls += stalled
        flagged = any(port == f'{lane}.I0' and blocked_tag == tag
                      for port, blocked_tag, _ in undrainable_tags(image))
        assert flagged == stalled, source
    assert 0 < stalls < 1000


def test_upstream_lane_can_trigger_or_avoid_held_tag_stall():
    from tripc.channel_graph import undrainable_tags
    from tripsim import Chip
    from tripwire_spec import TAGS

    source = """program cross_lane
connect L0.I0 <- HOST_IN accept=DATA|EVENT
connect L1.I0 <- L0.O1 accept=DATA|EVENT
lane L0:
    slot urgent: do MOV O1 <- I0, deq, keep
lane L1:
    states IDLE ACTIVE
    slot urgent: when ACTIVE, I0 is DATA do MOV none <- I0, deq
    slot urgent: when IDLE, I0 is EVENT do MOV none <- I0, deq then ACTIVE
"""
    image, _ = tripc.compile_text(source)
    assert ('L1.I0', 'DATA', 'held') in list(undrainable_tags(image))
    for fire_period in (1, 2):
        for tags, stalled in ((('DATA',), True), (('EVENT', 'DATA'), False)):
            chip = Chip(fire_period=fire_period)
            tripc.load(chip, image)
            host = chip.fabric.producers['HOST_IN']
            peer = chip.fabric.producers['L0.O1']
            for tag in tags:
                host.load(TAGS[tag], 1)
                chip.fabric.commit()
                chip.run_for(16)
            assert host.free()
            assert peer.free() == (not stalled)
            # The next arrival can occupy HOST_IN but cannot be forwarded
            # if the peer is still holding L0's first output.
            host.load(TAGS['DATA'], 2)
            chip.fabric.commit()
            chip.run_for(16)
            assert host.free() == (not stalled)
        for period in (8, 11, 16):
            for first_tag in ('DATA', 'EVENT'):
                chip = Chip(fire_period=fire_period)
                tripc.load(chip, image)
                host = chip.fabric.producers['HOST_IN']
                first_overrun = None
                for clock in range(8 * period):
                    if clock % period == 0:
                        if not host.free():
                            first_overrun = clock
                            break
                        tag = first_tag if clock == 0 else 'DATA'
                        host.load(TAGS[tag], clock)
                    chip.step()
                # The stalled peer holds arrival one and HOST_IN holds arrival two.
                assert first_overrun == (2 * period if first_tag == 'DATA' else None)


def test_routine_state_transition_preserves_possible_dequeue():
    from tripc.channel_graph import undrainable_tags
    from tripsim import Chip
    from tripwire_spec import TAGS

    source = """program routine_unlock
connect L0.I0 <- HOST_IN accept=DATA
lane L0:
    states IDLE ACTIVE
    slot urgent: when ACTIVE do MOV none <- I0, deq
    slot: when IDLE do CALL unlock
routine unlock:
    setst ACTIVE
    ret
"""
    image, _ = tripc.compile_text(source)
    assert list(undrainable_tags(image)) == []
    for cadence in (1, 2):
        chip = Chip(fire_period=cadence)
        tripc.load(chip, image)
        producer = chip.fabric.producers['HOST_IN']
        producer.load(TAGS['DATA'], 1)
        chip.fabric.commit()
        chip.run_for(64)
        assert producer.free()
