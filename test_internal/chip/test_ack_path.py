"""Separate internal-entry and port-only checks of conditional ACK edge budgets."""
import json

import cocotb
from cocotb.triggers import ClockCycles

from chiplib import ROOT, Wire, hex_bytes, load, sigrok, start, write_vcd
from kernels.ack_path import AckPathMonitor, AckTimingController
from protomodels.i2c_memory import check_result, exercise
from tripc.linked_budget import compose_linked_response
from tripc.response import analyze_queries


def contracts(image):
    queries = json.loads((ROOT / 'programs/analysis/i2c_memory_response.json').read_text())
    budget = json.loads((ROOT / 'programs/analysis/i2c_memory_linked_budget.json').read_text())
    responses = analyze_queries(image, queries)
    for r in responses.values():
        r['linked_budget'] = compose_linked_response(image, r, budget)
    return responses


def internal_snapshot(dut, clock, scl, outputs, enables):
    lane = dut.u_chip.g_lane[0].u_lane
    unit = dut.u_chip.g_unit[0].u_unit
    tx = unit.u_tx
    get = lambda signal: int(signal.value)
    head = get(lane.in_head) & ((1 << 18) - 1)
    output = get(lane.out_tok) & ((1 << 18) - 1)
    return dict(clock=clock, scl=scl, target_low=bool(enables & 1 and not outputs & 1),
                input_available=bool(get(lane.in_avail) & 1), input_tag=head >> 16,
                input_data=head & 0xFFFF, state=get(lane.dbg_state), flags=get(lane.dbg_flags),
                pending=get(lane.dbg_pend),
                exec_idle=not (get(lane.ex_slot) or get(lane.ex_rt) or get(lane.ex_ld)),
                routine_idle=not (get(lane.rb) or get(lane.st_v) or get(lane.acc_v)),
                outputs_free=get(lane.ofree) == 3, other_empty=not get(lane.in_avail) & 2,
                tx_empty=not (get(tx.rem) or get(tx.lk_ret) or get(tx.lk_pre) or get(tx.pend_v)
                              or get(tx.p_act) or get(tx.w_v)),
                tx_bits=get(tx.rem), selected=bool(get(unit.sel) and get(unit.sel_q)),
                enabled=bool(get(tx.oe)), running=bool(get(lane.run)),
                rx_free=bool(get(unit.rx_free)), rx_seq=get(dut.u_chip.g_unit[0].u_prod.seq),
                out_seq=get(lane.out_seq) & 1, out_valid=bool(get(lane.out_valid) & 1),
                out_tag=output >> 16, out_data=output & 0xFFFF)


async def waveform(dut, pins, controller, responses, profile, expected, label, internal):
    monitor = AckPathMonitor(controller, responses, profile, internal)

    def environment(uo, outputs, enables, bus):
        assert not enables & outputs & 1, 'Open-drain SDA driven high'
        assert not enables & 2, 'Target drove SCL'
        scl, sda = bus >> 1 & 1, bus & 1
        snapshot = (internal_snapshot(dut, controller.clocks, scl, outputs, enables) if internal else
                    dict(clock=controller.clocks, scl=scl,
                         target_low=bool(enables & 1 and not outputs & 1)))
        levels = controller.step(scl, sda)
        monitor.sample(snapshot)
        return {}, {0: levels[1], 1: levels[0]}

    wire = Wire(pins, environment, {'scl': lambda uo, bus: bus >> 1 & 1,
                                     'sda': lambda uo, bus: bus & 1})
    try:
        for _ in range(controller.period * 15 + 100):
            if controller.done():
                break
            await ClockCycles(dut.clk, 100)
        assert controller.done(), 'ACK-path waveform timed out'
        if internal:
            check_result(controller, expected)
            assert int(dut.u_chip.overrun.value) == 0
        else:
            assert [x[1] for x in controller.log if x[0] == 'R'] == expected
            assert all(not r.get('changed_while_high') for r in controller.ack_records)
            for r in controller.ack_records:
                assert r['controller_released_on_rise'] and not r.get('controller_drove_high_phase')
                assert not r.get('extra_rise')
                if r['acked']:
                    assert r['setup_clocks'] >= controller.required_setup
        records = monitor.finish()
    finally:
        wire.stop()
    simulator = cocotb.SIM_NAME.replace(' ', '_').replace('/', '_')
    path = f'ack_path_{simulator}_{label}.vcd'
    write_vcd(path, wire.rec)
    decoded = sigrok(path, 'i2c:scl=scl:sda=sda', 'i2c')
    assert decoded is not None and hex_bytes(decoded, 'Data read: ') == expected, decoded
    fields = ('rx_publish', 'lane', 'tx_accept', 'arm', 'edge_to_drive', 'target_low_setup')
    summary = {field: sorted({r[field] for r in records if field in r}) for field in fields}
    dut._log.info('ACK_PATH %s internal=%s count=%d metrics=%s', label, internal, len(records), summary)
    return records


@cocotb.test()
async def test_ack_entry_path(dut):
    """RTL-only: observe rather than assume the compiler query's entry premises."""
    index = 0
    for program in ('i2c_target_eeprom', 'i2c_target_eeprom_guard'):
        for period, high, phase in [(125, 60, 0), (50, 25, 0), (50, 13, 0),
                                    (50, 25, 1), (50, 13, 3)]:
            p = await start(dut, uio=0xFF, clock=index == 0)
            index += 1
            image = await load(p, program)
            ctrl = AckTimingController(period, high, phase)
            expected = exercise(ctrl)
            profile = 'fast_at_20ns' if period == 125 else 'fast_plus_at_20ns'
            records = await waveform(dut, p, ctrl, contracts(image), profile, expected,
                                     f'{program}_{period}_{high}_{phase}', True)
            assert len(records) == 35 and all(r['entry_checked'] for r in records)


@cocotb.test()
async def test_ack_edge_budget(dut):
    """Port-only: this selected case also runs on the exact official netlist."""
    for index, program in enumerate(('i2c_target_eeprom', 'i2c_target_eeprom_guard')):
        p = await start(dut, uio=0xFF, clock=index == 0)
        image = await load(p, program)
        responses = contracts(image)
        for high in (25, 13):
            ctrl = AckTimingController(50, high)
            # Fully seed the bytes read, so profiles can run without host reload.
            ctrl.write(0x50, bytes([0x20, 0x12, 0xA5]))
            ctrl.random_read(0x50, 0x20, 2)
            ctrl.write(0x51, bytes([0x20, 0x99]))
            ctrl.random_read(0x50, 0x20, 1)
            records = await waveform(dut, p, ctrl, responses, 'fast_plus_at_20ns',
                                     [0x12, 0xA5, 0x12], f'{program}_edges_{high}', False)
            assert len(records) == 10 and all(not r['entry_checked'] for r in records)
