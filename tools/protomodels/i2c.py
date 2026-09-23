"""Reference I2C controller (the other side of the wire in simulation).

Written from the I2C-bus specification (NXP UM10204): SDA changes only while SCL is
low, except for START (SDA falls while SCL is high) and STOP (SDA rises while SCL is
high); the receiver acknowledges each byte by pulling SDA low during the 9th clock.
Not written from TRIPWIRE firmware (VERIFICATION.md §9 rule 2).

Clock-level: step(scl_bus, sda_bus) is called once per 50 MHz clock with the resolved
open-drain bus levels and returns (scl_release, sda_release), 1 = released (pulled
high), 0 = driven low. Each bit is 4 quarter-periods: SCL low (data set up), SCL high
x2 (data sampled in the middle), SCL low.
"""


class I2CController:
    def __init__(self, clocks_per_bit):
        if clocks_per_bit < 8:
            raise ValueError("need at least 8 clocks per bit")
        self.q = clocks_per_bit // 4
        self.ops = []
        self.log = []               # ("W", byte, acked) / ("R", byte, acked_by_us) / ("START",) / ("STOP",)
        self._gen = None
        self.scl = self.sda = 1

    # transactions -------------------------------------------------------
    def write(self, addr, data):
        self.ops.append(("write", addr, bytes(data)))

    def read(self, addr, n):
        self.ops.append(("read", addr, n))

    def idle(self, clocks):
        self.ops.append(("idle", clocks))

    def done(self):
        return self._gen is not None and self._gen is False

    # clock-level --------------------------------------------------------
    def step(self, scl_bus, sda_bus):
        if self._gen is None:
            self._gen = self._run()
            next(self._gen)
        if self._gen is not False:
            try:
                self._gen.send((scl_bus, sda_bus))
            except StopIteration:
                self._gen = False
        return self.scl, self.sda

    def _hold(self, n):
        """Hold the current outputs for n clocks; returns the bus at the last clock."""
        bus = None
        for _ in range(n):
            bus = yield
        return bus

    def _run(self):
        q = self.q
        yield
        for op in self.ops:
            if op[0] == "idle":
                yield from self._hold(op[1])
                continue
            yield from self._start()
            if op[0] == "write":
                _, addr, data = op
                acked = yield from self._byte_out(addr << 1)
                self.log.append(("W", addr << 1, acked))
                for b in data:
                    if not acked:
                        break
                    acked = yield from self._byte_out(b)
                    self.log.append(("W", b, acked))
            else:
                _, addr, n = op
                acked = yield from self._byte_out((addr << 1) | 1)
                self.log.append(("W", (addr << 1) | 1, acked))
                for i in range(n if acked else 0):
                    b = yield from self._byte_in(ack=(i < n - 1))
                    self.log.append(("R", b, i < n - 1))
            yield from self._stop()
            yield from self._hold(4 * q)

    def _start(self):
        q = self.q
        self.sda, self.scl = 1, 1
        yield from self._hold(q)
        self.sda = 0                                  # SDA falls while SCL high
        yield from self._hold(q)
        self.scl = 0
        yield from self._hold(q)
        self.log.append(("START",))

    def _stop(self):
        q = self.q
        self.scl, self.sda = 0, 0
        yield from self._hold(q)
        self.scl = 1
        yield from self._hold(q)
        self.sda = 1                                  # SDA rises while SCL high
        yield from self._hold(q)
        self.log.append(("STOP",))

    def _bit(self, out):
        """One clock cycle; drives `out` (1 = release) and returns the sampled SDA."""
        q = self.q
        self.scl, self.sda = 0, out
        yield from self._hold(q)
        self.scl = 1
        yield from self._hold(q)
        _, sda = yield from self._hold(1)             # sample in the middle of SCL high
        yield from self._hold(q - 1)
        self.scl = 0
        yield from self._hold(q)
        return sda

    def _byte_out(self, byte):
        for i in range(7, -1, -1):
            yield from self._bit((byte >> i) & 1)
        ack = yield from self._bit(1)                 # release SDA; target pulls low to ACK
        return ack == 0

    def _byte_in(self, ack):
        b = 0
        for _ in range(8):
            b = (b << 1) | (yield from self._bit(1))
        yield from self._bit(0 if ack else 1)
        return b
