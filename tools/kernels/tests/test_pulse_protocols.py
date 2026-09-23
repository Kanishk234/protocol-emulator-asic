"""L3-PULSE on the model: WS2812 and DShot programs against reference decoders (and sigrok for WS281x)."""

import re
import shutil
import subprocess

import pytest

from kernels import load_program
from protomodels import pulse
from tripsim import Chip
from tripsim.isa import TAG_DATA, TAG_EVENT
from tripsim.vcd import VcdRecorder


def run(chip, clocks, vcd=None):
    rec = VcdRecorder({"din": lambda c: c.outputs()[0] & 1}) if vcd else None
    if rec:
        chip.observers.append(rec)
    levels = []
    for _ in range(clocks):
        chip.step()
        levels.append(chip.outputs()[0] & 1)
    if rec:
        rec.write(vcd)
    return levels


FRAME1 = [0x00, 0xFF, 0x80, 0x12, 0x34, 0x56]       # two LEDs (G, R, B each)
FRAME2 = [0xA5, 0x5A, 0x0F]


def test_ws2812_two_frames(tmp_path):
    chip = Chip(lanes=1)
    load_program(chip, "ws2812")
    for b in FRAME1:
        chip.host_push(b, TAG_DATA)
    chip.host_push(0, TAG_EVENT)
    for b in FRAME2:
        chip.host_push(b, TAG_DATA)
    chip.host_push(0, TAG_EVENT)
    levels = run(chip, (len(FRAME1) + len(FRAME2)) * 8 * 63 + 2 * 3100 + 200, vcd=tmp_path / "ws.vcd")
    frames, errs = pulse.ws2812_decode(levels)
    assert errs == []                                   # every datasheet tolerance met
    assert frames == [FRAME1, FRAME2]
    if shutil.which("sigrok-cli"):
        out = subprocess.run(["sigrok-cli", "-i", str(tmp_path / "ws.vcd"), "-I", "vcd",
                              "-P", "rgb_led_ws281x:din=din", "-A", "rgb_led_ws281x=rgb"],
                             capture_output=True, text=True, check=True).stdout
        colours = re.findall(r"#([0-9a-fA-F]{6})", out)
        # sigrok shows each LED as #RRGGBB, reordered from the strip's G-R-B wire order
        leds = [FRAME1[0:3], FRAME1[3:6], FRAME2]
        expect = [bytes([g_r_b[1], g_r_b[0], g_r_b[2]]).hex() for g_r_b in leds]
        assert [c.lower() for c in colours] == expect


@pytest.mark.parametrize("rate", [150, 300, 600, 1200])
def test_dshot_frames_and_checksum(rate):
    values = [(0, 0), (48, 0), (1046, 1), (2047, 0), (1000, 1)]     # (throttle, telemetry)
    chip = Chip(lanes=1)
    load_program(chip, "dshot", RATE=rate)
    for t, tel in values:
        chip.host_push(t << 1 | tel)
    bit = 50000 // rate
    levels = run(chip, len(values) * (18 * bit + 200) + 500)
    frames, errs = pulse.dshot_decode(levels, bit)
    assert errs == []
    assert frames == [(t, tel, True) for t, tel in values]


def test_dshot_checksum_is_computed_by_the_lane():
    """Guard against a vacuous pass: a corrupted routine must produce bad checksums."""
    from tripc import compile_file, load
    from kernels import PROGRAMS
    src = (PROGRAMS / "dshot.trw").read_text().replace("AND r1, r1, 15", "AND r1, r1, 7")
    import tempfile, pathlib
    p = pathlib.Path(tempfile.mkdtemp()) / "dshot_bad.trw"
    p.write_text(src)
    image, _ = compile_file(p)
    chip = Chip(lanes=1)
    load(chip, image)
    v = 1000 << 1 | 0
    assert pulse.dshot_crc(v) & 0x8                    # premise: masking with 7 must change it
    chip.host_push(v)
    frames, _ = pulse.dshot_decode(run(chip, 18 * 83 + 600), 83)
    assert frames and frames[0][2] is False
