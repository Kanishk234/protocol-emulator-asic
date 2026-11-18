"""Compiler lane-token bounds checked against actual RTL, not a pin timing proof."""
import json
from pathlib import Path

import cocotb

from test_lane import Lane, slot
import tripc
import tripwire_spec as S
from tripc.response import analyze_queries


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
