"""L3-I2S on the model: programs/i2s.trw against the reference I2S receiver/ADC and sigrok's i2s."""

import re
import shutil
import subprocess

import pytest

from kernels import load_program
from protomodels.i2s import I2SADC, I2SReceiver
from tripsim import Chip
from tripsim.isa import TAG_EVENT
from tripsim.vcd import VcdRecorder

SAMPLES = [(0x1234, 0xABCD), (0x8000, 0x7FFF), (0x0001, 0xFFFE), (0x5A5A, 0xA5A5), (0, 0xFFFF)]


def run(fs, adc_samples=None, loopback=False, vcd=None):
    chip = Chip(lanes=1)
    load_program(chip, "i2s", FS=fs)
    for left, right in SAMPLES:
        chip.host_push(left)
        chip.host_push(right)
    rx, adc = I2SReceiver(), I2SADC(adc_samples or [])
    rec = None
    if vcd:
        rec = VcdRecorder({"sck": lambda c: c.outputs()[0] & 1, "ws": lambda c: c.outputs()[0] >> 2 & 1,
                           "sd": lambda c: c.outputs()[0] >> 1 & 1})
        chip.observers.append(rec)
    got = []
    for _ in range(round((len(SAMPLES) + 2) * 50e6 / fs)):
        uo = chip.outputs()[0]
        sck, sd, ws = uo & 1, uo >> 1 & 1, uo >> 2 & 1
        rx.step(sck, ws, sd)
        chip.ui_in = sd if loopback else adc.step(sck, ws)
        chip.step()
        while chip.host_out:
            got.append(chip.host_out.popleft())
    if rec:
        rec.write(vcd)
    return rx.words, got


@pytest.mark.parametrize("fs", [48000, 96000, 192000])    # BCLK 1.536 / 3.072 / 6.144 MHz
def test_i2s_out(fs, tmp_path):
    words, _ = run(fs, vcd=tmp_path / "i2s.vcd")
    expect = [w for pair in SAMPLES for w in zip("LR", pair)]
    assert [(c, w) for c, w, n in words] == expect[:len(words)] and len(words) >= len(expect) - 1
    assert all(n == 16 for _, _, n in words)
    if shutil.which("sigrok-cli"):
        out = subprocess.run(["sigrok-cli", "-i", str(tmp_path / "i2s.vcd"), "-I", "vcd",
                              "-P", "i2s:sck=sck:ws=ws:sd=sd", "-A", "i2s"],
                             capture_output=True, text=True, check=True).stdout
        dec = [(c[0], int(v, 16)) for c, v in re.findall(r"(Left|Right) channel: ([0-9a-f]{8})", out)]
        assert len(dec) >= len(expect) - 1 and dec == expect[:len(dec)], out
        # sigrok measures its first word from where it started counting (15 bits), so it warns
        # once about the second word; any other length warning would be a real error
        warns = re.findall(r"Received (\d+)-bit word, expected (\d+)-bit word", out)
        assert warns in ([], [("16", "15")]), out


def test_i2s_in_from_an_adc_and_loopback():
    adc = [(0x0102, 0x0304), (0x1111, 0x2222), (0xF00D, 0xBEEF), (0x7777, 0x8888)]
    _, got = run(48000, adc_samples=adc)
    words = [d for t, d in got if t == TAG_EVENT]
    # the ADC starts at the first WS change, i.e. with the first right word: the first left is 0
    expect = [0] + [w for pair in adc for w in pair][1:]
    assert words[:len(expect)] == expect and not any(words[len(expect):]), words   # then silence
    _, got = run(48000, loopback=True)
    words = [d for t, d in got if t == TAG_EVENT]
    sent = [w for pair in SAMPLES for w in pair]
    assert words == sent[:len(words)] and len(words) >= len(sent) - 1
