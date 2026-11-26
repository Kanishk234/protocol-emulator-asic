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
