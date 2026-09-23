"""Pin units, pin-to-pin latency and UART through sigrok (ARCHITECTURE.md §5.5, §7)."""

import re
import shutil
import subprocess

import pytest

from tripsim import PAD_UI, PAD_UO, Chip
from tripsim.asm import cmpm_field, reflex
from tripsim.vcd import VcdRecorder

LEVEL1, LEVEL0 = 0x1800, 0x1000          # LEVEL v=1 / v=0, delay 0


def test_pin_to_pin_reaction_is_seven_clocks():
    """§5.5: pad edge -> sync (2) -> RX (1) -> EVAL (1) -> EXEC (1) -> TX accept (1) -> pad (1)."""
    chip = Chip(lanes=1)
    chip.pin_config(0, pin_a=PAD_UI + 0, rxmode="edge_ts")
    chip.pin_config(1, pin_a=PAD_UO + 0, txmode="level", idle=0)
    chip.own(PAD_UO + 0, 1)
    chip.connect("L0.I0", "U0.rx")
    chip.connect("U1.tx", "L0.O0")
    lane = chip.lanes[0]
    lane.k[:] = [LEVEL1, LEVEL0, 0, 0]
    # MOVB (D-009): the condition and dequeue act on I0, the result is the K constant
    lane.load_slot(0, reflex(urgent=True, op="MOVB", dst="O0", a="I0", b="K0", tag="EVENT",
                             head15=1, deq=True, ot="CTRL"))
    lane.load_slot(1, reflex(urgent=True, op="MOVB", dst="O0", a="I0", b="K1", tag="EVENT",
                             head15=0, deq=True, ot="CTRL"))
    chip.run([0])
    chip.run_for(20)
    for level in (1, 0, 1):
        assert (chip.outputs()[0] & 1) != level, "output moved without an input edge"
        t0 = chip.cycle
        chip.ui_in = level
        while (chip.outputs()[0] & 1) != level:
            chip.step()
            assert chip.cycle - t0 < 50
        assert chip.cycle - t0 == 7
        chip.run_for(10)
    assert chip.pins[1].flags["LATE"] == 0


def uart_wave(data, clocks_per_bit, idle_clocks=40):
    bits = [1] * idle_clocks
    for byte in data:
        frame = [0] + [(byte >> i) & 1 for i in range(8)] + [1]
        for i, b in enumerate(frame):
            n = round((i + 1) * clocks_per_bit) - round(i * clocks_per_bit)
            bits += [b] * n
        bits += [1] * 3
    return bits + [1] * idle_clocks


def sigrok_uart(vcd, channel, baud):
    out = subprocess.run(["sigrok-cli", "-i", str(vcd), "-I", "vcd",
                          "-P", f"uart:rx={channel}:baudrate={baud}:format=hex",
                          "-A", "uart=rx-data"], capture_output=True, text=True, check=True).stdout
    return bytes(int(h, 16) for h in re.findall(r"uart-\d+: ([0-9A-Fa-f]{2})\b", out))


needs_sigrok = pytest.mark.skipif(shutil.which("sigrok-cli") is None, reason="sigrok-cli not installed")


@needs_sigrok
@pytest.mark.parametrize("baud", [1_000_000, 921_600])
def test_uart_tx_shift_decoded_by_sigrok(tmp_path, baud):
    """Host bytes -> lane builds the 10-bit frame with SHOR -> U0 SHIFT -> uo0."""
    period = 50e6 / baud
    chip = Chip(lanes=1)
    chip.pin_config(0, pin_a=PAD_UO + 0, txmode="shift", nbits=10, period=period, idle=1)
    chip.own(PAD_UO + 0, 0)
    chip.connect("L0.I0", "HOST_IN")
    chip.connect("U0.tx", "L0.O0")
    lane = chip.lanes[0]
    lane.regs[1] = 0x200                                   # stop bit
    lane.load_slot(0, reflex(op="SHOR", dst="O0", a="I0", f=(1 << 4) | 1, deq=True))
    msg = b"TRIPWIRE\x00\xff\x55"
    for byte in msg:
        chip.host_push(byte)
    rec = VcdRecorder({"tx": lambda c: c.outputs()[0] & 1})
    chip.observers.append(rec)
    chip.run([0])
    chip.run_for(round((len(msg) * 10 + 20) * period))
    rec.write(tmp_path / "tx.vcd")
    assert sigrok_uart(tmp_path / "tx.vcd", "tx", baud) == msg
    assert chip.pins[0].flags["LATE"] == 0


@pytest.mark.parametrize("baud", [1_000_000, 115_200 * 4])
def test_uart_rx_framing_check(baud):
    """ui0 -> U0 SHIFT_RX (10 bits) -> lane checks start/stop with CMPM, extracts the byte."""
    period = 50e6 / baud
    chip = Chip(lanes=1)
    chip.pin_config(0, pin_a=PAD_UI + 0, rxmode="shift_rx", nbits=10, period=period, idle=1)
    chip.connect("L0.I0", "U0.rx")
    chip.connect("HOST_OUT", "L0.O0")
    lane = chip.lanes[0]
    lane.k[:] = [0x201, 0x200, 0, 0]                       # frame mask / expected: start 0, stop 1
    lane.load_slot(0, reflex(op="CMPM", a="I0", f=cmpm_field("K0", "K1"), state=0, ns=1, flag=0))
    lane.load_slot(1, reflex(op="EXT", dst="O0", a="I0", f=(7 << 4) | 1, deq=True,
                             state=1, flags={0: 1}, ns=0))
    lane.load_slot(2, reflex(op="MOV", dst="O0", a="I0", deq=True, ot="ERR",
                             state=1, flags={0: 0}, ns=0))
    chip.run([0])
    msg = b"\x00\x7e\xa5\xff"
    wave = uart_wave(msg, period)
    bad = [1] * 40 + [0] * round(period) + [1] * round(8 * period) + [0] * round(period) + [1] * 60
    wave += bad                                            # 0xFF with a missing stop bit
    wave += uart_wave(b"\x42", period)
    it = iter(wave)
    chip.run_for(len(wave), env=lambda c: setattr(c, "ui_in", next(it)))
    got = list(chip.host_out)
    assert [d for t, d in got if t == 0] == list(msg) + [0x42]
    assert [t for t, _ in got].count(3) == 1                # one framing error reported
    assert chip.pins[0].flags["OVERRUN"] == 0
