"""Verification helpers: external I2C markers and optional internal path checks.

The compiler budget is independent of this monitor. Adapters in tests supply
model/RTL snapshots; external-only replay deliberately cannot check entry state.
"""
from collections import deque

import tripwire_spec as S
from protomodels.i2c_memory import MemoryController


class AckTimingController(MemoryController):
    def __init__(self, period, high, phase=0):
        super().__init__(period, high)
        self.phase = phase
        self.windows = []
        self._window = None
        self._wire_previous = (1, 1)
        self._address_next = True

    def _run(self):
        yield from self._hold(self.phase)
        yield from super()._run()

    def _byte_out(self, byte):
        window = {'id': len(self.windows), 'byte': byte, 'address': self._address_next,
                  'bits': 0, 'sampled_byte': 0, 'rise': None, 'fall': None,
                  'sample': None, 'end': None, 'acked': None, 'drive': None,
                  'low_since': None, 'stable_drive': None, 'sample_phase_low': True}
        self._address_next = False
        self.windows.append(window)
        self._window = window
        window['acked'] = yield from super()._byte_out(byte)
        self._window = None
        return window['acked']

    def step(self, scl, sda):
        old_scl, old_sda = self._wire_previous
        if old_scl and scl and old_sda and not sda:
            self._address_next = True
        w = self._window
        if w is not None:
            if not old_scl and scl:
                w['bits'] += 1
                if w['bits'] <= 8:
                    w['sampled_byte'] = (w['sampled_byte'] << 1) | sda
                if w['bits'] == 8:
                    assert w['sampled_byte'] == w['byte'], w
                    w['rise'] = self.clocks
                elif w['bits'] == 9:
                    w['sample'] = self.clocks
            if old_scl and not scl:
                if w['bits'] == 8:
                    w['fall'] = self.clocks
                elif w['bits'] == 9:
                    w['end'] = self.clocks
        self._wire_previous = scl, sda
        return super().step(scl, sda)


