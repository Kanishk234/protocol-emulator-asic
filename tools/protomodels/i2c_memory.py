"""External I2C memory transactions and pad-level ACK setup measurements.

This drives a controller; it does not implement TRIPWIRE or predict its internal state.
"""
from .i2c import I2CController


class MemoryController(I2CController):
    """Extend the bus controller with pointer-write/repeated-START reads.

    ACK setup is counted in simulation clocks before SCL rises, while the
    controller releases SDA. It measures observable pad behavior, not STA slack.
    """

    def __init__(self, clocks_per_bit, high_clocks=None):
        super().__init__(clocks_per_bit)
        self.period = clocks_per_bit
        # UM10204 rev.7 Table 11, at the target's 20 ns clock. Enforce actual
        # low/high and START timings, rather than checking frequency alone.
        if clocks_per_bit >= 500:
            min_high, min_low, min_start = 200, 235, 235
            self.required_setup = 13     # ceil(250 ns / 20 ns)
        elif clocks_per_bit >= 125:
            min_high, min_low, min_start = 30, 65, 30
            self.required_setup = 5      # 100 ns
        elif clocks_per_bit >= 50:
            min_high, min_low, min_start = 13, 25, 13
            self.required_setup = 3      # ceil(50 ns / 20 ns)
        else:
            raise ValueError('Memory scenarios support at most 1 MHz at a 50 MHz clock')
        self.high = min(clocks_per_bit // 2, clocks_per_bit - min_low) if high_clocks is None else high_clocks
        if not min_high <= self.high <= clocks_per_bit - min_low:
            raise ValueError('SCL phases violate the selected I2C mode timing')
        self.q = max((clocks_per_bit + 3) // 4, min_start)
        self.clocks = 0
        self.ack_records = []
        self._ack_window = None
        self._previous_scl = 1

    def random_read(self, addr, pointer, count):
        if not 0 <= pointer <= 255 or count < 1:
            raise ValueError('Need an eight-bit pointer and a positive read count')
        self.ops.append(('random_read', addr, pointer, count))

    def step(self, scl_bus, sda_bus):
        self.clocks += 1
        window = self._ack_window
        if window is not None and self.sda:
            if not scl_bus and not sda_bus:
                window.setdefault('first_low', self.clocks)
            if not self._previous_scl and scl_bus:
                window['sda_on_rise'] = sda_bus
                first = window.get('first_low')
                window['setup_clocks'] = None if first is None else self.clocks - first
            if scl_bus and 'sda_on_rise' in window and sda_bus != window['sda_on_rise']:
                window['changed_while_high'] = True
        self._previous_scl = scl_bus
        return super().step(scl_bus, sda_bus)

    def _bit(self, out):
        # Exact period, including odd periods; allow a short-high Fm+ stress case.
        low = self.period - self.high
        before = low // 2
        self.scl, self.sda = 0, out
        yield from self._hold(before)
        self.scl = 1
        yield from self._hold(self.high // 2)
        _, sampled = yield from self._hold(1)
        yield from self._hold(self.high - self.high // 2 - 1)
        self.scl = 0
        yield from self._hold(low - before)
        return sampled

    def _byte_out(self, byte):
        for bit in range(7, -1, -1):
            yield from self._bit(byte >> bit & 1)
        self._ack_window = {'byte': byte}
        ack = (yield from self._bit(1)) == 0
        self._ack_window['acked'] = ack
        self.ack_records.append(self._ack_window)
        self._ack_window = None
        return ack

    def _start(self):
        self.sda, self.scl = 1, 1
        yield from self._hold(self.q)
        self.sda = 0
        yield from self._hold(self.q)
        self.scl = 0
        low = self.period - self.high
        yield from self._hold(low - low // 2)
        self.log.append(('START',))

    def _restart(self):
        # Release SDA during SCL low before bringing SCL high; avoid a false STOP.
        self.scl, self.sda = 0, 1
        yield from self._hold(self.q)
        self.scl = 1
        yield from self._hold(self.q)
        self.sda = 0
        yield from self._hold(self.q)
        self.scl = 0
        low = self.period - self.high
        yield from self._hold(low - low // 2)
        self.log.append(('START',))

    def _send(self, byte):
        acked = yield from self._byte_out(byte)
        self.log.append(('W', byte, acked))
        return acked

    def _receive(self, count):
        for index in range(count):
            ack = index < count - 1
            value = yield from self._byte_in(ack)
            self.log.append(('R', value, ack))

    def _run(self):
        yield
        for op in self.ops:
            if op[0] == 'idle':
                yield from self._hold(op[1])
                continue
            yield from self._start()
            if op[0] == 'write':
                _, addr, data = op
                acked = yield from self._send(addr << 1)
                for value in data:
                    if not acked:
                        break
                    acked = yield from self._send(value)
            elif op[0] == 'read':
                _, addr, count = op
                if (yield from self._send(addr << 1 | 1)):
                    yield from self._receive(count)
            elif op[0] == 'random_read':
                _, addr, pointer, count = op
                addressed = yield from self._send(addr << 1)
                selected = (yield from self._send(pointer)) if addressed else False
                if selected:
                    yield from self._restart()
                    if (yield from self._send(addr << 1 | 1)):
                        yield from self._receive(count)
            else:
                raise ValueError('Unknown transaction: ' + op[0])
            yield from self._stop()
            yield from self._hold(4 * self.q)


def exercise(controller, addr=0x50):
    """Fixed public scenario; expected bytes come from its memory operations."""
    controller.read(addr, 2)                         # erased initial image/current address
    controller.write(addr, bytes([0x20, 0x12, 0xA5, 0x00, 0xFF]))
    controller.random_read(addr, 0x20, 4)             # pointer write + repeated START
    controller.read(addr, 1)                          # pointer persists and advances
    controller.write(addr + 1, bytes([0x20, 0x99]))    # wrong-address traffic cannot write
    controller.random_read(addr, 0x20, 1)
    controller.write(addr, bytes([0x06, 0x31, 0x42, 0x53, 0x64]))  # page wraps 7 -> 0
    controller.random_read(addr, 0, 2)
    controller.random_read(addr, 6, 2)
    controller.write(addr, bytes([0xFF, 0x7E]))
    controller.random_read(addr, 0xFF, 3)              # sequential read wraps 255 -> 0
    controller.read(addr + 1, 1)                      # wrong-address read is NACKed
    controller.random_read(addr, 0x20, 1)              # recover after NACK/STOP
    return [0xFF, 0xFF, 0x12, 0xA5, 0x00, 0xFF, 0xFF, 0x12,
            0x53, 0x64, 0x31, 0x42, 0x7E, 0x53, 0x64, 0x12]


def check_result(controller, expected, addr=0x50):
    reads = [entry[1] for entry in controller.log if entry[0] == 'R']
    assert reads == expected, (reads, expected, controller.log)
    wrong = {(addr + 1) << 1, (addr + 1) << 1 | 1}
    # In this fixed scenario, only wrong-address control bytes should be NACKed.
    for record in controller.ack_records:
        if record['byte'] in wrong and not record['acked']:
            assert record.get('sda_on_rise') == 1, record
        else:
            assert record['acked'] and record.get('sda_on_rise') == 0, record
            assert record.get('setup_clocks', 0) >= controller.required_setup, record
        assert not record.get('changed_while_high'), record
    nacks = [r['byte'] for r in controller.ack_records if not r['acked']]
    assert nacks == [(addr + 1) << 1, (addr + 1) << 1 | 1], nacks
    return min(r['setup_clocks'] for r in controller.ack_records if r['acked'])
