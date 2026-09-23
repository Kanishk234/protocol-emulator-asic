"""Pin units, pin-to-pin latency and UART through sigrok (ARCHITECTURE.md §5.5, §7)."""

import re
import shutil
import subprocess

import pytest

from tripsim import PAD_UI, PAD_UIO, PAD_UO, Chip
from tripsim.asm import cmpm_field, reflex
from tripsim.vcd import VcdRecorder

LEVEL1, LEVEL0 = 0x1800, 0x1000          # LEVEL v=1 / v=0, delay 0


def test_pin_to_pin_reaction_is_seven_clocks():
    """§5.5: pad edge -> sync (2) -> RX (1) -> EVAL (1) -> EXEC (1) -> TX accept (1) -> pad (1)."""
    chip = Chip(lanes=1)
    chip.pin_config(0, pin_a=PAD_UI + 0, ev_edge="both")          # edge events on ui0
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


def pulse_chip(**sym):
    chip = Chip(lanes=1)
    chip.pin_config(0, pin_a=PAD_UO + 0, txmode="pulse", nbits=4, order="msb", idle=0, **sym)
    chip.own(PAD_UO + 0, 0)
    chip.connect("U0.tx", "HOST_IN")
    return chip


def trace(chip, n):
    out = []
    for _ in range(n):
        chip.step()
        out.append(chip.outputs()[0] & 1)
    return out


def runs(levels):
    """[(level, length)] of a waveform, dropping the leading idle."""
    out = []
    for v in levels:
        if out and out[-1][0] == v:
            out[-1][1] += 1
        else:
            out.append([v, 1])
    return [tuple(r) for r in out[1:]]


def test_pulse_width_symbols_exact_and_back_to_back():
    """PULSE (§14 P17): WS2812-like symbols; two tokens join with no gap."""
    chip = pulse_chip(sym0_first=1, sym0_t1=3, sym0_t2=7, sym1_first=1, sym1_t1=6, sym1_t2=4)
    chip.host_push(0b1010)
    chip.host_push(0b0110)
    r = runs(trace(chip, 120))
    one, zero = [(1, 6), (0, 4)], [(1, 3), (0, 7)]
    expect = one + zero + one + zero + zero + one + one + zero
    # the last symbol's low phase merges with the idle-low line that follows
    assert r[:len(expect) - 1] == expect[:-1]
    assert r[len(expect) - 1][0] == 0 and r[len(expect) - 1][1] >= 7
    assert chip.pins[0].flags["LATE"] == 0


def test_pulse_manchester_and_distance_codes():
    """The same primitive does Manchester (level first differs) and pulse-distance (space differs)."""
    chip = pulse_chip(sym0_first=1, sym0_t1=5, sym0_t2=5, sym1_first=0, sym1_t1=5, sym1_t2=5)
    chip.host_push(0b0011)                         # Manchester: 0 = high-low, 1 = low-high
    levels = trace(chip, 60)
    start = levels.index(1)
    # bits 0,0,1,1 -> H5 L5 | H5 L5 | L5 H5 | L5 H5 (adjacent lows merge)
    assert levels[start:start + 40] == [1] * 5 + [0] * 5 + [1] * 5 + [0] * 10 + [1] * 5 + [0] * 5 + [1] * 5
    chip = pulse_chip(sym0_first=1, sym0_t1=4, sym0_t2=4, sym1_first=1, sym1_t1=4, sym1_t2=12)
    chip.host_push(0b0101)                         # pulse distance: fixed mark, the space carries the bit
    r = runs(trace(chip, 80))
    assert r[:7] == ([(1, 4), (0, 4), (1, 4), (0, 12)] * 2)[:7]   # the last space merges with idle
    assert r[7][0] == 0 and r[7][1] >= 12


def level_unit(od=False):
    chip = Chip(lanes=1)
    chip.pin_config(0, pin_a=PAD_UIO + 0, txmode="level", idle=0, od=od, nbits=4, order="lsb")
    chip.own(PAD_UIO + 0, 0)
    chip.connect("U0.tx", "HOST_IN")
    return chip