class AckPathMonitor:
    def __init__(self, controller, responses, profile, internal=True):
        self.controller = controller
        self.responses = responses
        self.profile = profile
        self.internal = internal
        self.history = deque(maxlen=32)
        self.entries = {}
        self.records = []
        self.previous_clock = -1
        for name in ('address_ack', 'write_ack'):
            r = responses[name]
            assert r['status'] == 'bounded' and r['linked_budget']['status'] == 'conditional_pass'
            assert r['query']['lane'] == 'L0' and r['query']['input_port'] == 'I0'
            assert r['query']['response_port'] == 'O0' and not r['query']['registers']

    def sample(self, snapshot):
        s = snapshot
        clock = s['clock']
        assert clock == self.previous_clock + 1, 'Path monitor must observe every clock'
        self.previous_clock = clock
        if self.internal:
            self.history.append(dict(s))
        if not self.controller.windows:
            return
        w = self.controller.windows[-1]
        if w['rise'] is None:
            return
        if w['end'] is None or clock < w['end']:
            if s['target_low']:
                if w['drive'] is None:
                    w['drive'] = clock
                if w.get('low_since') is None:
                    w['low_since'] = clock
            else:
                w['low_since'] = None
            if w['sample'] is not None and clock == w['sample']:
                w['stable_drive'] = w.get('low_since')
            if w['sample'] is not None and clock >= w['sample'] and s['scl']:
                w['sample_phase_low'] &= s['target_low']
        if not self.internal:
            return
        role = 'address_ack' if w['address'] else 'write_ack'
        response = self.responses[role]
        q = response['query']
        eligible = (s['input_available'] and s['input_tag'] == S.TAGS['DATA'] and s['state'] == q['state']
                    and s['input_data'] in q['input_values']
                    and (s['flags'] & q['flag_mask']) == q['flag_value'])
        if eligible and w['id'] not in self.entries:
            assert s['input_data'] == w['byte'], (s, w)
            required = ('exec_idle', 'routine_idle', 'outputs_free', 'other_empty',
                        'tx_empty', 'selected', 'enabled', 'running')
            assert all(s[key] for key in required) and s['pending'] == 0 and not s['target_low'], (s, w)
            before = [row for row in self.history if w['rise'] <= row['clock'] < clock]
            assert len(before) == clock - w['rise'] and before, (clock, w)
            assert all(row['rx_free'] and row['rx_seq'] == before[0]['rx_seq'] for row in before), before
            publish = clock - w['rise']
            assert publish <= response['linked_budget']['pipeline_clocks']['rx_publish'], (publish, w)
            self.entries[w['id']] = {'window': w, 'role': role, 'head': clock,
                                      'rx_publish': publish, 'rx_seq': s['rx_seq'],
                                      'out_seq': s['out_seq'], 'out': None, 'arm': None}
        entry = self.entries.get(w['id'])
        if entry is None:
            return
        if w['end'] is None or clock < w['end']:
            assert s['selected'] and s['enabled'] and s['running'], (s, w)
        if entry['out'] is None:
            assert s['rx_seq'] == entry['rx_seq'] and s['other_empty'] and s['routine_idle'], (s, w)
            if s['input_available']:
                assert s['input_tag'] == S.TAGS['DATA'] and s['input_data'] == w['byte'], (s, w)
            if s['out_seq'] != entry['out_seq']:
                assert s['out_valid'] and s['out_tag'] == S.TAGS['DATA'] and s['out_data'] == 0, (s, w)
                entry['out'] = clock
                assert clock - entry['head'] <= response['bound_clocks'], entry
        if entry['out'] is not None and entry['arm'] is None and s['tx_bits'] == 1:
            entry['arm'] = clock
            assert clock - entry['out'] <= response['linked_budget']['pipeline_clocks']['tx_accept'], entry
            assert clock - w['rise'] <= response['linked_budget']['profiles'][self.profile]['armed_by_clocks'], entry

    def finish(self):
        assert self.controller.done(), 'Incomplete controller waveform'
        for w in self.controller.windows:
            if w['address']:
                expected = w['byte'] in self.responses['address_ack']['query']['input_values']
            else:
                assert w['byte'] in self.responses['write_ack']['query']['input_values'], w
                expected = True
            assert w['acked'] is not None and bool(w['acked']) == expected, w
        acknowledged = [w for w in self.controller.windows if w['acked']]
        assert acknowledged, 'No acknowledged byte; timing check would be vacuous'
        if self.internal:
            assert len(self.entries) == len(acknowledged), (len(self.entries), len(acknowledged))
        records = []
        for w in acknowledged:
            role = 'address_ack' if w['address'] else 'write_ack'
            r = self.responses[role]
            p = r['linked_budget']['profiles'][self.profile]
            assert w['byte'] in r['query']['input_values'], w
            assert all(w.get(k) is not None for k in ('rise', 'fall', 'sample', 'end', 'drive', 'stable_drive')), w
            assert w['fall'] - w['rise'] >= p['response_edge_min'], w
            assert w['sample'] - w['fall'] >= p['sample_edge_min'], w
            assert w['drive'] >= w['fall'], w
            drive = w['stable_drive'] - w['fall']
            assert 0 <= drive <= r['linked_budget']['pipeline_clocks']['edge_to_drive'], w
            setup = w['sample'] - w['stable_drive'] - r['linked_budget']['pipeline_clocks']['observation_reserve']
            assert setup >= p['target_low_setup_bound_clocks'] and w['sample_phase_low'], w
            record = {'role': role, 'byte': w['byte'], 'edge_to_drive': drive,
                      'target_low_setup': setup, 'entry_checked': self.internal}
            if self.internal:
                entry = self.entries[w['id']]
                assert entry['out'] is not None and entry['arm'] is not None, entry
                assert entry['arm'] < w['fall'] and entry['arm'] <= w['drive'], entry
                record.update(rx_publish=entry['rx_publish'], lane=entry['out'] - entry['head'],
                              tx_accept=entry['arm'] - entry['out'], arm=entry['arm'] - w['rise'])
            records.append(record)
        self.records = records
        return records
