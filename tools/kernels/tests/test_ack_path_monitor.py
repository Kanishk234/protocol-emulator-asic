"""Adversarial sampled traces must not produce a passing path receipt."""
from types import SimpleNamespace

import pytest

from kernels.ack_path import AckPathMonitor
from test_ack_path import contracts


def trace(*, internal=True, mutate=None):
    _, responses = contracts('i2c_target_eeprom_guard')
    window = dict(id=0, byte=0xA0, address=True, rise=0, fall=13, sample=50, end=63,
                  acked=True, drive=None, sample_phase_low=True)
    controller = SimpleNamespace(windows=[window], done=lambda: True)
    monitor = AckPathMonitor(controller, responses, 'fast_plus_at_20ns', internal)
    for clock in range(64):
        s = dict(clock=clock, scl=int(clock < 13 or 50 <= clock < 63),
                 target_low=clock >= 16, input_available=3 <= clock < 7,
                 input_tag=0, input_data=0xA0, state=1 if clock < 4 else 2 if clock < 6 else 3,
                 flags=0 if clock < 5 else 1, pending=int(clock == 4),
                 exec_idle=clock != 4 and clock != 6, routine_idle=True,
                 outputs_free=True, other_empty=True, tx_empty=clock < 8,
                 tx_bits=int(8 <= clock < 16), selected=True, enabled=True, running=True,
                 rx_free=clock < 3 or clock >= 7, rx_seq=int(clock >= 3),
                 out_seq=int(clock >= 7), out_valid=clock >= 7, out_tag=0, out_data=0)
        if mutate:
            mutate(clock, s, window)
        monitor.sample(s)
    return monitor.finish()


def test_manual_timing_geometry_matches_contract():
    rows = trace()
    assert rows == [dict(role='address_ack', byte=0xA0, edge_to_drive=3,
                         target_low_setup=33, entry_checked=True,
                         rx_publish=3, lane=4, tx_accept=1, arm=8)]


@pytest.mark.parametrize('field,value', [
    ('exec_idle', False), ('routine_idle', False), ('pending', 1),
    ('outputs_free', False), ('other_empty', False), ('tx_empty', False),
    ('enabled', False), ('selected', False), ('running', False),
])
def test_rejects_failed_entry_premise(field, value):
    def mutate(clock, snapshot, window):
        if clock == 3:
            snapshot[field] = value
    with pytest.raises(AssertionError):
        trace(mutate=mutate)


@pytest.mark.parametrize('failure', ['rx_busy', 'new_arrival', 'late_output', 'late_arm',
                                      'late_drive', 'early_drive', 'unstable_high',
                                      'deselected', 'missing_entry', 'unexpected_nack', 'interrupted_low'])
def test_faults_cannot_be_silently_omitted(failure):
    def mutate(clock, s, w):
        if failure == 'rx_busy' and clock == 1: s['rx_free'] = False
        if failure == 'new_arrival' and clock == 5: s['rx_seq'] ^= 1
        if failure == 'late_output': s['out_seq'] = int(clock >= 8)
        if failure == 'late_arm': s['tx_bits'] = int(9 <= clock < 16)
        if failure == 'late_drive': s['target_low'] = clock >= 17
        if failure == 'early_drive': s['target_low'] = clock >= 12
        if failure == 'unstable_high' and clock == 51: s['target_low'] = False
        if failure == 'deselected' and clock == 10: s['selected'] = False
        if failure == 'missing_entry': s['input_available'] = False
        if failure == 'unexpected_nack': w['acked'] = False
        if failure == 'interrupted_low' and clock == 48: s['target_low'] = False
    with pytest.raises(AssertionError):
        trace(mutate=mutate)


def test_external_only_mode_does_not_claim_entry_checks():
    rows = trace(internal=False)
    assert rows[0]['entry_checked'] is False and 'arm' not in rows[0]
    with pytest.raises(AssertionError):
        trace(internal=False, mutate=lambda clock, s, w: s.update(target_low=clock >= 17))
