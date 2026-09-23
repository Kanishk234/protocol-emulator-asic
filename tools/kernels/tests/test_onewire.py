"""L3-1W on the model: programs/onewire.trw against the reference 1-Wire device and sigrok."""

import re
import shutil
import subprocess

from kernels import load_program
from protomodels.onewire import US, OneWireDevice, crc8
from tripsim import Chip
from tripsim.isa import TAG_CTRL, TAG_DATA
from tripsim.vcd import VcdRecorder

DQ = 0
RESET, READ = 0, 1
SLOT = 70 * US


def bus_of(chip, dev):
    _, uio, oe = chip.outputs()
    ours_low = ((oe >> DQ) & 1) and not ((uio >> DQ) & 1)
    return int(dev.drive and not ours_low)


def run(dev, chip, clocks, each=None):
    for _ in range(clocks):
        bus = bus_of(chip, dev)
        chip.uio_in = (0xFF & ~1) | bus
        chip.step()
        dev.step(bus)
        if each:
            each(bus)


def make(**kw):
    chip = Chip(lanes=1)
    chip.settle_inputs(uio=0xFF)
    load_program(chip, "onewire")
    return chip, OneWireDevice(**kw)


def test_reset_presence_and_read_rom(tmp_path):
    chip, dev = make()
    rec = VcdRecorder({"dq": lambda c: c.uio_in & 1})
    chip.observers.append(rec)
    chip.host_push(RESET, tag=TAG_CTRL)
    chip.host_push(0x33)                                    # READ ROM
    for _ in range(8):
        chip.host_push(READ, tag=TAG_CTRL)
    run(dev, chip, 1000 * US + 9 * 8 * SLOT + 200 * US)
    rec.write(tmp_path / "ow.vcd")
    out = [d for t, d in chip.host_out if t == TAG_DATA]
    assert dev.resets == 1 and dev.received == [0x33]
    assert out[0] == 0                                      # presence pulse seen
    assert out[1:] == dev.rom and crc8(out[1:8]) == out[8]
    if shutil.which("sigrok-cli"):
        txt = subprocess.run(["sigrok-cli", "-i", str(tmp_path / "ow.vcd"), "-I", "vcd",
                              "-P", "onewire_link:owr=dq,onewire_network", "-A", "onewire_network"],
                             capture_output=True, text=True, check=True).stdout
        assert "Read ROM" in txt, txt
        rom = re.search(r"ROM: 0x([0-9a-fA-F]{16})", txt)
        assert rom and int(rom.group(1), 16) == int.from_bytes(bytes(dev.rom), "little"), txt


def test_no_device_reports_no_presence():
    chip, dev = make(present=False)
    chip.host_push(RESET, tag=TAG_CTRL)
    run(dev, chip, 1100 * US)
    assert [d for t, d in chip.host_out if t == TAG_DATA] == [1]


def test_write_slot_timing():
    """AN126: a 0 is 60 us low, a 1 is 6 us low; every slot is 70 us (checked on the wire)."""
    chip, dev = make()
    byte = 0b10100101
    chip.host_push(byte)
    lows, st = [], {"t": 0, "prev": 1, "start": None}

    def watch(bus):
        if st["prev"] and not bus:
            st["start"] = st["t"]
        if bus and not st["prev"]:
            lows.append((st["start"], st["t"] - st["start"]))
        st["prev"], st["t"] = bus, st["t"] + 1

    run(dev, chip, 9 * SLOT, each=watch)
    assert [d for _, d in lows] == [(6 if (byte >> i) & 1 else 60) * US for i in range(8)]
    assert all(b[0] - a[0] == SLOT for a, b in zip(lows, lows[1:]))
    assert dev.received == [byte]
