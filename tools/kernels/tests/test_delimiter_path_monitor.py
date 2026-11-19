"""Synthetic controls for the finite wire-to-guard assertion monitor."""
from types import SimpleNamespace as NS

import pytest
import tripc
from kernels import PROGRAMS
from kernels.delimiter_path import DelimiterPathMonitor


def trace(change=None):
    image, _ = tripc.compile_file(PROGRAMS / 'i2c_target_eeprom_guard.trw')
    monitor = DelimiterPathMonitor(image)
    for clock in range(40):
        rx = NS(valid=clock >= 3, seq=int(clock >= 3), tag=2, data=0)
        producer = NS(valid=clock >= 5, seq=int(clock >= 5), tag=1, data=0x3009)
        memory = NS(last_seq=int(clock >= 6))
        guard = NS(last_seq=int(clock >= 6))
        unit = NS(rx_prod=rx, _sel=True, _sel_next=True)
        gate = NS(clk={} if 6 <= clock < 26 else None, tx_port=guard)
        lane = NS(rb=10 <= clock < 28, mem_req=('ENTRY', 0) if clock == 10 else None,
                  stats={'fired': [int(clock >= 10), 0]}, inp=[None, memory])
        chip = NS(pins=[unit, gate], lanes=[None, lane],
                  fabric=NS(producers={'L0.O1': producer}), outputs=lambda: (0x80, 0, 0))
        scl = int(clock < 13 or clock >= 38)
        sda = 0
        if change:
            change(clock, chip)
        monitor.sample(chip, clock, scl, sda)
    return monitor.finish()


def test_complete_path_and_job_are_nonvacuous():
    assert trace() == dict(events=1, jobs=1, rx=3, command=5, settled=26,
                           first_rise_margin=12, wire_events_per_59=1,
                           memory_delimiters_per_59=1, reflexes=0, job_clocks=19)


@pytest.mark.parametrize('fault', ['late_rx', 'wrong_event', 'missing_command', 'wrong_command',
                                  'late_take', 'late_guard', 'extra_reflex', 'slow_job'])
def test_path_monitor_rejects_broken_endpoints(fault):
    def change(clock, chip):
        if fault == 'late_rx' and clock < 4:
            chip.pins[0].rx_prod.valid = False
        if fault == 'wrong_event':
            chip.pins[0].rx_prod.data = 0x8000
        if fault == 'missing_command':
            chip.fabric.producers['L0.O1'].valid = False
        if fault == 'wrong_command':
            chip.fabric.producers['L0.O1'].data = 0x3002
        if fault == 'late_take' and clock < 7:
            chip.lanes[1].inp[1].last_seq = 0
        if fault == 'late_guard':
            chip.pins[1].clk = {}
        if fault == 'extra_reflex' and clock >= 20:
            chip.lanes[1].stats['fired'][1] = 3
        if fault == 'slow_job' and 10 <= clock < 32:
            chip.lanes[1].rb = True
    with pytest.raises(AssertionError):
        trace(change)


def test_skipped_observation_is_rejected():
    image, _ = tripc.compile_file(PROGRAMS / 'i2c_target_eeprom_guard.trw')
    with pytest.raises(AssertionError, match='every clock'):
        DelimiterPathMonitor(image).sample(None, 1, 1, 1)
