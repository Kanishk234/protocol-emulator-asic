"""L3-I2C-C on the model: I2C controller kernel against the reference target and sigrok."""

import re
import shutil
import subprocess

import pytest

from kernels import i2c_controller
from protomodels.i2c import I2CTarget
from tripsim import Chip
from tripsim.isa import TAG_CTRL, TAG_DATA, TAG_EVENT
from tripsim.vcd import VcdRecorder

SDA, SCL = 0, 1
ADDR = 0x50


def commands(chip):
    """START W(A0) W(01) W(02) STOP | START W(A2) STOP | START W(A0) W(05) rSTART W(A1) R R R STOP."""
    S, P = (0, TAG_EVENT), (0x8000, TAG_EVENT)
    W = lambda b: (b, TAG_DATA)
    R = lambda nack: (nack, TAG_CTRL)
    seq = [S, W(0xA0), W(0x01), W(0x02), P,
           S, W(0xA2), P,
           S, W(0xA0), W(0x05), S, W(0xA1), R(0), R(0), R(1), P]
    for data, tag in seq:
        chip.host_push(data, tag)


EXPECTED_HOST = [0, 0, 0,      # ACKs for A0, 01, 02
                 1,            # NACK for A2 (another device)
                 0, 0,         # ACKs for A0, 05
                 0,            # ACK for A1 (read)
                 0x11, 0x22, 0x33]


def run(period, stretch=0, vcd=None, max_clocks=400_000):
    chip = Chip(lanes=1)
    chip.settle_inputs(uio=0xFF)
    i2c_controller.load(chip, period, sda=SDA, scl=SCL)
    commands(chip)
    tgt = I2CTarget(ADDR, read_data=[0x11, 0x22, 0x33], stretch=stretch)
    rec = None
    if vcd:
        rec = VcdRecorder({"scl": lambda c: (c.uio_in >> SCL) & 1, "sda": lambda c: (c.uio_in >> SDA) & 1})
        chip.observers.append(rec)
    quiet = 0
    phases = {0: [], 1: []}                 # completed SCL low/high phase lengths on the bus
    prev_scl, run_len = 1, 0
    for _ in range(max_clocks):
        _, uio, oe = chip.outputs()
        ours_low = lambda bit: ((oe >> bit) & 1) and not ((uio >> bit) & 1)
        scl = int(tgt.scl and not ours_low(SCL))
        sda = int(tgt.sda and not ours_low(SDA))
        if scl != prev_scl:
            phases[prev_scl].append(run_len)
            prev_scl, run_len = scl, 0
        run_len += 1
        chip.uio_in = (0xFF & ~3) | (scl << SCL) | (sda << SDA)
        chip.step()
        tgt.step(scl, sda)
        done = len(chip.host_out) == len(EXPECTED_HOST) and tgt.log and tgt.log[-1] == ("STOP",)
        quiet = quiet + 1 if done else 0
        if quiet > 2 * period:
            break
    else:
        raise AssertionError(f"did not finish: host_out={list(chip.host_out)} log={tgt.log}")
    if rec:
        rec.write(vcd)
    chip.scl_phases = phases
    return chip, tgt


def check(chip, tgt, period):
    # bus timing oracle: every SCL low and high phase lasts >= PERIOD/2 (tLOW, tHIGH),
    # even when the target stretches (the first high phase is the idle bus before START)
    assert min(chip.scl_phases[0]) >= period // 2, f"tLOW {min(chip.scl_phases[0])}"
    assert min(chip.scl_phases[1][1:]) >= period // 2, f"tHIGH {min(chip.scl_phases[1][1:])}"
    assert [d for _, d in chip.host_out] == EXPECTED_HOST
    assert tgt.received == [0x01, 0x02, 0x05]
    assert [e for e in tgt.log if e[0] != "ADDR"] == [("START",), ("STOP",)] * 2 + [("START",), ("START",), ("STOP",)]
    assert [e[1:] for e in tgt.log if e[0] == "ADDR"] == [(0xA0, True), (0xA2, False), (0xA0, True), (0xA1, True)]
    assert all(u.stats["bad_tokens"] == 0 for u in chip.pins)


@pytest.mark.parametrize("stretch", [0, 40, "long"])      # "long": more than a whole SCL period
@pytest.mark.parametrize("period", [500, 124, 50])        # 100 kHz, ~400 kHz, 1 MHz
def test_i2c_controller(period, stretch):
    s = 2 * period + 7 if stretch == "long" else stretch
    check(*run(period, s), period)


@pytest.mark.skipif(shutil.which("sigrok-cli") is None, reason="sigrok-cli not installed")
def test_i2c_controller_sigrok(tmp_path):
    run(124, stretch=40, vcd=tmp_path / "i2cc.vcd")
    out = subprocess.run(["sigrok-cli", "-i", str(tmp_path / "i2cc.vcd"), "-I", "vcd",
                          "-P", "i2c:scl=scl:sda=sda", "-A", "i2c"],
                         capture_output=True, text=True, check=True).stdout
    lines = [ln.split(": ", 1)[1] for ln in out.splitlines() if ": " in ln]
    assert [int(m, 16) for m in re.findall(r"Data write: ([0-9A-F]{2})", out)] == [0x01, 0x02, 0x05]
    assert [int(m, 16) for m in re.findall(r"Data read: ([0-9A-F]{2})", out)] == [0x11, 0x22, 0x33]
    assert lines.count("Start") == 3 and lines.count("Start repeat") == 1 and lines.count("Stop") == 3
