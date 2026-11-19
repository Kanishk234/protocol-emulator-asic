"""Encoded service envelope checked against the independent SRAM/lane model."""
import pytest
import tripc
import tripwire_spec as S
from kernels import PROGRAMS
from tripc.service import routine_service
from tripsim import Chip, isa


STATES = {'refresh': 'M_REFRESH', 'store_byte': 'M_STORE', 'advance_read': 'M_ADVANCE'}


def service_trace(image, routine, phase, pointer, starve=False):
    chip = Chip(lanes=2)
    tripc.load(chip, image, run=False)
    lane = chip.lanes[1]
    lane.state = image['lanes']['L1']['states'][STATES[routine]]
    lane.regs[0] = pointer
    lane.regs[3] = pointer ^ 0xA5
    chip.cycle = phase
    chip.run([1])
    start = chip.cycle
    chip.step()
    assert lane.rb, 'CALL must actually start the routine'
    if starve:
        # A real always-ready urgent reflex: the excluded environment can
        # starve an issuable routine, even though it makes no output writes.
        hostile, _ = tripc.compile_text('program hostile\nlane L0:\n'
                                      '    slot urgent: do MOV none <- zero\n')
        lane.slots[0] = isa.decode_slot(int(hostile['lanes']['L0']['slots'][0], 16))
    limit = routine_service(image, routine)['bound_clocks']
    for _ in range(limit + 1):
        chip.step()
        if not lane.rb:
            assert lane.rir is None and lane.mem_req is None
            return chip.cycle - start, lane.stats['routine_steps']
    return None, lane.stats['routine_steps']


@pytest.mark.parametrize('program', ['i2c_target_eeprom', 'i2c_target_eeprom_guard'])
@pytest.mark.parametrize('routine', list(STATES))
@pytest.mark.parametrize('phase', range(4))
def test_memory_service_all_pointer_values_and_rotation_offsets(program, routine, phase):
    image, _ = tripc.compile_file(PROGRAMS / f'{program}.trw')
    result = routine_service(image, routine)
    assert result['status'] == 'conditional_bound'
    assert not result['arrival_invariants_proven']
    assert result['sram_accesses'] == (1 + result['instruction_fetches']
                                       + result['data_reads'] + result['data_writes'])
    for pointer in range(256):
        elapsed, steps = service_trace(image, routine, phase, pointer)
        assert elapsed is not None and elapsed <= result['bound_clocks']
        assert steps == image['routines'][routine]['max_steps']


def tiny(body):
    return tripc.compile_text('program service\nlane L0:\n'
                             '    states A B\n'
                             '    slot: when A do CALL worker then B\n'
                             'routine worker:\n' + body)[0]


@pytest.mark.parametrize('body', [
    '    out O0, r0\n    ret\n',
    '    br end\n    end:\n    ret\n',
    '    load16 r0, 2\n    loop:\n    djnz r0, loop\n    ret\n',
    '    setst A\n    ret\n',
    '    nop\n    ret\n',
    '    ret\n    ret\n',
])
def test_refuse_unchecked_control_flow_or_progress(body):
    result = routine_service(tiny(body), 'worker')
    assert result['status'] == 'unsupported' and result['bound_clocks'] is None


def test_stores_receive_separate_rotation_accesses_and_metadata_is_not_trusted():
    image = tiny('    st r0, r1\n    ld r2, r1\n    ret\n')
    image['routines']['worker']['max_steps'] = 0
    result = routine_service(image, 'worker')
    assert result['instruction_fetches'] == 3
    assert result['data_reads'] == result['data_writes'] == 1
    assert result['sram_accesses'] == 6 and result['bound_clocks'] == 27
    assert not result['data_write_nonalias_proven']
    assert any('alias' in premise for premise in result['assumptions'])


@pytest.mark.parametrize('mutation', ['entry', 'count', 'word', 'ret', 'call'])
def test_refuse_invalid_or_nonterminal_words(mutation):
    image = tiny('    ret\n')
    start = image['sram'][0]
    if mutation == 'entry': image['sram'][0] = len(image['sram'])
    elif mutation == 'count': image['routines']['worker']['words'] = 0
    elif mutation == 'word': image['sram'][start] = 1 << S.ROUTINE_BITS
    elif mutation == 'ret': image['sram'][start] = 0
    elif mutation == 'call': image['sram'][start] = S.OPS['CALL'] << 11
    assert routine_service(image, 'worker')['status'] == 'unsupported'


def test_unlimited_urgent_traffic_is_not_a_finite_service_guarantee():
    image, _ = tripc.compile_file(PROGRAMS / 'i2c_target_eeprom_guard.trw')
    elapsed, _ = service_trace(image, 'store_byte', 0, 0, starve=True)
    assert elapsed is None


def test_unknown_routine_has_no_bound():
    image = tiny('    ret\n')
    assert routine_service(image, 'absent')['bound_clocks'] is None


def test_report_uses_access_envelope_not_old_step_only_estimate():
    image, report = tripc.compile_file(PROGRAMS / 'i2c_target_eeprom_guard.trw')
    assert '| store_byte | 9 | 10 | ≤ 51 clocks |' in report
    assert 'no selected reflex actions' in report
    assert '≤ 48 clocks' not in report
    assert routine_service(image, 'store_byte')['bound_clocks'] == 51


def test_report_does_not_turn_an_output_step_bound_into_a_service_bound():
    _, report = tripc.compile_text('program waits\nroutine worker:\n'
                                   '    out O0, r0\n    ret\n'
                                   'lane L0:\n    slot: do CALL worker\n')
    assert '| worker | 2 | 2 | unknown:' in report
