"""L3-HDLC on the model: programs/hdlc.trw against the reference HDLC codec (ISO/IEC 13239)."""

import pytest

from kernels import load_program
from protomodels import hdlc
from tripsim import Chip
from tripsim.isa import TAG_DATA, TAG_ERR, TAG_EVENT

PERIOD = 50
FRAMES = [[0x03, 0x3F, 0x7E, 0xFF, 0x7D], [0xFF] * 6, [0x00, 0x01, 0x02]]


def make():
    chip = Chip(lanes=1)
    chip.settle_inputs(ui=1)
    load_program(chip, "hdlc")
    return chip


def host_frames(got):
    frames, cur = [], []
    for tag, d in got:
        if tag == TAG_DATA:
            cur.append(d)
        else:
            frames.append((cur[:-2], tag == TAG_EVENT, tag, d))
            cur = []
    return frames


def test_tx_frames_decode_and_loop_back():
    chip = make()
    chip.run_for(PERIOD * 12)                              # an idle (all-ones) line first
    for f in FRAMES:
        for b in f:
            chip.host_push(b)
        chip.host_push(0, tag=TAG_EVENT)
    line, got, delay = [], [], [1] * 3                     # loopback through a 3-clock wire
    for _ in range(PERIOD * 400):
        out = chip.outputs()[0] & 1
        delay.append(out)
        chip.ui_in = delay.pop(0)
        chip.step()
        line.append(out)
        while chip.host_out:
            got.append(chip.host_out.popleft())
    start = line.index(0) % PERIOD                         # the reference samples mid-bit
    bits = [line[k] for k in range(start + PERIOD // 2, len(line), PERIOD)]
    assert hdlc.decode(bits) == [(f, True) for f in FRAMES]
    assert [(d, ok) for d, ok, _, _ in host_frames(got)] == [(f, True) for f in FRAMES]


@pytest.mark.parametrize("drift", [1.0, 1.01, 0.99])       # the far end's clock ±1 %
def test_rx_frames_bad_fcs_and_abort(drift):
    frames = FRAMES + [[0x55, 0xAA], [0x7E, 0x7E, 0x7E, 0x7E]]
    line = hdlc.encode(frames, bad_fcs={2}, abort_after=(3, 1))
    chip = make()
    got, t = [], 0.0
    for b in line:
        n = round(t + PERIOD * drift) - round(t)
        t += PERIOD * drift
        for _ in range(n):
            chip.ui_in = b
            chip.step()
            while chip.host_out:
                got.append(chip.host_out.popleft())
    for _ in range(200):
        chip.step()
        while chip.host_out:
            got.append(chip.host_out.popleft())
    res = host_frames(got)
    assert [d for d, ok, _, _ in res if ok] == [FRAMES[0], FRAMES[1], [0x7E] * 4]
    assert res[2][2] == TAG_ERR and res[2][3] >> 12 == 0                # bad FCS
    assert res[3][2] == TAG_ERR and res[3][3] >> 12 == 2                # abort
    assert len(res) == 5
