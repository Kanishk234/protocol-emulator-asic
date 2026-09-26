import pytest
from hypothesis import given, settings, strategies as st

from refmodels.i2c import Event, Target, decode, wired_and


class TextbookController:
    """An I2C controller written directly from the bus rules (for model tests only).
    Each phase lasts `q` clocks; SCL high phases wait while a target stretches the clock."""

    def __init__(self, target, q=4):
        self.t, self.q = target, q
        self.sda_c = self.scl_c = 1
        self.sda_t = self.scl_t = 1
        self.sda, self.scl = [], []

    def bus(self):
        return wired_and(self.sda_c, self.sda_t), wired_and(self.scl_c, self.scl_t)

    def tick(self, n=1):
        for _ in range(n):
            s, c = self.bus()
            self.sda.append(s)
            self.scl.append(c)
            self.sda_t, self.scl_t = self.t.step(s, c)

    def scl_high(self):
        """Release SCL, wait until it is really high (stretching), keep it high q clocks.
        Returns SDA sampled at the end of the high phase."""
        self.scl_c = 1
        self.tick()
        while self.bus()[1] == 0:
            self.tick()
        self.tick(self.q - 1)
        return self.bus()[0]

    def start(self):
        if self.bus()[1] == 0:           # repeated START: release SDA, then SCL
            self.sda_c = 1
            self.tick(self.q)
            self.scl_high()
        self.sda_c = 0
        self.tick(self.q)
        self.scl_c = 0
        self.tick(self.q)

    def bit_out(self, b):
        self.sda_c = b
        self.tick(self.q)
        v = self.scl_high()
        self.scl_c = 0
        self.tick(1)
        return v

    def write(self, byte):
        for k in range(8):
            self.bit_out((byte >> (7 - k)) & 1)
        return self.bit_out(1) == 0      # released SDA; ACK if the target pulls it low

    def read(self, ack):
        v = 0
        for _ in range(8):
            v = (v << 1) | self.bit_out(1)
        self.bit_out(0 if ack else 1)
        return v

    def stop(self):
        self.sda_c = 0
        self.tick(self.q)
        self.scl_high()
        self.sda_c = 1
        self.tick(2 * self.q)


def write_regs(c, addr, ptr, data):
    c.start()
    acks = [c.write(addr << 1), c.write(ptr)] + [c.write(d) for d in data]
    c.stop()
    return acks


def read_regs(c, addr, ptr, n):
    c.start()
    acks = [c.write(addr << 1), c.write(ptr)]
    c.start()                           # repeated START
    acks.append(c.write((addr << 1) | 1))
    data = [c.read(ack=(k != n - 1)) for k in range(n)]
    c.stop()
    return acks, data


def test_write_then_read_back():
    t = Target(0x42)
    c = TextbookController(t)
    assert write_regs(c, 0x42, 3, [0xDE, 0xAD]) == [True] * 4
    assert t.regs == {3: 0xDE, 4: 0xAD}
    acks, data = read_regs(c, 0x42, 3, 2)
    assert acks == [True] * 3 and data == [0xDE, 0xAD]
    ev = decode(c.sda, c.scl)
    kinds = [e.kind for e in ev]
    assert kinds.count("start") == 2 and kinds.count("restart") == 1 and kinds.count("stop") == 2
    assert ev[1] == Event("byte", 0x84, True)


def test_wrong_address_nacks_and_ignores():
    t = Target(0x42)
    c = TextbookController(t)
    assert write_regs(c, 0x43, 0, [0x55]) == [False, False, False]
    assert t.regs == {}


def test_nack_on_data_byte():
    t = Target(0x10, nack_after=2)
    c = TextbookController(t)
    # byte 1 after the address is the register pointer; byte 2 (0x01) is NACKed, the rest ignored
    assert write_regs(c, 0x10, 0, [0x01, 0x02, 0x03]) == [True, True, False, False, False]


def test_last_read_byte_is_nacked_by_controller():
    t = Target(0x21, regs={0: 0x11, 1: 0x22, 2: 0x33})
    c = TextbookController(t)
    _, data = read_regs(c, 0x21, 0, 3)
    assert data == [0x11, 0x22, 0x33]
    ev = [e for e in decode(c.sda, c.scl) if e.kind == "byte"]
    assert [e.ack for e in ev[-3:]] == [True, True, False]


@settings(max_examples=40)
@given(st.integers(0x08, 0x77), st.integers(0, 12),
       st.lists(st.integers(0, 255), min_size=1, max_size=3),
       st.integers(0, 9), st.integers(2, 6))
def test_roundtrip_with_stretching(addr, ptr, data, stretch, q):
    t = Target(addr, stretch=stretch)
    c = TextbookController(t, q=q)
    assert all(write_regs(c, addr, ptr, data))
    acks, back = read_regs(c, addr, ptr, len(data))
    assert all(acks) and back == data
    if stretch:
        # the target really held SCL low while the controller had released it
        assert any(c.scl[i] == 0 for i in range(len(c.scl)))


# --- the generator-based reference controller (refmodels.i2c.Controller) against the model target
from refmodels.i2c import run_bus  # noqa: E402


def ops_write(addr, ptr, data):
    return [("start",), ("write", addr << 1), ("write", ptr)] + [("write", d) for d in data] + [("stop",)]


def ops_read(addr, ptr, n):
    return ([("start",), ("write", addr << 1), ("write", ptr), ("start",), ("write", (addr << 1) | 1)]
            + [("read", k != n - 1) for k in range(n)] + [("stop",)])


def test_controller_model_write_read():
    t = Target(0x3A)
    c, sda, scl = run_bus(ops_write(0x3A, 2, [9, 8, 7]) + ops_read(0x3A, 2, 3), [t])
    assert t.regs == {2: 9, 3: 8, 4: 7}
    assert c.results == [True] * 5 + [True] * 3 + [9, 8, 7]
    kinds = [e.kind for e in decode(sda, scl) if e.kind != "byte"]
    assert kinds == ["start", "stop", "start", "restart", "stop"]


@settings(max_examples=30)
@given(st.integers(0, 12), st.integers(2, 6))
def test_controller_model_honours_stretching(stretch, q):
    t = Target(0x50, stretch=stretch)
    c, _, _ = run_bus(ops_write(0x50, 0, [0xA5]) + ops_read(0x50, 0, 1), [t], q=q)
    assert c.results[-1] == 0xA5
