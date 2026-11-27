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

    _, rewired = tripc.compile_text(source.replace('L0.I0 <- L1.O1', 'L0.I0 <- HOST_IN'))
    assert 'No forwarding can start' not in rewired
