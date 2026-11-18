"""Closed response contracts, adversarial refusals and independent model checks."""
import json
import os
import random
import subprocess
import sys

import pytest
import tripc
import tripwire_spec as S
from kernels import PROGRAMS
from tripc.response import _alu, analyze_queries, analyze_response
from tripsim import isa
from tripsim.fabric import Fabric
from tripsim.lane import Lane


CONTRACTS = PROGRAMS / 'analysis' / 'i2c_memory_response.json'


def query(**changes):
    q = dict(lane='L0', state='A', input_port='I0', input_tag='DATA', input_values=[0],
             response_port='O0', response_tag='DATA', response_data=0)
    q.update(changes)
    return q


def compile_lane(body, before=''):
    return tripc.compile_text('program response_test\n' + before + '\nlane L0:\n' + body)[0]


@pytest.mark.parametrize('program', ['i2c_target_eeprom', 'i2c_target_eeprom_guard'])
def test_memory_ack_contracts(program):
    image, _ = tripc.compile_file(PROGRAMS / f'{program}.trw')
    contracts = json.loads(CONTRACTS.read_text())
    assert contracts['address_ack']['input_values'] == [0xA0, 0xA1]
    assert contracts['write_ack']['input_values'] == list(range(256))
    result = analyze_queries(image, contracts)
    assert result['address_ack']['bound_clocks'] == 4
    assert len(result['address_ack']['cases']) == 16
    assert result['write_ack']['bound_clocks'] == 2
    assert len(result['write_ack']['cases']) == 1024
    for case in result['address_ack']['cases']:
        assert [t['slot'] for t in case['trace']] == [2, None, 3]
        assert case['trace'][1]['pending'] == 1
    assert all(not r['pin_to_pin_bound'] and not r['deadlock_certificate'] for r in result.values())


def test_wrong_address_is_not_an_ack_guarantee():
    image, _ = tripc.compile_file(PROGRAMS / 'i2c_target_eeprom_guard.trw')
    q = json.loads(CONTRACTS.read_text())['address_ack']
    q['input_values'] = [0xA2]
    r = analyze_response(image, q)
    assert r['status'] == 'counterexample' and r['bound_clocks'] is None


def test_omitting_write_direction_cannot_give_a_universal_bound():
    image, _ = tripc.compile_file(PROGRAMS / 'i2c_target_eeprom_guard.trw')
    q = json.loads(CONTRACTS.read_text())['write_ack']
    q.pop('flag_mask')
    q.pop('flag_value')
    q['input_values'] = [0]
    r = analyze_response(image, q)
    assert r['status'] != 'bounded' and r['bound_clocks'] is None


@pytest.mark.parametrize('body,reason', [
    ('    states A\n    slot: when A do MOV O0 <- r0\n', 'unknown register'),
    ('    states A B\n    slot: when A do MOV none <- r0 -> f0 then B\n', 'Flag result'),
    ('    states A\n    slot: when A do MOV O0 <- time\n', 'unknown register or time'),
    ('    states A B\n    slot: when A do MOVB O1 <- zero, 0 then B\n', 'consumer-progress'),
    ('    states A\n    slot: when A do MOV none <- zero\n', 'Repeated abstract'),
    ('    states A\n', 'No ready action'),
])
def test_refuses_unsupported_progress_or_unknown_values(body, reason):
    r = analyze_response(compile_lane(body), query())
    assert r['status'] != 'bounded' and r['bound_clocks'] is None
    assert reason in r['cases'][0]['reason']


def test_call_requires_another_contract():
    image, _ = tripc.compile_text('program call\nlane L0:\n    states A\n'
                                 '    slot: when A do CALL work\nroutine work:\n    ret\n')
    r = analyze_response(image, query())
    assert r['status'] == 'unknown' and 'routine/SRAM' in r['cases'][0]['reason']


