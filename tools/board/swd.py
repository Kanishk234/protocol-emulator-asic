"""SWD (Arm Serial Wire Debug) host on the WARP SWD bit engine (protocols/swd), held-out H3.

The fabric runs SWD's physical layer (clock, turnarounds, bit timing); this module builds the
packets from the ADIv5 specification: request bits and parity, ACK handling (WAIT retried,
FAULT cleared with ABORT), data parity, posted AP reads. MicroPython and CPython.

    import warp, swd
    w = warp.on_demo_board(clock_hz=10_000_000); w.load_file("swd.wbit"); w.run()
    s = swd.Swd(swd.WarpLink(w))
    s.connect()                       # line reset, JTAG-to-SWD, line reset, idle
    print(hex(s.dp_read(0x0)))        # DPIDR
    s.ap_write(0, 0x04, 0x20000000)   # AP 0, register 0x04 (e.g. a MEM-AP's TAR)
    print(hex(s.ap_read(0, 0x04)))
"""

OK, WAIT, FAULT = 0b001, 0b010, 0b100
JTAG_TO_SWD = 0xE79E
OP_WRITE, OP_READ, OP_TURN = 0x00, 0x20, 0x40


class SwdError(Exception):
    pass


def parity(v):
    p = 0
    while v:
        p ^= v & 1
        v >>= 1
    return p


class WarpLink:
    """The bit engine's commands over a warp.Warp host channel."""

    def __init__(self, w):
        self.w = w

    def send(self, *bytes_):
        for b in bytes_:
            self.w.ch_write(b)

    def reply(self):
        v = self.w.ch_read()
        if v is None:
            raise SwdError("no reply from the SWD engine")
        return v


class Swd:
    def __init__(self, link, retries=100):
        self.link = link
        self.retries = retries

    # ---- bit level
    def write_bits(self, v, n):
        while n > 0:
            k = min(n, 8)
            self.link.send(OP_WRITE | (k - 1), v & 0xFF)
            v >>= 8
            n -= k

    def read_bits(self, n):
        v, shift = 0, 0
        while n > 0:
            k = min(n, 8)
            self.link.send(OP_READ | (k - 1))
            v |= (self.link.reply() >> (8 - k)) << shift
            shift += k
            n -= k
        return v

    def turn(self):
        self.link.send(OP_TURN)

    # ---- line
    def line_reset(self):
        self.write_bits((1 << 56) - 1, 56)

    def connect(self):
        """Line reset, the JTAG-to-SWD sequence, line reset, idle cycles (ADIv5 B4.3)."""
        self.line_reset()
        self.write_bits(JTAG_TO_SWD, 16)
        self.line_reset()
        self.write_bits(0, 8)

    # ---- packets
    @staticmethod
    def request(apndp, rnw, a):
        a2, a3 = (a >> 2) & 1, (a >> 3) & 1
        return (1 | apndp << 1 | rnw << 2 | a2 << 3 | a3 << 4
                | (apndp ^ rnw ^ a2 ^ a3) << 5 | 0 << 6 | 1 << 7)

    def _transfer(self, apndp, rnw, a, v=0):
        """One packet; returns (ack, value)."""
        self.write_bits(self.request(apndp, rnw, a), 8)
        self.turn()
        ack = self.read_bits(3)
        if ack == OK and rnw:
            data = self.read_bits(32)
            p = self.read_bits(1)
            self.turn()
            if p != parity(data):
                raise SwdError("read data parity error")
            return ack, data
        self.turn()
        if ack == OK:
            self.write_bits(v, 32)
            self.write_bits(parity(v), 1)
        self.write_bits(0, 2)                  # idle cycles
        return ack, None

    def transfer(self, apndp, rnw, a, v=0):
        """A packet with WAIT retried; FAULT raises after clearing the sticky error (ABORT)."""
        for _ in range(self.retries):
            ack, data = self._transfer(apndp, rnw, a, v)
            if ack == OK:
                return data
            if ack == WAIT:
                continue
            if ack == FAULT:
                self._transfer(0, 0, 0x0, 0x1E)    # ABORT: clear sticky errors
                raise SwdError("FAULT")
            raise SwdError("no or invalid ACK 0b%s" % bin(ack)[2:])
        raise SwdError("WAIT %d times" % self.retries)

    # ---- registers
    def dp_read(self, a):
        return self.transfer(0, 1, a)

    def dp_write(self, a, v):
        self.transfer(0, 0, a, v)

    def _select(self, ap, reg):
        self.dp_write(0x8, (ap << 24) | (reg & 0xF0))

    def ap_write(self, ap, reg, v):
        self._select(ap, reg)
        self.transfer(1, 0, reg & 0x0C, v)

    def ap_read(self, ap, reg):
        """AP reads are posted: the value arrives with the next read of RDBUFF."""
        self._select(ap, reg)
        self.transfer(1, 1, reg & 0x0C)
        return self.dp_read(0xC)
