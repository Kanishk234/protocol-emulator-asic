"""L3-I2C-T on the model: I2C target kernel against the reference controller and sigrok."""

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


def run_bus(chip, ctrl, max_clocks=200_000, vcd=None):
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


def transactions(ctrl):
    ctrl.write(ADDR, b"\x01\x02\xa5")
    ctrl.write(ADDR + 1, b"\x77")          # another device: must be NACKed and ignored
    ctrl.write(ADDR, b"\xff\x00")


def acks(ctrl):
    return [(b, a) for kind, *rest in ctrl.log if kind == "W" for b, a in [rest]]


@pytest.mark.parametrize("khz", [100, 400, 1000])
def test_i2c_target_write(khz):
    chip = Chip(lanes=1)
    i2c_target.load(chip, ADDR, sda=SDA, scl=SCL)
    ctrl = I2CController(clocks_per_bit=50_000 // khz)
    transactions(ctrl)
    run_bus(chip, ctrl)
    assert [d for _, d in chip.host_out] == [0x01, 0x02, 0xA5, 0xFF, 0x00]
    assert acks(ctrl) == [(0xA0, True), (0x01, True), (0x02, True), (0xA5, True),
                          (0xA2, False),
                          (0xA0, True), (0xFF, True), (0x00, True)]
    assert chip.pins[0].flags["OVERRUN"] == 0


@pytest.mark.skipif(shutil.which("sigrok-cli") is None, reason="sigrok-cli not installed")
def test_i2c_target_sigrok(tmp_path):
    chip = Chip(lanes=1)
    i2c_target.load(chip, ADDR, sda=SDA, scl=SCL)
    ctrl = I2CController(clocks_per_bit=125)                     # 400 kHz
    transactions(ctrl)
    run_bus(chip, ctrl, vcd=tmp_path / "i2c.vcd")
    out = subprocess.run(["sigrok-cli", "-i", str(tmp_path / "i2c.vcd"), "-I", "vcd",
                          "-P", "i2c:scl=scl:sda=sda", "-A", "i2c"],
                         capture_output=True, text=True, check=True).stdout
    lines = [ln.split(": ", 1)[1] for ln in out.splitlines() if ": " in ln]
    writes = [int(m, 16) for m in re.findall(r"Data write: ([0-9A-F]{2})", out)]
    assert writes == [0x01, 0x02, 0xA5, 0xFF, 0x00]    # 0x77 never sent: its address was NACKed
    assert lines.count("Start") == 3 and lines.count("Stop") == 3
    assert lines.count("NACK") == 1 and lines.count("ACK") == 7


def fastest_clocks_per_bit(lo=8, hi=60):
    """Smallest clocks-per-bit (fastest bus) at which the kernel still works."""
    best = None
    for cpb in range(hi, lo - 1, -2):
        chip = Chip(lanes=1)
        i2c_target.load(chip, ADDR, sda=SDA, scl=SCL)
        ctrl = I2CController(clocks_per_bit=cpb)
        transactions(ctrl)
        try:
            run_bus(chip, ctrl)
            ok = ([d for _, d in chip.host_out] == [0x01, 0x02, 0xA5, 0xFF, 0x00]
                  and [a for _, a in acks(ctrl)] == [True] * 4 + [False] + [True] * 3)
        except AssertionError:
            ok = False
        if not ok:
            break
        best = cpb
    return best


def test_i2c_target_speed_margin():
    """Fm+ (1 MHz) guarantees SCL high >= 260 ns = 13 clocks. The ACK path (queued 7 clocks
    after the 8th SCL rise, due 2 clocks after the fall) needs about 6: keep ~2x margin."""
    cpb = fastest_clocks_per_bit()
    assert cpb is not None and cpb <= 26, f"fastest working: {cpb} clocks/bit"