def test_unknown_registers_are_not_silently_zero():
    image = compile_lane('    states A\n    slot: when A do MOV O0 <- r0\n')
    assert analyze_response(image, query())['status'] == 'unknown'
    assert analyze_response(image, query(registers={'r0': 0}))['bound_clocks'] == 2


def test_exec_reads_register_after_previous_exec_commits():
    image = compile_lane('    states A B\n'
                         '    slot: when A do MOVB r0 <- zero, 7 then B\n'
                         '    slot: when B do MOV O0 <- r0\n')
    assert analyze_response(image, query(response_data=7))['bound_clocks'] == 3


def test_eval_pending_set_wins_over_exec_clear():
    image = compile_lane('    states A B C\n'
                         '    slot: when A do MOVB none <- zero, 0 -> f0 then B\n'
                         '    slot: when B do MOVB none <- zero, 1 -> f0 then C\n'
                         '    slot: when C, f0 == 1 do MOVB O0 <- zero, 0\n'
                         '    slot: when C, f0 == 0 do MOVB O0 <- zero, 1\n')
    r = analyze_response(image, query(response_data=1))
    assert r['bound_clocks'] == 5
    assert all([t['slot'] for t in c['trace']] == [0, 1, None, 3] for c in r['cases'])


def test_input_is_latched_at_eval_and_disappears_after_dequeue():
    direct = compile_lane('    states A\n    slot: when A, I0 is DATA do MOV O0 <- I0, deq\n')
    assert analyze_response(direct, query(input_values=[23], response_data=23))['bound_clocks'] == 2
    lost = compile_lane('    states A B\n'
                        '    slot: when A, I0 is DATA do MOV none <- I0, deq then B\n'
                        '    slot: when B, I0 is DATA do MOVB O0 <- I0, 0\n')
    assert analyze_response(lost, query())['status'] == 'counterexample'


def test_time_operand_can_be_ignored_but_not_assumed_known():
    image = compile_lane('    states A\n    slot: when A do MOVB O0 <- time, 0\n')
    assert analyze_response(image, query())['bound_clocks'] == 2


def test_second_input_and_output_ports():
    image = compile_lane('    states A\n    slot: when A, I1 is DATA do MOV O1 <- I1, deq\n')
    r = analyze_response(image, query(input_port='I1', response_port='O1',
                                      input_values=[42], response_data=42))
    assert r['bound_clocks'] == 2


def test_mkctl_and_kept_tags():
    image = compile_lane('    states A\n    slot: when A, I0 is EVENT do MKCTL O0 <- I0, f=0x30, keep\n')
    r = analyze_response(image, query(input_tag='EVENT', input_values=[1],
                                      response_tag='CTRL', response_data=0x3001))
    assert r['bound_clocks'] == 2
    image = compile_lane('    states A\n    slot: when A, I0 is EVENT do MOV O0 <- I0, keep\n')
    assert analyze_response(image, query(input_tag='EVENT', response_tag='EVENT'))['bound_clocks'] == 2


def test_short_horizon_is_unknown_not_a_certificate():
    image, _ = tripc.compile_file(PROGRAMS / 'i2c_target_eeprom.trw')
    q = json.loads(CONTRACTS.read_text())['address_ack']
    q['max_clocks'] = 3
    r = analyze_response(image, q)
    assert r['status'] == 'unknown' and r['bound_clocks'] is None


@pytest.mark.parametrize('change', [
    {'lane': []}, {'lane': 'L7'}, {'state': 'missing'}, {'state': True},
    {'input_port': 'I3'}, {'input_tag': 'bad'}, {'response_data': -1},
    {'input_values': []}, {'input_values': [True]}, {'input_values': [0, 0]},
    {'flag_mask': 8}, {'flag_mask': 1, 'flag_value': 2}, {'registers': {'r4': 0}},
    {'max_clocks': 0}, {'max_clocks': 4097}, {'typo': 0},
])
def test_invalid_or_vacuous_contract_rejected(change):
    with pytest.raises(ValueError):
        analyze_response(compile_lane('    states A\n'), query(**change))


