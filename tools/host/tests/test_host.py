"""tools/host: §9 frames, and the load sequence of every shipped program checked against the D-046 map with
a software register model (the RTL side is checked by test_internal/host and, later, the pin-level tests)."""

import pathlib

import pytest

import tripc
import tripwire_spec as S
from host import HM, Host, RegisterModel, frame_read, frame_write, load_sequence, port_word, slot_words
from host.host import LANES, PC_WORDS, UNITS, lane_addr

PROGRAMS = sorted((pathlib.Path(__file__).resolve().parents[3] / "programs").glob("*.trw"))
ACCESS = {"run", "step", "irq_en", "unit_flags", "slots", "ports", "dropped", "pin_cfg", "owners", "lanes",
          "host_in", "sram"}


def block_of(addr):
    for name, (base, n) in S.HOST_MAP.items():
        if base <= addr < base + n:
            return name
    return None


def test_frames():
    assert frame_write(0x2001, [0xBEEF, 0x0102]) == bytes([0x80, 0x20, 0x01, 0xBE, 0xEF, 0x01, 0x02])
    out, parse = frame_read(0x5004, 2)
    assert out == bytes([0x00, 0x50, 0x04, 0, 0, 0, 0, 0])
    assert parse(bytes([0xFF] * 4 + [0x12, 0x34, 0xAB, 0xCD])) == [0x1234, 0xABCD]


def test_encodings():
    w = (1 << 53) - 1
    assert slot_words(w) == [0xFFFF, 0xFFFF, 0xFFFF, 0x1F]
    assert port_word("L0.I1", "L1.O0", "tap", 0b0101) == 1 | 1 << 1 | 7 << 2 | 0b0101 << 6
    assert PC_WORDS == 22 and UNITS == 6 and LANES == 3


@pytest.mark.parametrize("path", PROGRAMS, ids=lambda p: p.stem)
def test_load_sequence_programs_every_register(path):
    """§14 H1: halt first; every unit block, all owners, all 13 ports, all 12 slots + K and r0-r3/STATE of
    each used lane, the SRAM; RUN last. Every address is a writable register of the map."""
    image, _ = tripc.compile_file(path)
    seq = load_sequence(image)
    assert seq[0] == (HM["run"], [0])
    used = sorted(int(n[1:]) for n in image["lanes"])
    assert seq[-1] == (HM["run"], [sum(1 << k for k in used)])
    m = RegisterModel()
    for addr, words in seq:
        for i in range(len(words)):
            assert block_of(addr + i) in ACCESS, hex(addr + i)
        m.write(addr, words)
    for k in used:
        lane = image["lanes"][f"L{k}"]
        want = [int(w, 16) for w in lane["slots"]] + [0] * (12 - len(lane["slots"]))
        assert [m.slot(k, s) for s in range(12)] == want
        assert [m.mem[HM["slots"] | k << 8 | 12 << 4 | i] for i in range(4)] == lane["k"]
        assert [m.mem[lane_addr(k, f"r{i}")] for i in range(4)] == lane["regs"]
        assert m.mem[lane_addr(k, "state")] == 0
    for u in range(UNITS):
        regs = [int(w, 16) for w in image["pin_regs"][f"U{u}"]][:PC_WORDS]
        assert [m.mem[HM["pin_cfg"] + 32 * u + i] for i in range(PC_WORDS)] == regs
    owners = {pad: m.mem.get(HM["owners"] + pad - 8) for pad in range(8, 24)}
    for pad, unit in image["own"]:
        assert owners[pad] == unit
    assert all(v in (None, 7) or (p, v) in map(tuple, image["own"]) for p, v in owners.items())
    conn = {c[0]: c for c in image["connect"]}
    for c, port in enumerate(S.FABRIC_CONSUMERS):
        v = m.mem[HM["ports"] + c]
        if port in conn:
            _, prod, mode, acc = conn[port]
            assert v & 1 and (v >> 2 & 15) == S.LEGAL_SOURCES[port].index(prod)
            assert (v >> 1 & 1) == (mode == "tap") and (v >> 6 & 15) == acc
        else:
            assert v == 0
    if image["routines"]:
        assert [m.mem[HM["sram"] + i] for i in range(len(image["sram"]))] == image["sram"]


class FakeChip:
    """Just enough of the chip's SPI side for the client: a byte-level decoder over a RegisterModel,
    with HOST_IN / HOST_OUT."""

    def __init__(self):
        self.m = RegisterModel()
        self.hin = None
        self.hout = [(2, 0x55AA)]

    def xfer(self, data):
        cmd, addr = data[0], data[1] << 8 | data[2]
        if cmd & 0x80:
            words = [data[i] << 8 | data[i + 1] for i in range(3, len(data), 2)]
            for i, w in enumerate(words):
                a = addr + i
                if HM["host_in"] <= a < HM["host_in"] + 4 and self.hin is None:
                    self.hin = (a & 3, w)
            self.m.write(addr, words)
            return bytes(len(data))
        n = (len(data) - 4) // 2
        out = []
        for i in range(n):
            a = addr + i
            if a == HM["host_status"]:
                v = (bool(self.hout)) << 15 | (self.hin is None) << 14 | (self.hout[0][0] if self.hout else 0)
            elif a == HM["host_out"]:
                v = self.hout.pop(0)[1] if self.hout else 0
            else:
                v = self.m.mem.get(a, 0)
            out += [v >> 8, v & 0xFF]
        return bytes(4) + bytes(out)


def test_client_push_pop_and_load():
    chip = FakeChip()
    h = Host(chip.xfer)
    assert h.push(0x1234, tag=1) and chip.hin == (1, 0x1234)
    assert not h.push(0x9999), "HOST_IN busy: the push must be refused"
    assert h.pop() == (2, 0x55AA) and h.pop() is None
    image, _ = tripc.compile_file(PROGRAMS[0])
    h.load(image)
    assert chip.m.run == sum(1 << int(n[1:]) for n in image["lanes"])
