"""L3-CAN on the model: programs/can.trw against the reference CAN 2.0A node and sigrok."""

import re
import shutil
import subprocess

import pytest

from kernels import load_program
from protomodels.can import CANNode, crc15
from tripsim import Chip
from tripsim.isa import TAG_DATA, TAG_ERR, TAG_EVENT
from tripsim.vcd import VcdRecorder

LOOP = 5                                # transceiver loop delay TXD -> bus -> RXD, clocks (100 ns)


class Bus:
    """Wired-AND bus: our TXD (uo0) and the reference nodes; our RXD (ui0) sees it LOOP clocks late."""

    def __init__(self, chip, nodes, vcd=False):
        self.chip, self.nodes = chip, nodes
        self.hist = [1] * LOOP
        self.rec = None
        if vcd:
            self.rec = VcdRecorder({"can": lambda c: self.level})
            chip.observers.append(self.rec)
        self.level = 1
        self.got = []                               # what the host has read from HOST_OUT

    def run(self, clocks):
        for _ in range(clocks):
            ours = self.chip.outputs()[0] & 1
            self.level = ours
            for n in self.nodes:
                self.level &= n.drive
            self.hist.append(self.level)
            self.chip.ui_in = self.hist.pop(0)
            self.chip.step()
            for n in self.nodes:
                n.step(self.level)
            while self.chip.host_out:                   # the host reads its FIFO (16 deep)
                self.got.append(self.chip.host_out.popleft())


def make(period):
    chip = Chip(lanes=2)
    chip.settle_inputs(ui=1)
    load_program(chip, "can", PERIOD=period)
    return chip


def send(chip, can_id, data):
    chip.host_push(len(data), tag=TAG_EVENT)
    chip.host_push(can_id)
    for b in data:
        chip.host_push(b)


def frames_seen(bus):
    """Host-side decode of the chip's reports: [(id, data, crc_ok)], plus TX results."""
    frames, words, results = [], [], []
    for tag, d in bus.got:
        if tag == TAG_EVENT and d == 0x9001:            # our frame started
            continue
        if tag == TAG_EVENT and d & 0x8000:             # our frame's result
            results.append(d)
        elif tag == TAG_DATA:
            words.append(d)
        elif tag in (TAG_EVENT, TAG_ERR):
            bits = "".join(f"{w:012b}" for w in words)
            dlc = int(bits[15:19], 2)
            n = 19 + 8 * min(dlc, 8) + 15 - len(bits)
            bits += f"{d & 0xFFF:0{n}b}" if n else ""
            data = [int(bits[19 + 8 * k:27 + 8 * k], 2) for k in range(min(dlc, 8))]
            ok = tag == TAG_EVENT and crc15([int(b) for b in bits[:-15]]) == int(bits[-15:], 2)
            frames.append((int(bits[1:12], 2), data, ok))
            words = []
    return frames, results


