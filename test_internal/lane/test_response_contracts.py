"""Compiler lane-token bounds checked against actual RTL, not a pin timing proof."""
import json
from pathlib import Path

import cocotb

from test_lane import Lane, slot
import tripc
import tripwire_spec as S
from tripc.response import analyze_queries
from tripc.service import routine_service


ROOT = Path(__file__).resolve().parents[2]


@cocotb.test()
async def test_compiler_ack_token_bounds(dut):
    h = await Lane.start(dut)
    count = 0
    for program in ('i2c_target_eeprom', 'i2c_target_eeprom_guard'):
        image, _ = tripc.compile_file(ROOT / 'programs' / f'{program}.trw')
        queries = json.loads((ROOT / 'programs/analysis/i2c_memory_response.json').read_text())
        results = analyze_queries(image, queries)
        lane_image = image['lanes']['L0']
        h.set_k(lane_image['k'])
        for reg, value in enumerate((0x1357, 0xACE1, 0x8000, 0xFFFF)):
            await h.tick(host=(reg, value))
        for result in results.values():
            assert result['status'] == 'bounded'
            q = result['query']
            for case in result['cases']:
                # Finish post-response EXEC effects before preparing a new idle
                # query. All output subscribers are taken, as the contract says.
                h.set_slots([])
                await h.tick(run=0, in_avail=0, out_all_taken=3)
                await h.tick()
                for bit in range(3):
                    h.set_slots([slot(OP=S.OPS['MOVB'], DST=S.DST['none'],
                                      BSEL=S.BSEL['imm'], IMM=0 if case['initial_flags'] >> bit & 1 else 1,
                                      DFE=1, DF=bit)])
                    await h.tick(step=1)
                    await h.tick()
                await h.tick(host=(4, q['state']))
                h.set_slots([int(w, 16) for w in lane_image['slots']])
                # Snapshot before the first EVAL: pipeline and pending flags
                # must actually be idle, rather than assumed by the test oracle.
                before = await h.tick()
                assert before['dbg_pend'] == 0 and before['dbg_rir_valid'] == 0
                assert before['dbg_flags'] == case['initial_flags']
                seq = before['out_seq'] & 1
                available = 1
                token = (S.TAGS[q['input_tag']] << S.DATA_BITS) | case['input']
                for clock in range(case['response_clocks'] + 2):
                    record = await h.tick(run=1, in_avail=available, in_head=token)
                    if clock < len(case['trace']):
                        expected = case['trace'][clock]
                        assert record['dbg_pend'] == expected['pending']
                        assert record['dbg_state'] == expected['state']
                    if (record['out_seq'] & 1) != seq:
                        assert clock == case['response_clocks'], (program, q, case, clock)
                        assert record['out_valid'] & 1
                        expected_token = (S.TAGS[q['response_tag']] << S.DATA_BITS) | q['response_data']
                        assert record['out_tok'] & ((1 << 18) - 1) == expected_token
                        break
                    if record['in_take'] & 1:
                        available = 0
                else:
                    raise AssertionError(f'RTL missed compiler response bound: {program}, {case}')
                count += 1
    assert count == 2080
    dut._log.info('Compiler ACK token bounds match RTL for %d closed-contract cases', count)


