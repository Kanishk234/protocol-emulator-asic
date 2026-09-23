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


class I2CTarget:
    """Reference I2C target: 7-bit address, write bytes stored, read bytes served.

    From UM10204:
    - SDA is sampled on SCL rising edges, and changed only after SCL falls.
    - The receiver ACKs a byte by pulling SDA low for the 9th clock.
    - A transmitting target releases SDA for the controller's ACK/NACK.
    - Clock stretching: holding SCL low after the ACK clock (`stretch` clocks, 0 = none).
    Clock-level: step(scl_bus, sda_bus) -> (scl_release, sda_release).
    """

    def __init__(self, addr, read_data=(), stretch=0):
        self.addr = addr
        self.read_data = list(read_data)
        self.stretch = stretch
        self.received = []
        self.log = []                 # ("START",) ("STOP",) ("ADDR", byte, acked)
        self.state = "idle"
        self._prev = (1, 1)
        self._bits = self._byte = 0
        self._rw = 0
        self._out = 0xFF
        self._master_ack = True
        self._hold = 0
        self.scl, self.sda = 1, 1

    def step(self, scl, sda):
        pscl, psda = self._prev
        self._prev = (scl, sda)
        if self._hold:
            self._hold -= 1
            self.scl = 0 if self._hold else 1
        if pscl and scl and psda != sda:                       # START / STOP
            if not sda:
                self.state, self._bits, self._byte = "addr", 0, 0
                self.log.append(("START",))
            else:
                self.state = "idle"
                self.log.append(("STOP",))
            self.sda = 1
        elif scl and not pscl:                                 # rising edge: sample
            if self.state in ("addr", "write"):
                if self._bits < 8:
                    self._byte = (self._byte << 1) | sda
                self._bits += 1
            elif self.state == "read":
                if self._bits == 8:
                    self._master_ack = sda == 0
                self._bits += 1
        elif pscl and not scl:                                 # falling edge: drive
            self._falling()
        return self.scl, self.sda

    def _falling(self):
        if self.state in ("addr", "write") and self._bits == 8:
            if self.state == "addr":
                ours = self._byte >> 1 == self.addr
                self.log.append(("ADDR", self._byte, ours))
                if not ours:
                    self.state = "idle"
                    return
                self._rw = self._byte & 1
            else:
                self.received.append(self._byte)
            self.sda = 0                                      # ACK
        elif self._bits == 9:                                  # end of the ACK clock
            self.sda, self._bits, self._byte = 1, 0, 0
            if self.state == "addr":
                self.state = "read" if self._rw else "write"
            elif self.state == "read" and not self._master_ack:
                self.state = "idle"                          # controller NACKed: done
            if self.state == "read":
                self._out = self.read_data.pop(0) if self.read_data else 0xFF
                self.sda = (self._out >> 7) & 1
            if self.stretch and self.state in ("read", "write"):
                self.scl, self._hold = 0, self.stretch
        elif self.state == "read":
            self.sda = (self._out >> (7 - self._bits)) & 1 if self._bits < 8 else 1


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
