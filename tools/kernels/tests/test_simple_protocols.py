"""L3 on the model: MIDI (uart.trw at 31250 baud), DMX512, servo PWM and IR NEC, against
reference models written from their specs, and sigrok's midi, dmx512, pwm and ir_nec decoders."""

import re
import shutil
import subprocess

import pytest

from kernels import load_program
from protomodels import dmx, nec, uart
from tripsim import Chip
from tripsim.isa import TAG_DATA, TAG_ERR, TAG_EVENT
from tripsim.vcd import VcdRecorder

SIGROK = shutil.which("sigrok-cli")


def sigrok(path, decoder, annotations):
    return subprocess.run(["sigrok-cli", "-i", str(path), "-I", "vcd", "-P", decoder, "-A", annotations],
                          capture_output=True, text=True, check=True).stdout


def run_tx(chip, clocks, bit=0, rec_name=None):
    line = []
    rec = None
    if rec_name:
        rec = VcdRecorder({rec_name: lambda c: (c.outputs()[0] >> bit) & 1})
        chip.observers.append(rec)
    for _ in range(clocks):
        chip.step()
        line.append((chip.outputs()[0] >> bit) & 1)
    return line, rec


# ------------------------------------------------------------------ MIDI
MIDI = bytes([0x90, 60, 100, 0x80, 60, 0, 0xB0, 7, 127, 0xC5, 12])      # note on/off, CC, program


def test_midi_tx_is_uart_at_31250(tmp_path):
    chip = Chip(lanes=1)
    load_program(chip, "uart", BAUD=31250)
    for b in MIDI:
        chip.host_push(b)
    line, rec = run_tx(chip, round((len(MIDI) * 10 + 10) * 1600), rec_name="midi")
    assert uart.decode(line, 1600) == [(b, True) for b in MIDI]
    if SIGROK:
        rec.write(tmp_path / "midi.vcd")
        out = sigrok(tmp_path / "midi.vcd", "uart:rx=midi:baudrate=31250,midi", "midi")
        assert "note on (note = 60 'C4', velocity = 100)" in out, out
        assert "note off (note = 60 'C4'" in out and "control change" in out, out
        assert "Channel 6: program change to instrument 13" in out, out       # program 12, 1-based


def test_midi_rx_is_uart_at_31250():
    chip = Chip(lanes=1)
    chip.settle_inputs(ui=1)
    load_program(chip, "uart", BAUD=31250)
    wave = uart.encode(MIDI, 1600)
    it = iter(wave)
    chip.run_for(len(wave), env=lambda c: setattr(c, "ui_in", next(it)))
    assert bytes(d for t, d in chip.host_out if t == TAG_DATA) == MIDI


# ------------------------------------------------------------------ DMX512
@pytest.mark.parametrize("stops,mtbp", [(2, 0), (3, 20)])   # marks between frames / before BREAK
def test_dmx_tx_packets(stops, mtbp, tmp_path):
    chip = Chip(lanes=1)
    load_program(chip, "dmx", STOPS=stops, MTBP=mtbp)
    packets = [[0, 255, 128, 0, 17, 42], [0] + list(range(1, 25))]
    for slots in packets:
        chip.host_push(0, tag=TAG_EVENT)
        for b in slots:
            chip.host_push(b)
    total = sum(150 * 50 + len(p) * (9 + stops) * 200 for p in packets) + 20_000
    line, rec = run_tx(chip, total, rec_name="dmx")
    got = dmx.decode(line)
    assert [s for _, _, s in got] == packets
    assert all(brk >= 88 and mab >= 8 for brk, mab, _ in got)
    # sigrok's dmx512 decoder takes its last sample exactly at the end of the 2nd stop bit, so
    # back-to-back frames or a BREAK right after a stop bit (both legal: MTBF and MTBP may be 0)
    # misalign it; it is checked with a 4 us MTBF and a 20 us MTBP
    if SIGROK and stops == 3:
        rec.write(tmp_path / "dmx.vcd")
        out = sigrok(tmp_path / "dmx.vcd", "dmx512:dmx=dmx", "dmx512")
        # this sigrok version only looks for the next BREAK after 512 slots (a stop-bit error at
        # bit 10 is overridden by "next frame" in the same step), so it checks the first packet
        first = out[:out.index("Invalid")] if "Invalid" in out else out
        assert first.count("Break") == 1 and "MAB" in first, out
        vals = [int(v) for v in re.findall(r"dmx512-1: (\d+) / 0x", first)]    # start code, then slots
        assert vals == packets[0], out