@cocotb.test()
async def test_compiler_memory_routine_service(dut):
    """Count real SRAM rotation stalls, including the store's separate access."""
    h = await Lane.start(dut)
    maxima = {}
    count = 0
    states = {'refresh': 'M_REFRESH', 'store_byte': 'M_STORE', 'advance_read': 'M_ADVANCE'}
    for program in ('i2c_target_eeprom', 'i2c_target_eeprom_guard'):
        image, _ = tripc.compile_file(ROOT / 'programs' / f'{program}.trw')
        lane = image['lanes']['L1']
        await h.mem_write(0, image['sram'])
        h.set_k(lane['k'])
        for routine, state in states.items():
            service = routine_service(image, routine)
            assert service['status'] == 'conditional_bound'
            for phase in range(4):
                for pointer in (0, 7, 8, 255):
                    h.set_slots([])
                    await h.tick(run=0, in_avail=0)
                    for reg, value in enumerate((pointer, 0xFF, 0, pointer ^ 0xA5)):
                        await h.tick(host=(reg, value))
                    await h.tick(host=(4, lane['states'][state]))
                    before = await h.tick()
                    while before['tnow'] % 4 != phase:
                        before = await h.tick()
                    assert not before['dbg_flags'] & 8 and not before['dbg_rir_valid']
                    h.set_slots([int(w, 16) for w in lane['slots']])
                    start = await h.tick(run=1)
                    busy = False
                    accesses = 0
                    for elapsed in range(service['bound_clocks'] + 1):
                        record = start if elapsed == 0 else await h.tick()
                        accesses += bool(record['mem_en'])
                        busy |= bool(record['dbg_flags'] & 8)
                        if busy and not record['dbg_flags'] & 8:
                            assert elapsed <= service['bound_clocks']
                            assert accesses == service['sram_accesses']
                            maxima[routine] = max(maxima.get(routine, 0), elapsed)
                            break
                    else:
                        raise AssertionError((program, routine, phase, pointer, service))
                    count += 1
    assert count == 96
    assert maxima == {'refresh': 19, 'store_byte': 51, 'advance_read': 31}
    dut._log.info('ROUTINE_SERVICE cases=%d maxima=%s', count, maxima)


@cocotb.test()
async def test_compiler_delimiter_interference(dut):
    """L1 service under each one/two-delimiter burst and injection clock.

    The lane harness checks the actual CTRL consumers, not the U1 pin guard.
    Input words are held until taken, with the fabric's inter-word bubble.
    """
    h = await Lane.start(dut)
    image, _ = tripc.compile_file(ROOT / 'programs/i2c_target_eeprom_guard.trw')
    lane = image['lanes']['L1']
    await h.mem_write(0, image['sram'])
    h.set_k(lane['k'])
    states = {'refresh': 'M_REFRESH', 'store_byte': 'M_STORE', 'advance_read': 'M_ADVANCE'}
    bursts = [(0x3009,), (0x3002,), (0x3009, 0x3002), (0x3002, 0x3009)]
    count = 0
    maxima = {}
    for routine, state in states.items():
        base = routine_service(image, routine)['bound_clocks']
        for phase in range(4):
            for commands in bursts:
                limit = routine_service(image, routine, reflex_budget=len(commands))['bound_clocks']
                for offset in range(base):
                    h.set_slots([])
                    await h.tick(run=0, in_avail=0)
                    for reg, value in enumerate((7, 0xFF, 0, 0xA5)):
                        await h.tick(host=(reg, value))
                    await h.tick(host=(4, lane['states'][state]))
                    before = await h.tick()
                    while before['tnow'] % 4 != phase:
                        before = await h.tick()
                    h.set_slots([int(w, 16) for w in lane['slots']])
                    pending = list(commands)
                    busy = False
                    end = None
                    gap = 0
                    takes = 0
                    for elapsed in range(limit + 10):
                        available = bool(pending and elapsed >= offset + 2 and not gap)
                        token = ((S.TAGS['CTRL'] << S.DATA_BITS) | pending[0]) if available else 0
                        record = await h.tick(run=1, in_avail=2 if available else 0,
                                              in_head=token << (S.DATA_BITS + S.TAG_BITS))
                        if gap:
                            gap -= 1
                        if record['in_take'] & 2:
                            assert available
                            pending.pop(0)
                            takes += 1
                            gap = 1
                        busy |= bool(record['dbg_flags'] & 8)
                        if busy and not record['dbg_flags'] & 8 and end is None:
                            end = elapsed
                            assert end <= limit, (routine, phase, offset, commands, end, limit)
                        if end is not None and not pending and not gap:
                            break
                    assert end is not None and takes == len(commands)
                    maxima[routine] = max(maxima.get(routine, 0), end)
                    count += 1
    assert count == 1616
    dut._log.info('DELIMITER_SERVICE cases=%d maxima=%s', count, maxima)