def frame_clocks(period, nbytes):
    body = 34 + 8 * nbytes                             # SOF .. CRC, destuffed
    return (body + body // 4 + 10 + 11 + 20) * period   # worst-case stuffing, trailer, idle, lane gaps


def sigrok_frames(path, period):
    out = subprocess.run(["sigrok-cli", "-i", str(path), "-I", "vcd", "-P",
                          f"can:can_rx=can:nominal_bitrate={50_000_000 // period}:sample_point=75", "-A", "can"],
                         capture_output=True, text=True, check=True).stdout
    return out


@pytest.mark.parametrize("period", [400, 100, 50])     # 125 kbit/s, 500 kbit/s, 1 Mbit/s
def test_we_send_reference_receives(period, tmp_path):
    chip = make(period)
    ref = CANNode(period)
    bus = Bus(chip, [ref], vcd=True)
    bus.run(12 * period)                                # bus idle first
    send(chip, 0x123, [0xDE, 0xAD, 0xBE, 0xEF])
    send(chip, 0x7FF, [])                               # all-ones ID: stuffing in the ID field
    send(chip, 0x000, [0x00] * 8)                       # long dominant runs: many stuff bits
    bus.run(sum(frame_clocks(period, n) for n in (4, 0, 8)) + 20 * period)
    got = [(f["id"], f["data"], f["crc_ok"]) for f in ref.received]
    assert got == [(0x123, [0xDE, 0xAD, 0xBE, 0xEF], True), (0x7FF, [], True), (0, [0] * 8, True)]
    frames, results = frames_seen(bus)
    assert [r & 0xE000 for r in results] == [0xA000] * 3            # every frame ACKed
    assert frames == got                                          # self-reception matches
    if shutil.which("sigrok-cli"):
        bus.rec.write(tmp_path / "can.vcd")
        out = sigrok_frames(tmp_path / "can.vcd", period)
        assert out.count("ACK slot: ACK") == 3, out
        ids = [int(x, 16) for x in re.findall(r"Identifier: \d+ \(0x([0-9a-f]+)\)", out)]
        assert ids == [0x123, 0x7FF, 0x000], out
        data = [int(x, 16) for x in re.findall(r"Data byte \d+: 0x([0-9a-f]{2})", out)]
        assert data == [0xDE, 0xAD, 0xBE, 0xEF] + [0] * 8, out
        assert "error" not in out.lower() and out.count("End of frame") == 3, out


@pytest.mark.parametrize("period", [400, 100, 50])
@pytest.mark.parametrize("drift", [1.0, 1.004, 0.996])            # reference clock ±0.4 %
def test_reference_sends_we_receive_and_ack(period, drift):
    frames = [(0x555, [0x55, 0xAA]), (0x0F0, [1, 2, 3, 4, 5, 6, 7, 8]), (0x7FF, [])]
    chip = make(period)
    ref = CANNode(period * drift)
    bus = Bus(chip, [ref])
    bus.run(12 * period)                                # both nodes see bus idle (11 bits) first
    ref.pending = [(i, list(d)) for i, d in frames]
    bus.run(sum(frame_clocks(period, len(d)) for _, d in frames) + 30 * period)
    got, _ = frames_seen(bus)
    assert got == [(i, d, True) for i, d in frames]
    assert ref.results == [(i, "acked") for i, _ in frames]       # our ACKs arrived in the slot


def crc_ends_with_stuff_bit():
    """A frame whose CRC field ends with five equal bits, so a stuff bit follows it."""
    from protomodels.can import frame_fields, stuff
    for can_id in range(0x100, 0x800):
        f = frame_fields(can_id, [can_id & 0xFF])
        if len(stuff(f)) > len(stuff(f[:-1])) + 1:
            return can_id, [can_id & 0xFF]
    raise AssertionError("no such frame")


@pytest.mark.parametrize("loop", [5, 15])                   # 100 ns and 300 ns transceiver loop
def test_ack_lands_in_the_slot_after_a_stuff_bit_following_the_crc(loop, monkeypatch):
    """The ACK override is armed by the CRC delimiter's sample, not by the stuff bit before it."""
    monkeypatch.setattr(__import__(__name__), "LOOP", loop)
    period = 50
    can_id, data = crc_ends_with_stuff_bit()
    chip = make(period)
    ref = CANNode(period)
    bus = Bus(chip, [ref])
    bus.run(12 * period)
    ref.pending = [(can_id, data)]
    send(chip, 0x7F0, [0xA5, 0x0F])                     # and we transmit one after it
    bus.run(2 * frame_clocks(period, 2) + 20 * period)
    assert ref.results == [(can_id, "acked")]
    assert [(f["id"], f["data"]) for f in ref.received] == [(0x7F0, [0xA5, 0x0F])]
    frames, results = frames_seen(bus)
    assert frames[0] == (can_id, data, True) and results[-1] & 0xE000 == 0xA000


def test_arbitration_lost_then_retry():
    period = 100
    chip = make(period)
    ref = CANNode(period)
    bus = Bus(chip, [ref])
    bus.run(12 * period)                                # bus idle
    ref.pending = [(0x100, [0x11]), (0x0F0, [0x22])]
    bus.run(5 * period)                                 # ref's first frame starts
    send(chip, 0x0F8, [0x33])                           # queued during it: both start after it
    bus.run(3 * frame_clocks(period, 1) + 20 * period)
    frames, results = frames_seen(bus)
    # ref 0x100 first; then both start: 0x0F0 (ref) beats 0x0F8 (ours) at an ID bit
    assert [f[0] for f in frames[:2]] == [0x100, 0x0F0]
    assert results[0] & 0xE000 == 0x8000                # lost (abort event)
    assert [r["id"] for r in ref.received] == []        # ours did not complete
    send(chip, 0x0F8, [0x33])                           # the host retries
    bus.run(frame_clocks(period, 1) + 20 * period)
    frames, results = frames_seen(bus)
    assert results[-1] & 0xE000 == 0xA000
    assert [r["id"] for r in ref.received] == [0x0F8]
    assert ref.results[:2] == [(0x100, "acked"), (0x0F0, "acked")]


def test_bad_crc_is_reported_and_not_acked():
    period = 100
    chip = make(period)
    ref = CANNode(period, corrupt_crc=True)
    bus = Bus(chip, [ref])
    bus.run(12 * period)
    ref.pending = [(0x321, [9, 8, 7])]
    bus.run(frame_clocks(period, 3) + 10 * period)
    errs = [d for t, d in bus.got if t == TAG_ERR]
    assert errs and errs[0] >> 12 == 0                  # CRC error report
    assert ref.results[0] == (0x321, "noack")
