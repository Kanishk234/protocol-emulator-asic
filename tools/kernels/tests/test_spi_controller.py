"""L3-SPI-C on the model: SPI controller kernel against the reference target and sigrok."""

import re
import shutil
import subprocess

import pytest

from kernels import spi_controller
from protomodels.spi import SPITarget
from tripsim import Chip
from tripsim.vcd import VcdRecorder

SCK, MOSI, CS, MISO = 0, 1, 2, 0
DATA = [0x01, 0x80, 0xFF, 0x3C, 0x00, 0x5A]


def run(period, data=DATA, vcd=None, max_clocks=100_000):
    chip = Chip(lanes=1)
    spi_controller.load(chip, period, sck=SCK, mosi=MOSI, cs=CS, miso=MISO)
    spi_controller.push_transfer(chip, data)
    tgt = SPITarget(first=0xA5)
    pads = lambda c: ((c.outputs()[0] >> SCK) & 1, (c.outputs()[0] >> MOSI) & 1,
                      (c.outputs()[0] >> CS) & 1)
    rec = None
    if vcd:
        rec = VcdRecorder({"sck": lambda c: pads(c)[0], "mosi": lambda c: pads(c)[1],
                           "cs": lambda c: pads(c)[2], "miso": lambda c: c.ui_in & 1})
        chip.observers.append(rec)
    t = 0
    for t in range(max_clocks):
        chip.ui_in = tgt.step(*pads(chip)) << MISO
        chip.step()
        if len(chip.host_out) == len(data) and pads(chip)[2] == 1 and t > 50:
            break
    if rec:
        rec.write(vcd)
    return chip, tgt, t


@pytest.mark.parametrize("period", [50, 10, 6])          # 1 MHz, 5 MHz, 8.3 MHz SCK
def test_spi_controller_mode0(period):
    chip, tgt, _ = run(period)
    assert tgt.received == DATA
    assert [d for _, d in chip.host_out] == [0xA5] + DATA[:-1]
    assert all(u.stats["bad_tokens"] == 0 for u in chip.pins), "a unit got tokens it cannot use"


@pytest.mark.skipif(shutil.which("sigrok-cli") is None, reason="sigrok-cli not installed")
def test_spi_controller_sigrok(tmp_path):
    run(10, vcd=tmp_path / "spi.vcd")
    got = {}
    for cls in ("mosi-data", "miso-data"):
        out = subprocess.run(["sigrok-cli", "-i", str(tmp_path / "spi.vcd"), "-I", "vcd",
                              "-P", "spi:clk=sck:mosi=mosi:miso=miso:cs=cs",
                              "-A", f"spi={cls}"], capture_output=True, text=True, check=True).stdout
        got[cls] = [int(h, 16) for h in re.findall(r"spi-\d+: ([0-9A-F]{2})\b", out)]
    assert got["mosi-data"] == DATA
    assert got["miso-data"] == [0xA5] + DATA[:-1]


def fastest_period(lo=2, hi=12):
    best = None
    for p in range(hi, lo - 1, -1):
        chip, tgt, _ = run(p)
        if tgt.received != DATA or [d for _, d in chip.host_out] != [0xA5] + DATA[:-1]:
            break
        best = p
    return best


def test_spi_controller_speed_and_throughput():
    """Record the fastest SCK and the byte rate; 4 clocks/bit (12.5 MHz) must work."""
    p = fastest_period()
    assert p is not None and p <= 4, f"fastest SCK period: {p} clocks"
