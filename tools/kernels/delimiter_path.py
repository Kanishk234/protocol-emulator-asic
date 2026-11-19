"""Observe wire-origin delimiters and guard/routine service in model workloads.

This is a finite-workload assertion monitor. No universal arrival or analog
guarantee follows from a successful trace. Every raw delimiter must be matched.
"""
import tripwire_spec as S
from tripc.service import routine_service


class DelimiterPathMonitor:
    def __init__(self, image):
        self.image = image
        self.rows = []
        self.jobs = []
        self.previous_wire = (1, 1)
        self.clock = -1
        self.rx_seq = self.command_seq = 0
        self.active_start = self.job = None
        self.inflight = []
        self.current_command = None

    def sample(self, chip, clock, scl, sda):
        assert clock == self.clock + 1, 'Observe every clock'
        self.clock = clock
        old_scl, old_sda = self.previous_wire
        if old_scl and scl and old_sda != sda:
            row = dict(edge=clock, kind='STOP' if sda else 'START', rx=None,
                       command=None, memory=None, guard=None, settled=None, first_rise=None)
            self.rows.append(row)
            self.active_start = None if sda else row
        if not old_scl and scl and self.active_start is not None:
            row = self.active_start
            if row['first_rise'] is None:
                row['first_rise'] = clock
                assert row['settled'] is not None and row['settled'] < clock, row
        self.previous_wire = scl, sda

        unit = chip.pins[0]
        rx = unit.rx_prod
        if rx.valid and rx.seq != self.rx_seq:
            self.rx_seq = rx.seq
            if rx.tag == S.TAGS['EVENT']:
                pending = [r for r in self.rows if r['rx'] is None]
                assert pending, 'Unmatched EVENT'
                row = pending[0]
                assert (rx.data >> 15) == (row['kind'] == 'STOP'), row
                row['rx'] = clock
                assert 0 < clock - row['edge'] <= 3, row

        producer = chip.fabric.producers['L0.O1']
        if producer.valid and producer.seq != self.command_seq:
            self.command_seq = producer.seq
            if producer.tag == S.TAGS['CTRL']:
                pending = [r for r in self.rows if r['command'] is None]
                assert pending, 'Unmatched guard command'
                row = pending[0]
                assert row['rx'] is not None, row
                assert producer.data == (0x3009 if row['kind'] == 'START' else 0x3002), row
                row['command'] = clock
                assert 0 < clock - row['rx'] <= 2, row
                self.inflight.append(row)
                self.current_command = row
        for row in list(self.inflight):
            if producer.valid and producer.tag == S.TAGS['CTRL']:
                # This row is current only until the next command is published.
                if row is self.current_command:
                    for key, port in [('memory', chip.lanes[1].inp[1]), ('guard', chip.pins[1].tx_port)]:
                        if row[key] is None and port.last_seq == producer.seq:
                            row[key] = clock
                            assert clock - row['command'] == 1, row
            if (row['settled'] is None and row['memory'] is not None and row['guard'] is not None
                    and chip.pins[1].clk is None and unit._sel and unit._sel_next
                    and chip.outputs()[0] & 0x80):
                row['settled'] = clock
                assert clock - row['edge'] <= 30, row
                self.inflight.remove(row)

        lane = chip.lanes[1]
        total = sum(lane.stats['fired'])
        if lane.rb and self.job is None:
            assert lane.mem_req is not None and lane.mem_req[0] == 'ENTRY'
            name = next(n for n, info in self.image['routines'].items()
                        if info['index'] == lane.mem_req[1])
            self.job = dict(routine=name, start=clock - 1, fired=total)
        elif not lane.rb and self.job is not None:
            job, self.job = self.job, None
            job['reflexes'] = total - job.pop('fired')
            job['clocks'] = clock - job['start']
            assert job['reflexes'] <= 2, job
            bound = routine_service(self.image, job['routine'], reflex_budget=job['reflexes'])
            assert job['clocks'] <= bound['bound_clocks'], job
            self.jobs.append(job)

    def finish(self):
        assert self.rows and self.jobs and self.job is None, 'Vacuous or incomplete trace'
        for r in self.rows:
            assert all(r[k] is not None for k in ('rx', 'command', 'memory', 'guard', 'settled')), r
        starts = [r for r in self.rows if r['first_rise'] is not None]
        assert starts
        def window_count(key):
            times = [r[key] for r in self.rows]
            return max(sum(0 <= t - start < 59 for t in times) for start in times)
        wire_count, memory_count = window_count('edge'), window_count('memory')
        assert wire_count <= 2 and memory_count <= 2, (wire_count, memory_count)
        return dict(events=len(self.rows), jobs=len(self.jobs),
                    rx=max(r['rx'] - r['edge'] for r in self.rows),
                    command=max(r['command'] - r['edge'] for r in self.rows),
                    settled=max(r['settled'] - r['edge'] for r in self.rows),
                    first_rise_margin=min(r['first_rise'] - r['settled'] for r in starts),
                    wire_events_per_59=wire_count, memory_delimiters_per_59=memory_count,
                    reflexes=max(j['reflexes'] for j in self.jobs),
                    job_clocks=max(j['clocks'] for j in self.jobs))
