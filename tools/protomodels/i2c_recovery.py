"""Interrupted-transaction stimulus; observes resolved pins, never chip state."""
from .i2c_memory import MemoryController


class RecoveryController(MemoryController):
    """Seed memory, interrupt a transfer, optionally clear the bus, then read back.

    Seven prefix bits are a special boundary: the STOP preparation clocks bit
    eight. For a read, requesting STOP need not produce STOP on the actual bus.
    Keep requested actions separate from passively observed START/STOP edges.
    """

    def __init__(self, kind, bits, clear=False, period=50, high=13):
        if kind not in ('address', 'write', 'read') or not 0 <= bits <= 7:
            raise ValueError('Need address/write/read and zero to seven prefix bits')
        super().__init__(period, high)
        self.kind, self.bits, self.clear = kind, bits, clear
        self.stage = 'seed'
        self.verify_start_clock = None
        self.edges = []
        self._previous_bus = (1, 1)

    def step(self, scl_bus, sda_bus):
        scl, sda = self._previous_bus
        if scl and scl_bus and sda != sda_bus:
            self.edges.append((self.stage, 'STOP' if sda_bus else 'START'))
        self._previous_bus = scl_bus, sda_bus
        return super().step(scl_bus, sda_bus)

    def _run(self):
        self.ops = [('write', 0x50, bytes([0x20, 0x12, 0xA5, 0, 0xFF]))]
        yield from super()._run()
        if self.kind == 'read':
            self.ops = [('write', 0x50, bytes([0x20]))]
            yield from super()._run()
        self.stage = 'interrupt'
        yield from self._start()
        if self.kind == 'address':
            value = 0xA0
        elif self.kind == 'write':
            assert (yield from self._send(0xA0))
            assert (yield from self._send(0x20))
            value = 0x66
        else:
            assert (yield from self._send(0xA1))
            value = 0xFF  # Release SDA while the target transmits.
        for bit in range(7, 7 - self.bits, -1):
            yield from self._bit(value >> bit & 1)
        self.stage = 'recovery'
        if self.clear:
            for _ in range(9):
                yield from self._bit(1)
        yield from self._stop()
        yield from self._hold(4 * self.q)
        self.stage = 'verify'
        self.verify_start_clock = self.clocks
        self.ops = [('random_read', 0x50, 0x20, 4)]
        yield from super()._run()

    def check_recovered(self):
        assert self.done(), 'Recovery stimulus timed out'
        assert ('recovery', 'STOP') in self.edges, self.edges
        reads = [r[1] for r in self.log if r[0] == 'R']
        assert reads == [0x12, 0xA5, 0, 0xFF], (reads, self.log)
