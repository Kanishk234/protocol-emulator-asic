"""The SWD reference target against an ideal host written from the same specification."""

from refmodels import swd


class Host:
    """Bit-level SWD host: one SWCLK cycle = data set while low, target sampled at the rising
    edge; the host samples the target's data just before a rising edge."""

    def __init__(self, tgt, half=2):
        self.t, self.half = tgt, half

    def _cycle(self, drive):
        seen = None
        for _ in range(self.half):                 # clock low
            d = self.t.step(0, drive)
            seen = drive if drive is not None else (d if d is not None else 1)
        for _ in range(self.half):                 # clock high (rising edge at the first)
            self.t.step(1, drive)
        return seen

    def write_bits(self, v, n):
        for i in range(n):
            self._cycle((v >> i) & 1)

    def read_bits(self, n):
        return sum(self._cycle(None) << i for i in range(n))

    def turn(self):
        self._cycle(None)

    def line_reset(self):
        self.write_bits((1 << 56) - 1, 56)

    def connect(self):
        self.line_reset()
        self.write_bits(swd.JTAG_TO_SWD, 16)
        self.line_reset()
        self.write_bits(0, 8)

    def request(self, apndp, rnw, a):
        a2, a3 = (a >> 2) & 1, (a >> 3) & 1
        par = apndp ^ rnw ^ a2 ^ a3
        return 1 | apndp << 1 | rnw << 2 | a2 << 3 | a3 << 4 | par << 5 | 0 << 6 | 1 << 7

    def read(self, apndp, a):
        self.write_bits(self.request(apndp, 1, a), 8)
        self.turn()
        ack = self.read_bits(3)
        if ack != swd.OK:
            self.turn()
            return ack, None
        v = self.read_bits(32)
        p = self.read_bits(1)
        self.turn()
        assert p == swd.parity(v)
        return ack, v

    def write(self, apndp, a, v):
        self.write_bits(self.request(apndp, 0, a), 8)
        self.turn()
        ack = self.read_bits(3)
        self.turn()
        if ack == swd.OK:
            self.write_bits(v, 32)
            self.write_bits(swd.parity(v), 1)
        return ack


def test_connect_and_dpidr():
    t = swd.Target(dpidr=0x0BC11477)
    h = Host(t)
    h.connect()
    assert ("swd_mode",) in t.log
    assert h.read(0, 0x0) == (swd.OK, 0x0BC11477)
    assert t.errors == []


def test_ap_write_then_posted_read():
    t = swd.Target()
    h = Host(t)
    h.connect()
    assert h.write(0, 0x8, 0x0000_0000) == swd.OK          # SELECT AP 0 bank 0
    assert h.write(1, 0x4, 0x2000_0000) == swd.OK          # AP 0x04 (TAR)
    assert h.read(1, 0x4)[0] == swd.OK                     # posted: returns the old RDBUFF
    assert h.read(0, 0xC) == (swd.OK, 0x2000_0000)         # RDBUFF: the AP value
    assert t.errors == []


def test_wait_then_ok():
    t = swd.Target()
    h = Host(t)
    h.connect()
    t.wait_next = 2
    assert h.write(1, 0x4, 5) == swd.WAIT
    assert h.write(1, 0x4, 5) == swd.WAIT
    assert h.write(1, 0x4, 5) == swd.OK
    assert t.errors == []


def test_fault_is_sticky_until_abort():
    t = swd.Target()
    h = Host(t)
    h.connect()
    t.fault_next = 1
    assert h.read(1, 0x0)[0] == swd.FAULT
    assert h.read(1, 0x0)[0] == swd.FAULT
    assert h.write(0, 0x0, 0x1E) == swd.OK                 # ABORT
    assert h.read(1, 0x0)[0] == swd.OK


def test_bad_parity_gets_no_answer():
    t = swd.Target()
    h = Host(t)
    h.connect()
    h.write_bits(h.request(0, 1, 0) ^ (1 << 5), 8)         # parity bit flipped
    h.turn()
    assert h.read_bits(3) == 0b111                          # nobody drives: the pull-up
    assert t.errors
