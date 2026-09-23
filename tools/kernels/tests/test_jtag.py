"""L3-JTAG on the model: programs/jtag.trw against the reference TAP and sigrok."""

import re
import shutil
import subprocess

import pytest

from kernels import load_program
from protomodels.jtag import BYPASS, IDCODE, USER, JTAGTarget
from tripsim import Chip
from tripsim.isa import TAG_DATA, TAG_EVENT
from tripsim.vcd import VcdRecorder

TCK, TMS, TDI = 0, 1, 2                 # uo bits; TDO = ui0


class Host:
    """The host side of the scan engine: splits (TMS, TDI) bit lists into chunks of <= 12."""

    def __init__(self, chip, tap):
        self.chip, self.tap, self.lens = chip, tap, []

    def seq(self, tms, tdi=None):
        tdi = tdi or [0] * len(tms)
        for i in range(0, len(tms), 12):
            m, d = tms[i:i + 12], tdi[i:i + 12]
            n = len(m)
            self.chip.host_push((n - 1) << 12 | sum(b << k for k, b in enumerate(m)), tag=TAG_EVENT)
            self.chip.host_push((n - 1) << 12 | sum(b << k for k, b in enumerate(d)), tag=TAG_DATA)
            self.lens.append(n)

    def reset(self):
        self.seq([1, 1, 1, 1, 1, 0])                                    # to Run-Test/Idle

    def ir(self, code):                                                 # from and back to RTI
        self.seq([1, 1, 0, 0] + [0, 0, 0, 1] + [1, 0], [0] * 4 + [(code >> i) & 1 for i in range(4)] + [0, 0])

    def dr(self, value, n=32):
        bits = [(value >> i) & 1 for i in range(n)]
        self.seq([1, 0, 0] + [0] * (n - 1) + [1] + [1, 0], [0] * 3 + bits + [0, 0])

    def run(self, clocks):
        chip, tap = self.chip, self.tap
        for _ in range(clocks):
            uo = chip.outputs()[0]
            tdo = tap.step(uo >> TCK & 1, uo >> TMS & 1, uo >> TDI & 1)
            chip.ui_in = tdo
            chip.step()

    def tdo_bits(self):
        words = [d for t, d in self.chip.host_out if t == TAG_EVENT]
        assert len(words) == len(self.lens)
        return [(w >> k) & 1 for w, n in zip(words, self.lens) for k in range(n)]


def value(bits):
    return sum(b << i for i, b in enumerate(bits))


def make(period):
    chip = Chip(lanes=1)
    load_program(chip, "jtag", PERIOD=period)
    return chip, JTAGTarget()


@pytest.mark.parametrize("period", [50, 20, 10])       # 1, 2.5, 5 MHz TCK
def test_idcode_user_register_and_bypass(period, tmp_path):
    chip, tap = make(period)
    rec = VcdRecorder({"tck": lambda c: c.outputs()[0] & 1, "tms": lambda c: c.outputs()[0] >> 1 & 1,
                       "tdi": lambda c: c.outputs()[0] >> 2 & 1, "tdo": lambda c: c.ui_in & 1})
    chip.observers.append(rec)
    h = Host(chip, tap)
    h.reset()                                     # bits [0, 6)
    h.dr(0)                                       # IDCODE after reset: bits [6, 43)
    h.ir(USER)                                    # [43, 53)
    h.dr(0xCAFEF00D)                              # [53, 90)
    h.dr(0x12345678)                              # [90, 127): reads back 0xCAFEF00D
    h.ir(BYPASS)                                  # [127, 137)
    h.dr(0b1011, n=4)                             # [137, 146): 1-bit register delays TDI by one
    h.run(160 * period * 3 + 5000)
    rec.write(tmp_path / "jtag.vcd")
    t = h.tdo_bits()
    assert value(t[9:41]) == tap.idcode           # the 32 bits shifted in Shift-DR
    assert value(t[93:125]) == 0xCAFEF00D
    assert t[140:144] == [0, 1, 1, 0]             # BYPASS: captured 0, then TDI 1,1,0 delayed
    assert tap.user == 0x12345678 and tap.state == "RTI" and tap.ir == BYPASS
    if shutil.which("sigrok-cli"):
        out = subprocess.run(["sigrok-cli", "-i", str(tmp_path / "jtag.vcd"), "-I", "vcd",
                              "-P", "jtag:tdi=tdi:tdo=tdo:tck=tck:tms=tms", "-A", "jtag=bitstring-tdo"],
                             capture_output=True, text=True, check=True).stdout
        tdo_dr = [int(b, 2) for b in re.findall(r"TDO: ([01]{32})\b", out)]
        assert tap.idcode in tdo_dr and 0xCAFEF00D in tdo_dr, out
