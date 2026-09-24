"""L3-LIN on the model: programs/lin.trw (commander + bus monitor) against the reference LIN 2.x
responder and sigrok's lin decoder."""

import re
import shutil
import subprocess

import pytest

from kernels import load_program
from protomodels.lin import LINResponder, checksum, pid_of
from tripsim import Chip
from tripsim.isa import TAG_DATA, TAG_ERR, TAG_EVENT
from tripsim.vcd import VcdRecorder

BAUD = 19200
T = 50e6 / BAUD
FRAME = 180 * T                                  # a frame slot: header + 1.4 x (8 bytes + checksum)


class Bus:
    def __init__(self, chip, node, vcd=False):
        self.chip, self.node, self.got, self.level = chip, node, [], 1
        self.rec = None
        if vcd:
            self.rec = VcdRecorder({"lin": lambda c: self.level})
            chip.observers.append(self.rec)

    def run(self, clocks):
        for _ in range(int(clocks)):
            self.level = (self.chip.outputs()[0] & 1) & self.node.drive
            self.chip.ui_in = self.level
            self.chip.step()
            self.node.step(self.level)
            while self.chip.host_out:
                self.got.append(self.chip.host_out.popleft())


def make(node, vcd=False):
    chip = Chip(lanes=2)
    chip.settle_inputs(ui=1)
    load_program(chip, "lin", BAUD=BAUD)
    return chip, Bus(chip, node, vcd)


def header(chip, fid, n, publish=None):
    chip.host_push((0x8000 if publish else 0) | n << 8 | fid, tag=TAG_EVENT)
    for b in publish or ():
        chip.host_push(b)


def test_subscribe_publish_and_classic(tmp_path):
    node = LINResponder(T, publish={0x10: [1, 2, 3, 4], 0x3D: [9, 8, 7, 6, 5, 4, 3, 2]},
                        subscribe={0x22: 2, 0x3C: 8})
    chip, bus = make(node, vcd=True)
    bus.run(20 * T)
    header(chip, 0x10, 4)                                         # responder publishes
    header(chip, 0x22, 2, publish=[0xAB, 0xCD])                   # we publish
    header(chip, 0x3C, 8, publish=[0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80])  # classic
    header(chip, 0x3D, 8)                                         # classic, responder
    bus.run(4.5 * FRAME)
    assert node.headers == [(0x10, True), (0x22, True), (0x3C, True), (0x3D, True)]
    assert node.received == [(0x22, [0xAB, 0xCD], True),
                             (0x3C, [0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80], True)]
    ok = (TAG_EVENT, 0)
    assert bus.got == ([(TAG_DATA, b) for b in [1, 2, 3, 4]] + [ok]
                       + [(TAG_DATA, b) for b in [0xAB, 0xCD]] + [ok]
                       + [(TAG_DATA, b) for b in [0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80]] + [ok]
                       + [(TAG_DATA, b) for b in [9, 8, 7, 6, 5, 4, 3, 2]] + [ok])
    if shutil.which("sigrok-cli"):
        bus.rec.write(tmp_path / "lin.vcd")
        out = subprocess.run(["sigrok-cli", "-i", str(tmp_path / "lin.vcd"), "-I", "vcd", "-P",
                              f"uart:rx=lin:baudrate={BAUD},lin", "-A", "lin"],
                             capture_output=True, text=True, check=True).stdout
        ids = [int(x, 16) for x in re.findall(r"ID: ([0-9A-F]{2}) Parity: \d \(ok\)", out)]
        assert ids == [0x10, 0x22, 0x3C, 0x3D], out
        cks = [int(x, 16) for x in re.findall(r"Checksum: 0x([0-9A-F]{2})", out)]
        assert cks == [checksum(0x10, [1, 2, 3, 4]), checksum(0x22, [0xAB, 0xCD]),
                       checksum(0x3C, [0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80]),
                       checksum(0x3D, [9, 8, 7, 6, 5, 4, 3, 2])], out
        assert "invalid" not in out.lower() and "Parity: " in out, out


def test_bad_checksum_and_no_response():
    node = LINResponder(T, publish={0x05: [0x55, 0xAA]}, bad_checksum={0x05})
    chip, bus = make(node)
    bus.run(20 * T)
    header(chip, 0x05, 2)                         # the responder's checksum is wrong
    bus.run(FRAME)
    header(chip, 0x07, 3)                         # nobody answers ID 7 ...
    bus.run(FRAME)
    header(chip, 0x05, 2)                         # ... which the next header reveals
    bus.run(2 * FRAME)
    bad = (checksum(0x05, [0x55, 0xAA]) ^ 1) | 0x300
    assert bus.got[:3] == [(TAG_DATA, 0x55), (TAG_DATA, 0xAA), (TAG_ERR, bad)]
    assert bus.got[3] == (TAG_ERR, 0x400)
    assert [pid_of(f) for f, _ in node.headers] == [pid_of(5), pid_of(7), pid_of(5)]
