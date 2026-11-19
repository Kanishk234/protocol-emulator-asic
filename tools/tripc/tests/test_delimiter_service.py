"""Inject real multicast delimiter commands at each in-flight routine clock.

This internal harness isolates a service question: L0 is halted after loading,
and its actual O1 producer supplies the CTRLs to both U1 and L1. It is not a
pin-origin traffic proof or an alternate loaded firmware personality.
"""
from functools import lru_cache

import pytest
import tripc
import tripwire_spec as S
from kernels import PROGRAMS
from tripc.service import routine_service
from tripsim import Chip, isa


STATES = {'refresh': 'M_REFRESH', 'store_byte': 'M_STORE', 'advance_read': 'M_ADVANCE'}
BURSTS = [(0x3009,), (0x3002,), (0x3009, 0x3002), (0x3002, 0x3009)]


@lru_cache
def image():
    return tripc.compile_file(PROGRAMS / 'i2c_target_eeprom_guard.trw')[0]


def delimiter_trace(routine, phase, offset, commands, *, stall_delimiters=False):
    compiled = image()
    chip = Chip(lanes=2)
    tripc.load(chip, compiled, run=False)
    lane = chip.lanes[1]
    lane.state = compiled['lanes']['L1']['states'][STATES[routine]]
    lane.regs[0], lane.regs[3] = 7, 0xA5
    chip.cycle = phase
    chip.run([1])
    start = chip.cycle
    chip.step()
    assert lane.rb
    if stall_delimiters:
        # Restore the rejected rb==0 predicate only in this negative control.
        shift, _ = S.SLOT_FIELDS['FM']
        for n in (0, 1):
            lane.slots[n] = isa.decode_slot(int(compiled['lanes']['L1']['slots'][n], 16) | (8 << shift))
    producer = chip.fabric.producers['L0.O1']
    pending = list(commands)
    injected = consumed = 0
    end = settled = None
    initial_takes = lane.inp[1].takes
    initial_guard_takes = chip.pins[1].tx_port.takes
    visible, memory_takes, guard_takes = [], [], []
    limit = routine_service(compiled, routine, reflex_budget=len(commands))['bound_clocks']
    # Drain after RET too: a late delimiter must not disappear merely because
    # it did not interfere with the routine under test.
    for _ in range(limit + 100):
        elapsed = chip.cycle - start
        if pending and elapsed >= offset + 1 and producer.free():
            producer.load(S.TAGS['CTRL'], pending.pop(0))
            injected += 1
            visible.append(chip.cycle + 1)
        chip.step()
        if lane.inp[1].takes - initial_takes > len(memory_takes):
            memory_takes.append(chip.cycle)
        if chip.pins[1].tx_port.takes - initial_guard_takes > len(guard_takes):
            guard_takes.append(chip.cycle)
        if end is None and not lane.rb:
            end = chip.cycle - start
            consumed = lane.inp[1].takes - initial_takes
        if (settled is None and not pending and producer.free() and chip.pins[1].clk is None
                and chip.pins[0]._sel and chip.pins[0]._sel_next and chip.outputs()[0] & 0x80):
            settled = chip.cycle
        if end is not None and settled is not None:
            break
    assert not pending and injected == len(commands) and producer.free()
    assert lane.inp[1].takes - initial_takes == len(commands)
    assert lane.stats['fired'][0] + lane.stats['fired'][1] == len(commands)
    assert end is not None and end <= limit
    assert consumed <= len(commands)
    assert lane.stats['routine_steps'] == compiled['routines'][routine]['max_steps']
    assert len(visible) == len(memory_takes) == len(guard_takes) == len(commands)
    return dict(clocks=end, consumed_before_ret=consumed, bound=limit,
                memory_accept=max(t-v for t, v in zip(memory_takes, visible)),
                guard_accept=max(t-v for t, v in zip(guard_takes, visible)),
                guard_settled=settled - visible[0])


@pytest.mark.parametrize('routine', list(STATES))
@pytest.mark.parametrize('phase', range(4))
@pytest.mark.parametrize('commands', BURSTS)
def test_multicast_delimiters_at_each_routine_clock(routine, phase, commands):
    base = routine_service(image(), routine)['bound_clocks']
    for offset in range(base):
        record = delimiter_trace(routine, phase, offset, commands)
        assert record['memory_accept'] == record['guard_accept'] == 1
        assert record['guard_settled'] <= 2 * sum(c & 255 for c in commands) + 2 * len(commands) + 4


@pytest.mark.parametrize('budget', [-1, True, 1.5, 65536])
def test_invalid_reflex_budget_is_rejected(budget):
    with pytest.raises(ValueError):
        routine_service(image(), 'store_byte', reflex_budget=budget)


def test_budget_is_an_explicit_premise_not_a_proved_arrival_count():
    base = routine_service(image(), 'store_byte')
    burst = routine_service(image(), 'store_byte', reflex_budget=2)
    assert base['bound_clocks'] == 51 and burst['bound_clocks'] == 59
    assert not burst['arrival_invariants_proven'] and not burst['reflex_budget_proven']
    assert any('At most 2 reflex actions' in s for s in burst['assumptions'])


def test_routine_gated_delimiter_negative_control_delays_multicast():
    normal = delimiter_trace('store_byte', 1, 0, (0x3009, 0x3002))
    blocked = delimiter_trace('store_byte', 1, 0, (0x3009, 0x3002), stall_delimiters=True)
    assert normal['memory_accept'] == 1 and normal['consumed_before_ret'] == 2
    assert blocked['memory_accept'] > 1 and blocked['consumed_before_ret'] == 0
    assert blocked['guard_settled'] > normal['guard_settled']
