"""L3-I2C-T on the model: I2C target kernel (read + write) against the reference controller and sigrok."""

import re
import shutil
import subprocess

import pytest

from kernels import i2c_target
from protomodels.i2c import I2CController
from tripsim import Chip
from tripsim.vcd import VcdRecorder

ADDR = 0x50
SDA, SCL = 0, 1

READ_DATA = [0x11, 0x22, 0x33]
WRITTEN = [0x01, 0x02, 0xA5, 0xFF, 0x00]
EXPECTED_W = [(0xA0, True), (0x01, True), (0x02, True), (0xA5, True),
              (0xA2, False),                            # another device: NACKed, ignored
              (0xA1, True),                             # read from us
              (0xA0, True), (0xFF, True), (0x00, True),
              (0xA3, False)]                            # read from another device
EXPECTED_R = [(0x11, True), (0x22, True), (0x33, False)]  # controller NACKs the last byte


def run_bus(chip, ctrl, max_clocks=400_000, vcd=None):
    """Resolve the open-drain bus each clock between the controller and the chip."""
    rec = None
    if vcd:
        rec = VcdRecorder({"scl": lambda c: (c.uio_in >> SCL) & 1,
                           "sda": lambda c: (c.uio_in >> SDA) & 1})
        chip.observers.append(rec)
    for _ in range(max_clocks):
        _, uio_out, oe = chip.outputs()
        ours_low = lambda bit: ((oe >> bit) & 1) and not ((uio_out >> bit) & 1)
        scl = int(ctrl.scl and not ours_low(SCL))
        sda = int(ctrl.sda and not ours_low(SDA))
        chip.uio_in = (0xFF & ~((1 << SCL) | (1 << SDA))) | (scl << SCL) | (sda << SDA)
        chip.step()
        ctrl.step(scl, sda)
        if ctrl.done():
            break
    else:
        raise AssertionError("I2C transactions did not finish")
    if rec:
        rec.write(vcd)


def setup(cpb):
    chip = Chip(lanes=1)
    i2c_target.load(chip, ADDR, sda=SDA, scl=SCL)
    for b in READ_DATA + [0x44]:                        # 0x44 must stay unsent
        chip.host_push(b)
    ctrl = I2CController(clocks_per_bit=cpb)
    ctrl.write(ADDR, b"\x01\x02\xa5")
    ctrl.write(ADDR + 1, b"\x77")
    ctrl.read(ADDR, 3)
    ctrl.write(ADDR, b"\xff\x00")
    ctrl.read(ADDR + 1, 2)
    return chip, ctrl


def acks(ctrl):
    return [(b, a) for kind, *rest in ctrl.log if kind == "W" for b, a in [rest]]


def reads(ctrl):
    return [(b, a) for kind, *rest in ctrl.log if kind == "R" for b, a in [rest]]


def correct(chip, ctrl):
    return ([d for _, d in chip.host_out] == WRITTEN and acks(ctrl) == EXPECTED_W
            and reads(ctrl) == EXPECTED_R)


@pytest.mark.parametrize("khz", [100, 400, 1000])
def test_i2c_target_read_write(khz):
    chip, ctrl = setup(50_000 // khz)
    run_bus(chip, ctrl)
    assert [d for _, d in chip.host_out] == WRITTEN
    assert acks(ctrl) == EXPECTED_W
    assert reads(ctrl) == EXPECTED_R
    assert chip.pins[0].flags["OVERRUN"] == 0 and chip.pins[0].stats["bad_tokens"] == 0
    assert len(i2c_target.slots()) <= chip.lanes[0].nslots == 12


@pytest.mark.skipif(shutil.which("sigrok-cli") is None, reason="sigrok-cli not installed")
def test_i2c_target_sigrok(tmp_path):
    chip, ctrl = setup(125)                                          # 400 kHz
    run_bus(chip, ctrl, vcd=tmp_path / "i2c.vcd")
    out = subprocess.run(["sigrok-cli", "-i", str(tmp_path / "i2c.vcd"), "-I", "vcd",
                          "-P", "i2c:scl=scl:sda=sda", "-A", "i2c"],
                         capture_output=True, text=True, check=True).stdout
    lines = [ln.split(": ", 1)[1] for ln in out.splitlines() if ": " in ln]
    writes = [int(m, 16) for m in re.findall(r"Data write: ([0-9A-F]{2})", out)]
    rd = [int(m, 16) for m in re.findall(r"Data read: ([0-9A-F]{2})", out)]
    assert writes == WRITTEN                    # 0x77 never sent: its address was NACKed
    assert rd == READ_DATA
    assert lines.count("Start") == 5 and lines.count("Stop") == 5
    assert lines.count("ACK") == 10 and lines.count("NACK") == 3


def fastest_clocks_per_bit(lo=8, hi=60):
    """Smallest clocks-per-bit (fastest bus) at which the kernel still works."""
    best = None
    for cpb in range(hi, lo - 1, -2):
        chip, ctrl = setup(cpb)
        try:
            run_bus(chip, ctrl)
            ok = correct(chip, ctrl)
        except AssertionError:
            ok = False
        if not ok:
            break
        best = cpb
    return best


def test_i2c_target_speed_margin():
    """Fm+ (1 MHz) guarantees SCL high >= 260 ns = 13 clocks. Keep ~2x margin."""
    cpb = fastest_clocks_per_bit()
    assert cpb is not None and cpb <= 26, f"fastest working: {cpb} clocks/bit"