def test_level_oe_sync_and_late():
    """§14 P3/P4: delays count from the cursor; SYNC re-anchors; a missed delay sets LATE."""
    chip = level_unit()
    chip.host_push(0x5000, tag=1)                        # SYNC
    chip.host_push(0x1800 | 10, tag=1)                   # LEVEL 1, 10 ticks after the cursor
    chip.host_push(0x2000 | 5, tag=1)                    # OE 0, 5 ticks later
    seen = []
    for _ in range(40):
        chip.step()
        _, uio, oe = chip.outputs()
        seen.append((uio & 1, oe & 1))
    t_high = seen.index((1, 1))
    t_off = next(i for i, s in enumerate(seen) if s[1] == 0)
    assert t_off - t_high == 5                            # relative to the cursor, not to arrival
    assert chip.pins[0].flags["LATE"] == 0
    chip.run_for(200)                                    # cursor now far in the past
    chip.host_push(0x1000 | 3, tag=1)                    # LEVEL 0 "3 ticks after the cursor": missed
    chip.run_for(10)
    assert chip.pins[0].flags["LATE"] == 1


def test_setn_changes_shift_length():
    chip = pulse_chip(sym0_first=1, sym0_t1=2, sym0_t2=2, sym1_first=1, sym1_t1=2, sym1_t2=2)
    chip.host_push(0x6002, tag=1)                        # SETN 2
    chip.host_push(0b11)
    highs = sum(1 for r in runs(trace(chip, 60)) if r[0] == 1)
    assert highs == 2                                    # 2 bits, not the configured 4


def rx_unit(**cfg):
    chip = Chip(lanes=1)
    chip.pin_config(0, pin_a=PAD_UI + 0, pin_b=PAD_UI + 1, presc=1, order="lsb", **cfg)
    chip.connect("U0.tx", "HOST_IN")
    chip.connect("HOST_OUT", "U0.rx")
    return chip


def test_setn_rx_restarts_framing_at_the_cursor():
    """§14 P18: SETN rx=1 sets the RX word length and restarts framing, timed at the cursor."""
    chip = rx_unit(rxmode="linked_rx", rx_edge="rise", rx_nbits=4)
    chip.run_for(10)
    chip.ui_in = 0b10                                    # a stray rising edge: bit 0 of a 4-bit word
    chip.run_for(5)
    chip.ui_in = 0
    chip.host_push(0x5000, tag=1)                        # SYNC
    chip.host_push(0x4000 | 20, tag=1)                   # GAP 20
    chip.host_push(0x6020 | 3, tag=1)                    # SETN rx, 3 bits: at cursor = +20
    chip.run_for(30)
    for bit in (1, 0, 1):                                # a 3-bit word after the restart
        chip.ui_in = bit
        chip.run_for(4)
        chip.ui_in = bit | 0b10
        chip.run_for(4)
        chip.ui_in = bit
    chip.run_for(10)
    assert list(chip.host_out) == [(0, 0b101)]           # the stray bit was dropped


def test_sample_reads_pin_a_at_timed_points():
    """§14 P19: SAMPLE puts pin A's level at cursor + delay into the RX framing."""
    chip = rx_unit(rx_nbits=3)
    chip.host_push(0x5000, tag=1)                        # SYNC at accept (clock ~2): cursor ~3
    for _ in range(3):
        chip.host_push(0x8000 | 20, tag=1)               # SAMPLE 20 ticks after the previous one
    levels = [1] * 33 + [0] * 20 + [1] * 30              # sampled at ~23, ~43, ~63 (+2 sync)
    for v in levels:
        chip.ui_in = v
        chip.step()
    assert list(chip.host_out) == [(0, 0b101)]           # 1, 0, 1 in LSB order


def test_consumer_port_tag_filter():
    """§14 F7: a port drops tags it does not accept, without blocking the producer."""
    from tripsim.fabric import Fabric
    f = Fabric()
    p = f.producer("P")
    f.port("data_only"); f.port("all")
    f.connect("data_only", "P", accept=1 << 0)
    f.connect("all", "P")
    p.load(1, 7); f.commit()                             # a CTRL token
    assert not f.ports["data_only"].avail() and f.ports["all"].avail()
    f.ports["all"].take(); f.commit()
    assert p.free()                                      # the filtered port did not hold it
    assert f.ports["data_only"].filtered == 1


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
