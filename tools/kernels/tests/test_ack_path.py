"""Observe the actual whole-chip model entry premises and digital path budgets."""
from functools import lru_cache
import json

import pytest
import tripc
from kernels import PROGRAMS
from kernels.ack_path import AckPathMonitor, AckTimingController
from protomodels.i2c_memory import check_result, exercise
from tripc.linked_budget import compose_linked_response
from tripc.response import analyze_response
from tripsim import Chip


@lru_cache
def contracts(program, fire_period=1):
    image, _ = tripc.compile_file(PROGRAMS / f'{program}.trw')
    queries = json.loads((PROGRAMS / 'analysis/i2c_memory_response.json').read_text())
    responses = {name: analyze_response(image, query, fire_period=fire_period)
                 for name, query in queries.items()}
    budget = json.loads((PROGRAMS / 'analysis/i2c_memory_linked_budget.json').read_text())
    for r in responses.values():
        r['linked_budget'] = compose_linked_response(image, r, budget)
    return image, responses


def model_snapshot(chip, controller, scl, outputs, enables):
    lane, unit = chip.lanes[0], chip.pins[0]
    inp, out = lane.inp[0], lane.out[0]
    tag, data = inp.head() if inp.avail() else (0, 0)
    c = unit.cfg
    selected = c.pin_c is None or chip.synced(c.pin_c) == c.c_active
    return dict(clock=controller.clocks, scl=scl, target_low=bool(enables & 1 and not outputs & 1),
                input_available=inp.avail(), input_tag=tag, input_data=data,
                state=lane.state, flags=lane._flags4(), pending=lane._pend4(),
                exec_idle=lane.exec_latch is None,
                routine_idle=not lane.rb and lane.rir is None and lane.mem_req is None,
                outputs_free=all(lane._out_free(p) for p in (0, 1)), other_empty=not lane.inp[1].avail(),
                tx_empty=not unit.linked_bits and not unit.linked_end and not unit.actions
                and unit.wait_edge is None and unit.clk is None,
                tx_bits=len(unit.linked_bits), selected=selected and unit._sel,
                enabled=bool(unit.oe), running=lane.running,
                rx_free=unit.rx_prod.free(), rx_seq=unit.rx_prod.seq,
                out_seq=out.seq, out_valid=out.valid, out_tag=out.tag, out_data=out.data)


@pytest.mark.parametrize('program', ['i2c_target_eeprom', 'i2c_target_eeprom_guard'])
@pytest.mark.parametrize('period,high,profile', [
    (500, 250, 'standard_at_20ns'), (125, 60, 'fast_at_20ns'),
    (50, 25, 'fast_plus_at_20ns'), (50, 13, 'fast_plus_at_20ns')])
@pytest.mark.parametrize('phase', range(4))
def test_whole_workload_ack_entry_and_path(program, period, high, profile, phase):
    chip = Chip(lanes=2)
    fire_period = chip.lanes[0].fire_period
    image, responses = contracts(program, fire_period)
    tripc.load(chip, image)
    controller = AckTimingController(period, high, phase)
    expected = exercise(controller)
    monitor = AckPathMonitor(controller, responses, profile)
    for _ in range(period * 1600 + 10_000):
        _, outputs, enables = chip.outputs()
        assert not enables & outputs & 1 and not enables & 2
        scl = controller.scl
        sda = int(controller.sda and not (enables & 1 and not outputs & 1))
        snapshot = model_snapshot(chip, controller, scl, outputs, enables)
        chip.uio_in = 0xFC | scl << 1 | sda
        chip.step()
        controller.step(scl, sda)
        monitor.sample(snapshot)
        if controller.done():
            break
    check_result(controller, expected)
    records = monitor.finish()
    assert len(records) == 35
    assert all(r['rx_publish'] == 3 and r['tx_accept'] == 1 for r in records)
    if fire_period == 1:
        assert all(r['lane'] == (4 if r['role'] == 'address_ack' else 2) for r in records)
    else:
        assert all(r['lane'] in {case['response_clocks'] for case in responses[r['role']]['cases']}
                   for r in records)
    assert not any(unit.flags['OVERRUN'] for unit in chip.pins)
