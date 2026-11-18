"""Static predicate analysis versus ISA cases and the independent lane model."""
import random

import pytest
import tripc
import tripwire_spec as S
from kernels import PROGRAMS
from tripc.reaction import WIDTHS, analyze_lane, overlap_witness, readiness
from tripsim import isa
from tripsim.lane import Lane


def word(**fields):
    fields.setdefault('V', 1)
    fields.setdefault('U', 1)
    fields.setdefault('DST', S.DST['none'])
    fields.setdefault('ASRC', S.ASRC['zero'])
    return sum(value << S.SLOT_FIELDS[name][0] for name, value in fields.items())


@pytest.mark.parametrize('first,second,overlap', [
    (word(SE=1, SV=1), word(SE=1, SV=2), False),
    (word(SE=1, SV=1), word(), True),
    (word(FM=3, FV=1), word(FM=1, FV=0), False),
    (word(FM=1, FV=1), word(FM=2, FV=2), True),
    (word(ASRC=4, TE=1, TAG=0), word(ASRC=4, TE=1, TAG=2), False),
    (word(ASRC=4, TE=1, TAG=0), word(ASRC=5, TE=1, TAG=2), True),
    (word(ASRC=4, HE=1, HV=0), word(ASRC=4, HE=1, HV=1), False),
    (word(ASRC=4, HE=1, HV=0), word(ASRC=4, HE=1, HS=1, HV=1), True),
    # Head/tag checks are ignored for register operands, even in raw encodings.
    (word(ASRC=0, TE=1, TAG=0), word(ASRC=0, TE=1, TAG=2), True),
    (word(OP=S.OPS['CALL']), word(FM=8, FV=8), False),
    (word(V=0), word(), False),
])
def test_predicate_intersection(first, second, overlap):
    assert (overlap_witness(first, second) is not None) == overlap


def test_call_ignores_encoded_output_and_rejects_busy_routine():
    call = word(OP=S.OPS['CALL'], DST=S.DST['O0'])
    assert readiness(call, {'o0_free': (1, 0)}) is not None
    assert readiness(call, {'flags': (8, 8)}) is None
    assert readiness(word(OP=S.OPS['CALL'], FM=8, FV=8)) is None


def test_pending_and_output_readiness_are_not_a_latency_guarantee():
    target = word(FM=1, DST=S.DST['O0'])
    assert readiness(target, {'pending': (1, 1)}) is None
    assert readiness(target, {'o0_free': (1, 0)}) is None
    assert not analyze_lane([target], {'o0_free': (1, 0)})[0]['selected_if_ready']


def test_nonurgent_competitor_wins_without_an_issuable_routine():
    result = analyze_lane([word(U=0), word()])[0]
    assert result['slot'] == 1
    assert result['competitors_no_routine'] == [0]
    assert result['competitors_with_issuable_routine'] == []
    assert not result['selected_if_ready']
    assert result['selected_if_ready_with_issuable_routine']


def test_always_ready_competitor_keeps_delay_unknown():
    # It can issue forever without consuming a token or changing its predicate.
    result = analyze_lane([word(), word()])[1]
    assert result['competitors_no_routine'] == [0]
    assert not result['selected_if_ready']
    assert not result['selected_if_ready_with_issuable_routine']


def test_memory_context_excludes_delimiter_preemption_but_not_future_arrivals():
    image, report = tripc.compile_file(PROGRAMS / 'i2c_target_eeprom_guard.trw')
    words = [int(w, 16) for w in image['lanes']['L0']['slots']]
    generic = {item['slot']: item for item in analyze_lane(words)}
    assert generic[3]['competitors_no_routine'] == [0, 1]
    data_head = {item['slot']: item for item in analyze_lane(words, {'i0_tag': (3, S.TAGS['DATA'])})}
    assert data_head[3]['selected_if_ready']
    assert 'No end-to-end pin response' in report
    assert 'L0 slot 3 | [0, 1] | [0, 1] | unknown delay' in report


def test_guard_delimiters_can_select_during_a_memory_routine():
    image, _ = tripc.compile_file(PROGRAMS / 'i2c_target_eeprom_guard.trw')
    words = [int(w, 16) for w in image['lanes']['L1']['slots']]
    context = {'flags': (8, 8)}
    results = analyze_lane(words, context)
    assert len(results) == 2
    assert all(item['selected_if_ready'] for item in results)
    # Restore the rejected prototype's explicit !RB guard: no ready-slot claim.
    fm_shift = S.SLOT_FIELDS['FM'][0]
    blocked = [w | (8 << fm_shift) for w in words]
    assert all(not item['predicate_possible'] for item in analyze_lane(blocked, context))


@pytest.mark.parametrize('context', [
    {'unknown': (1, 0)}, {'flags': (16, 0)}, {'flags': (1, 2)},
    {'state': (-1, 0)}, {'i0_tag': (3, 4)}, {'state': 1},
])
def test_invalid_context_is_rejected(context):
    with pytest.raises(ValueError):
        analyze_lane([], context)


class Input:
    def __init__(self, available, tag, data):
        self.available, self.tag, self.data = available, tag, data

    def avail(self):
        return self.available

    def head(self):
        return self.tag, self.data

    def take(self):
        pass  # A selection snapshot; no commit or token movement in this test.


class Output:
    def __init__(self, free):
        self.available = free

    def free(self):
        return self.available


def model_lane(words, values):
    ins = [Input(values[f'i{p}_avail'], values[f'i{p}_tag'], values[f'i{p}_data']) for p in (0, 1)]
    outs = [Output(values[f'o{p}_free']) for p in (0, 1)]
    lane = Lane(0, len(words), ins, outs)
    lane.slots = [isa.decode_slot(w) for w in words]
    lane.state = values['state']
    lane.flags = [values['flags'] >> bit & 1 for bit in range(3)]
    lane.rb = values['flags'] >> 3 & 1
    lane.pend = [values['pending'] >> bit & 1 for bit in range(3)]
    lane.running = True
    return lane


def test_ten_thousand_selection_snapshots_against_independent_model():
    """Cross-check predicates, witnesses and both priority modes; no liveness claim."""
    rng = random.Random(0xE7A1)
    witnessed = ready_checked = guarantees = 0
    for _ in range(10_000):
        words = [rng.getrandbits(S.SLOT_BITS) for _ in range(rng.randint(2, 12))]
        values = {name: rng.randrange(1 << width) for name, width in WIDTHS.items()}
        lane = model_lane(words, values)
        context = {name: ((1 << WIDTHS[name]) - 1, value) for name, value in values.items()}
        ready = [lane._ready(s) for s in lane.slots]
        for w, actual in zip(words, ready):
            assert (readiness(w, context) is not None) == actual
            ready_checked += 1
        witness = overlap_witness(words[0], words[1])
        if witness is not None:
            check = model_lane(words[:2], witness)
            assert all(check._ready(s) for s in check.slots)
            witnessed += 1
        results = analyze_lane(words)
        for routine in (False, True):
            lane.rir = ('ldwb', 0, 0) if routine else None
            lane.compute_eval(0)
            selected = lane._e.get('latch', {}).get('n')
            key = 'selected_if_ready_with_issuable_routine' if routine else 'selected_if_ready'
            for item in results:
                if item[key] and ready[item['slot']]:
                    assert selected == item['slot']
                    guarantees += 1
    assert ready_checked > 60_000 and witnessed > 500 and guarantees > 100