def test_dmx_rx_break_and_slots():
    chip = Chip(lanes=1)
    chip.settle_inputs(ui=1)
    load_program(chip, "dmx")
    packets = [[0, 1, 2, 3], [0, 250, 251]]
    wave = dmx.encode(packets)
    it = iter(wave)
    chip.run_for(len(wave), env=lambda c: setattr(c, "ui_in", next(it)))
    got = list(chip.host_out)
    assert got == ([(TAG_ERR, 0)] + [(TAG_DATA, b) for b in packets[0]]
                   + [(TAG_ERR, 0)] + [(TAG_DATA, b) for b in packets[1]])


# ------------------------------------------------------------------ servo
def pulses(line):
    """[(rise_clock, high_clocks)] of a digital waveform."""
    out, i = [], 1
    while i < len(line):
        if line[i] and not line[i - 1]:
            j = i
            while j < len(line) and line[j]:
                j += 1
            out.append((i, j - i))
            i = j
        i += 1
    return out


@pytest.mark.slow  # ~3 min: nine 20 ms frames, clock by clock
def test_servo_widths_and_period(tmp_path):
    chip = Chip(lanes=1)
    load_program(chip, "servo")
    line, rec = run_tx(chip, 3 * 1_000_000, rec_name="pwm")                 # 3 frames at 1500 us
    chip.host_push(1000)
    more, _ = run_tx(chip, 3 * 1_000_000)
    chip.host_push(2000)
    more2, _ = run_tx(chip, 3 * 1_000_000)
    p = pulses(line + more + more2)[:-1]                                   # the last may be cut off
    widths = [w for _, w in p]
    assert widths[:3] == [1500 * 50] * 3
    assert 1000 * 50 in widths and widths[-1] == 2000 * 50
    periods = {b[0] - a[0] for a, b in zip(p, p[1:])}
    assert periods == {1_000_000}                                          # exactly 20 ms, every frame
    if SIGROK:
        rec.write(tmp_path / "pwm.vcd")
        out = sigrok(tmp_path / "pwm.vcd", "pwm:data=pwm", "pwm=duty-cycle")
        duty = [float(x) for x in re.findall(r"([\d.]+)%", out)]
        runs = [d for i, d in enumerate(duty) if i == 0 or d != duty[i - 1]]
        assert runs == [7.5, 5.0, 10.0], out                              # 1.5, 1.0, 2.0 ms of 20 ms


# ------------------------------------------------------------------ IR NEC
CARRIER = 50e6 / 38000


@pytest.mark.slow  # ~5 min: two 108 ms frame periods
def test_ir_nec_tx_carrier_and_frames(tmp_path):
    chip = Chip(lanes=2)
    load_program(chip, "ir_nec")
    chip.host_push(0x04 | 0x08 << 8)                    # address 0x04, command 0x08
    chip.host_push(0xA5 | 0x3C << 8)
    line, rec = run_tx(chip, 2 * 110 * 1000 * 50, rec_name="ir")         # two 108 ms frame periods
    frames, marks = nec.decode_modulated(line, CARRIER)
    assert frames == [(0x04, 0x08), (0xA5, 0x3C)]
    bit_marks = [l for _, l in marks if l < 1000 * 50]
    assert all(abs(l - nec.MARK) <= CARRIER for l in bit_marks)           # within one carrier cycle
    leaders = [s for s, l in marks if l > 8000 * 50]
    assert len(leaders) == 2 and leaders[1] - leaders[0] == 108 * 1000 * 50      # 108 ms period
    edges = [i for i in range(1, len(line)) if line[i] and not line[i - 1]]
    periods = [b - a for a, b in zip(edges, edges[1:]) if b - a < 2 * CARRIER]
    assert abs(sum(periods) / len(periods) - CARRIER) < 1                  # 38 kHz
    if SIGROK:
        rec.write(tmp_path / "ir.vcd")
        out = sigrok(tmp_path / "ir.vcd", "ir_nec:ir=ir:polarity=active-high:cd_freq=38000", "ir_nec")
        assert "Address: 0x04" in out and "Command: 0x08" in out, out
        assert "Address: 0xA5" in out and "Command: 0x3C" in out, out


@pytest.mark.slow  # ~3.5 min
def test_ir_nec_rx_frames_and_repeat():
    chip = Chip(lanes=2)
    chip.settle_inputs(ui=1)
    load_program(chip, "ir_nec")
    wave = nec.envelope(0x10, 0xEF, repeats=2) + nec.envelope(0x80, 0x01)
    it = iter(wave)
    chip.run_for(len(wave), env=lambda c: setattr(c, "ui_in", next(it)))
    got = list(chip.host_out)
    assert got == [(TAG_DATA, 0x10 | 0xEF << 8), (TAG_DATA, 0xEF | 0x10 << 8),
                   (TAG_EVENT, 0), (TAG_EVENT, 0),
                   (TAG_DATA, 0x80 | 0x7F << 8), (TAG_DATA, 0x01 | 0xFE << 8)]
