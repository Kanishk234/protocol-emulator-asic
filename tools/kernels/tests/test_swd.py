"""L3-SWD on the model: programs/swd.trw against the reference SWD target and sigrok."""

import re
import shutil
import subprocess

import pytest

from kernels import load_program
from protomodels.swd import DPIDR, OK, WAIT, SWDTarget, parity
from tripsim import Chip
from tripsim.isa import TAG_DATA, TAG_EVENT
from tripsim.vcd import VcdRecorder

SWCLK_BIT, SWDIO_BIT = 0, 0             # uo0, uio0


def request(apndp, rnw, addr):
    a2, a3 = (addr >> 2) & 1, (addr >> 3) & 1
    req = 1 | apndp << 1 | rnw << 2 | a2 << 3 | a3 << 4 | (apndp ^ rnw ^ a2 ^ a3) << 5 | 1 << 7
    return 0x7000 | req


def push_read(chip, apndp, addr):
    chip.host_push(request(apndp, 1, addr))


def push_write(chip, apndp, addr, v):
    chip.host_push(request(apndp, 0, addr))
    chip.host_push(0xB000 | (v & 0xFFF))
    chip.host_push(0xB000 | ((v >> 12) & 0xFFF))
    chip.host_push(0x8000 | parity(v) << 8 | (v >> 24), tag=TAG_EVENT)


class Bus:
    def __init__(self, chip, tgt, rec=None):
        self.chip, self.tgt, self.contention = chip, tgt, 0

    def run(self, clocks):
        chip, tgt = self.chip, self.tgt
        for _ in range(clocks):
            uo, uio, oe = chip.outputs()
            host_oe = (oe >> SWDIO_BIT) & 1
            if host_oe and tgt.oe:
                self.contention += 1
            dio = ((uio >> SWDIO_BIT) & 1) if host_oe else (tgt.value if tgt.oe else 1)   # pull-up
            chip.uio_in = (0xFF & ~1) | dio
            chip.step()
            tgt.step((uo >> SWCLK_BIT) & 1, dio)


def make(period, **kw):
    chip = Chip(lanes=1)
    chip.settle_inputs(uio=0xFF)
    load_program(chip, "swd", PERIOD=period)
    return chip, SWDTarget(**kw)


def host_words(chip):
    return [d for t, d in chip.host_out if t == TAG_DATA]


def read_result(words):
    ack_word, lo, hi, par = words
    v = lo | hi << 16
    return ack_word, v, (par & 1) == parity(v)


@pytest.mark.parametrize("period", [50, 20, 10, 6])   # 1, 2.5, 5, 8.3 MHz SWCLK (period 5 fails: see PROTOCOL_SUPPORT)
def test_dpidr_read_and_ap_write_read(period, tmp_path):
    chip, tgt = make(period)
    rec = VcdRecorder({"swclk": lambda c: c.outputs()[0] & 1, "swdio": lambda c: c.uio_in & 1})
    chip.observers.append(rec)
    bus = Bus(chip, tgt)
    push_read(chip, 0, 0x0)                             # DPIDR
    push_write(chip, 0, 0x8, 0x000000F0)                # SELECT: AP bank 0xF
    push_write(chip, 1, 0x4, 0xDEADBEEF)                # AP[0xF4] (e.g. TAR)
    push_read(chip, 1, 0x4)                             # posted AP read
    push_read(chip, 0, 0xC)                             # RDBUFF
    bus.run(6 * 60 * period + 2000)
    rec.write(tmp_path / "swd.vcd")
    w = host_words(chip)
    assert bus.contention == 0
    assert tgt.protocol_errors == 0
    assert read_result(w[0:4]) == (OK, DPIDR, True)
    assert w[4] == OK and w[5] == OK                                # the two writes
    assert read_result(w[6:10])[0] == OK                           # posted: previous AP read
    assert read_result(w[10:14]) == (OK, 0xDEADBEEF, True)
    assert len(w) == 14
    assert tgt.ap[(0xF0, 0x4)] == 0xDEADBEEF and all(e[5] for e in tgt.log)
    if shutil.which("sigrok-cli"):
        out = subprocess.run(["sigrok-cli", "-i", str(tmp_path / "swd.vcd"), "-I", "vcd",
                              "-P", "swd:swclk=swclk:swdio=swdio", "-A", "swd"],
                             capture_output=True, text=True, check=True).stdout
        assert out.count("OK") == 5, out
        data = [int(h, 16) for h in re.findall(r"0x([0-9a-f]{8})", out)]
        assert data == [DPIDR, 0xF0, 0xDEADBEEF, 0, 0xDEADBEEF], out
        assert "IDCODE" in out and "W SELECT" in out and "RDBUFF" in out


def test_wait_ack_then_retry():
    chip, tgt = make(20, wait_on={0})
    bus = Bus(chip, tgt)
    push_read(chip, 0, 0x0)                             # answered WAIT: no data phase
    push_read(chip, 0, 0x0)                             # retry
    bus.run(3 * 60 * 20 + 2000)
    w = host_words(chip)
    assert w[0] == WAIT
    assert read_result(w[1:5]) == (OK, DPIDR, True)
    assert bus.contention == 0 and tgt.protocol_errors == 0