def test_known_alu_values_match_independent_model():
    rng = random.Random(0xAC4)
    for _ in range(10_000):
        op = rng.choice([v for k, v in S.OPS.items() if k != 'CALL'])
        a, b = rng.randrange(65536), rng.randrange(65536)
        imm = rng.randrange(256)
        regs = [rng.randrange(65536) for _ in range(4)]
        constants = [rng.randrange(65536) for _ in range(4)]
        got = _alu({'OP': op, 'IMM': imm}, a, b, regs, constants)
        expected = isa.alu(op, a, b, imm, regs, constants)
        assert got == (expected.d, expected.r)


def model_response(image, q, case, rng):
    fabric = Fabric()
    request = fabric.producer('request')
    inputs = [fabric.port('I0'), fabric.port('I1')]
    outputs = [fabric.producer('O0'), fabric.producer('O1')]
    fabric.connect(q['input_port'], 'request')
    request.load(S.TAGS[q['input_tag']], case['input'])
    fabric.commit()
    lane_image = image['lanes'][q['lane']]
    lane = Lane(0, len(lane_image['slots']), inputs, outputs)
    lane.slots = [isa.decode_slot(int(w, 16)) for w in lane_image['slots']]
    lane.k = list(lane_image['k'])
    lane.regs = [q['registers'].get(f'r{i}', rng.randrange(65536)) for i in range(4)]
    lane.state = q['state']
    lane.flags = [case['initial_flags'] >> i & 1 for i in range(3)]
    lane.running = True
    target = outputs[int(q['response_port'][1])]
    for clock in range(q['max_clocks'] + 1):
        if target.valid:
            return clock, target.tag, target.data
        lane.compute_exec(clock)
        lane.compute_eval(clock)
        if clock < len(case['trace']):
            assert lane._e.get('latch', {}).get('n') == case['trace'][clock]['slot']
        lane.commit()
        fabric.commit()
    return None


@pytest.mark.parametrize('program', ['i2c_target_eeprom', 'i2c_target_eeprom_guard'])
def test_all_memory_cases_match_independent_pipeline_and_fabric(program):
    rng = random.Random(0xACC)
    image, _ = tripc.compile_file(PROGRAMS / f'{program}.trw')
    results = analyze_queries(image, json.loads(CONTRACTS.read_text()))
    for r in results.values():
        for case in r['cases']:
            # Three different assignments to unspecified registers per case.
            for _ in range(3):
                assert model_response(image, r['query'], case, rng) == (
                    case['response_clocks'], S.TAGS['DATA'], 0)


def test_cli_queries_fail_closed_and_do_not_change_images(tmp_path):
    env = dict(os.environ, PYTHONPATH=str(PROGRAMS.parent / 'tools'))
    program = PROGRAMS / 'i2c_target_eeprom_guard.trw'
    command = [sys.executable, '-m', 'tripc', str(program), '--response-queries', str(CONTRACTS)]
    image = tmp_path / 'image.json'
    result = tmp_path / 'response.json'
    run = subprocess.run(command + ['-o', str(image), '--response-results', str(result)],
                         capture_output=True, text=True, env=env)
    assert run.returncode == 0, run.stderr
    assert json.loads(image.read_text()) == tripc.compile_file(program)[0]
    assert '| address_ack | bounded | 16 | 4 |' in run.stdout
    assert 'values 0xa0..0xa1' in run.stdout and 'FLAGS & 0x2 = 0x2' in run.stdout
    assert 'values 0x0..0xff' in run.stdout
    assert json.loads(result.read_text())['write_ack']['bound_clocks'] == 2
    wrong = subprocess.run(command + ['-p', 'ADDR=0x2A'], capture_output=True, text=True, env=env)
    assert wrong.returncode == 2 and 'counterexample' in wrong.stdout
    bad = tmp_path / 'bad.json'
    bad.write_text('{')
    run = subprocess.run(command[:-1] + [str(bad)], capture_output=True, text=True, env=env)
    assert run.returncode == 2 and 'response query' in run.stderr
