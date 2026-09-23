"""L3-PS2 on the model: programs/ps2_host.trw against the reference PS/2 device and sigrok."""

import re
import shutil
import subprocess

from kernels import load_program
from protomodels.ps2 import PS2Device
from tripsim import Chip
from tripsim.isa import TAG_DATA, TAG_ERR
from tripsim.vcd import VcdRecorder

DATA, CLK = 0, 1
HALF = 1500                                # 16.7 kHz device clock


def run(dev, chip, clocks, vcd=None):
    rec = None
    if vcd:
        # sigrok 0.5's ps2 decoder only finishes a frame on a 12th CLK fall (off by one), so it would
        # take the next frame's start bit. The recorded clk gets a short extra low pulse (DATA idle high)
        # after each device frame so every frame is decoded on its own; the chip never sees it.
        mark = {"n": 0, "t": 0}
        def clk_sig(c):
            if dev.frames_sent > mark["n"]:
                mark["n"], mark["t"] = dev.frames_sent, 20
            if mark["t"]:
                mark["t"] -= 1
                return 0 if mark["t"] < 10 else (c.uio_in >> CLK) & 1
            return (c.uio_in >> CLK) & 1
        rec = VcdRecorder({"clk": clk_sig, "data": lambda c: (c.uio_in >> DATA) & 1})
        chip.observers.append(rec)
    for _ in range(clocks):
        _, uio, oe = chip.outputs()
        ours_low = lambda b: ((oe >> b) & 1) and not ((uio >> b) & 1)
        clk = int(dev.clk and not ours_low(CLK))
        data = int(dev.data and not ours_low(DATA))
        chip.uio_in = (0xFF & ~3) | (clk << CLK) | (data << DATA)
        chip.step()
        dev.step(clk, data)
    if rec:
        rec.write(vcd)


def make(send=(), bad_parity=()):
    chip = Chip(lanes=1)
    chip.settle_inputs(uio=0xFF)
    load_program(chip, "ps2_host")
    return chip, PS2Device(HALF, send=send, bad_parity=bad_parity)


def test_device_to_host_with_parity_error(tmp_path):
    chip, dev = make(send=[0x1C, 0xF0, 0x1C, 0x5A, 0x00, 0xFF], bad_parity={3})
    run(dev, chip, 6 * 11 * 2 * HALF + 6 * 5 * HALF + 2000, vcd=tmp_path / "ps2.vcd")
    got = list(chip.host_out)
    assert [d for t, d in got if t == TAG_DATA] == [0x1C, 0xF0, 0x1C, 0x00, 0xFF]
    errs = [d for t, d in got if t == TAG_ERR]
    assert len(errs) == 1 and (errs[0] >> 1) & 0xFF == 0x5A            # the frame with bad parity
    if shutil.which("sigrok-cli"):
        out = subprocess.run(["sigrok-cli", "-i", str(tmp_path / "ps2.vcd"), "-I", "vcd",
                              "-P", "ps2:clk=clk:data=data", "-A", "ps2"],
                             capture_output=True, text=True, check=True).stdout
        data = [int(h, 16) for h in re.findall(r"Data: ([0-9A-Fa-f]{2})\b", out)]
        assert data == [0x1C, 0xF0, 0x1C, 0x5A, 0x00, 0xFF]
        assert out.count("Parity error") == 1


def test_host_to_device():
    chip, dev = make()
    for b in (0xED, 0x02, 0xFF, 0x00):        # "set LEDs", LED mask, reset, a zero byte
        chip.host_push(b)
    run(dev, chip, 4 * (13 * 2 * HALF + 12_000))
    assert dev.received == [(b, True, True) for b in (0xED, 0x02, 0xFF, 0x00)]
    assert all(u.stats["bad_tokens"] == 0 for u in chip.pins)


def test_both_directions_interleaved():
    chip, dev = make(send=[0xFA, 0xAA])      # device: ACK, self-test passed
    chip.host_push(0xFF)                      # host: reset
    run(dev, chip, 3 * (13 * 2 * HALF + 12_000))
    assert dev.received == [(0xFF, True, True)]
    assert [d for t, d in chip.host_out if t == TAG_DATA] == [0xFA, 0xAA]
