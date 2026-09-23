"""L3-UART on the model: programs/uart.trw (TX + RX in one lane) against the reference line model and sigrok."""

import re
import shutil
import subprocess

import pytest

from kernels import load_program
from protomodels import uart
from tripsim import Chip
from tripsim.isa import TAG_DATA, TAG_ERR
from tripsim.vcd import VcdRecorder

MSG = b"TRIPWIRE\x00\xff\x55\xaa"


def cpb(baud):
    return 50e6 / baud


@pytest.mark.parametrize("baud", [9600 * 16, 115200, 460800, 1_000_000])
def test_uart_tx(baud, tmp_path):
    chip = Chip(lanes=1)
    load_program(chip, "uart", BAUD=baud)
    for b in MSG:
        chip.host_push(b)
    line = []
    rec = VcdRecorder({"tx": lambda c: c.outputs()[0] & 1})
    chip.observers.append(rec)
    for _ in range(round((len(MSG) * 10 + 20) * cpb(baud))):
        chip.step()
        line.append(chip.outputs()[0] & 1)
    assert uart.decode(line, cpb(baud)) == [(b, True) for b in MSG]
    assert chip.pins[0].flags["LATE"] == 0
    if shutil.which("sigrok-cli"):
        rec.write(tmp_path / "tx.vcd")
        out = subprocess.run(["sigrok-cli", "-i", str(tmp_path / "tx.vcd"), "-I", "vcd",
                              "-P", f"uart:rx=tx:baudrate={baud}:format=hex", "-A", "uart=rx-data"],
                             capture_output=True, text=True, check=True).stdout
        assert bytes(int(h, 16) for h in re.findall(r"uart-\d+: ([0-9A-F]{2})\b", out)) == MSG


@pytest.mark.parametrize("baud", [115200, 460800, 1_000_000])
def test_uart_rx_with_framing_errors(baud):
    chip = Chip(lanes=1)
    chip.settle_inputs(ui=1)                                   # idle-high line through reset
    load_program(chip, "uart", BAUD=baud)
    wave = uart.encode(MSG, cpb(baud), bad_stop={3})           # byte 3 has a broken stop bit
    it = iter(wave)
    chip.run_for(len(wave), env=lambda c: setattr(c, "ui_in", next(it)))
    chip.run_for(50)
    got = list(chip.host_out)
    assert [d for t, d in got if t == TAG_DATA] == [b for i, b in enumerate(MSG) if i != 3]
    errs = [d for t, d in got if t == TAG_ERR]
    assert len(errs) == 1 and (errs[0] >> 1) & 0xFF == MSG[3] and not errs[0] >> 9 & 1
    assert chip.pins[1].flags["OVERRUN"] == 0


def test_uart_loopback_all_bytes():
    """Metamorphic (L4-LOOP): TX looped to RX returns every byte value unchanged."""
    chip = Chip(lanes=1)
    chip.settle_inputs(ui=1)
    load_program(chip, "uart", BAUD=1_000_000)
    for b in range(256):
        chip.host_push(b)
    chip.host_fifo_depth = 1000
    chip.run_for(round(256 * 10 * 50 + 500), env=lambda c: setattr(c, "ui_in", c.outputs()[0] & 1))
    assert [d for t, d in chip.host_out if t == TAG_DATA] == list(range(256))
