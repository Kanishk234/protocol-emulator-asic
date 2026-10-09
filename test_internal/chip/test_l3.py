"""L3 on the RTL (VERIFICATION.md §6): firmware programs on trw_chip, through its pads. Each program is compiled
by tripc, loaded with tools/host over SPI, and checked against protocol reference models and sigrok where enabled.

  UART  programs/uart.trw            TX at 1 Mbaud, 115200 and 9600; RX at 460800 and 115200 with a framing error
  MIDI  programs/uart.trw            TX at 31,250 baud; note, control-change and program-change messages
  SPI-C programs/spi_controller.trw  mode 0 at 1, 5 and 8.3 MHz
  SPI-T programs/spi_target.trw      mode 0 against a reference controller at about 400 kHz
  I2C-C programs/i2c_controller.trw  100 kHz / ~400 kHz / 1 MHz: writes, NACK, repeated START, reads, stretching
  I2C-T programs/i2c_target.trw      writes, address NACK and readback at 400 kHz and 1 MHz
  DMX  programs/dmx.trw              two 8N2 packets with BREAK and MAB timing
  PULSE programs/ws2812.trw, dshot.trw WS2812 data frames and DShot at 150/300/600/1200 kbit/s
  PWM  programs/servo.trw            20 ms servo frames with a live width update
  I2S  programs/i2s.trw              full-duplex 16-bit stereo at 48/96/192 kHz
  Other shipped programs: PS/2, 1-Wire, JTAG, SWD, SMBus, HDLC, LIN, CAN, IR NEC repeat RX

The tests provide implementation-level evidence for these exercised cases only. Other roadmap programs need
matching RTL and hardened-netlist checks before they have implementation-level evidence.
"""

import importlib.util
import os
import re
from pathlib import Path

import cocotb
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge, ValueChange, with_timeout
from cocotb.utils import get_sim_time

from chiplib import HM, TAGS, Wire, hex_bytes, load as _load, sigrok, start, write_vcd
from protomodels import dmx, hdlc, nec, pulse, uart
from protomodels.i2c import I2CController, I2CTarget
from protomodels.i2s import I2SADC, I2SReceiver
from protomodels.can import CANNode
from protomodels.jtag import IDCODE, JTAGTarget
from protomodels.lin import LINResponder, checksum as lin_checksum
from protomodels.onewire import OneWireDevice, crc8
from protomodels.ps2 import PS2Device
from protomodels.smbus import SMBusDevice, crc8 as smbus_crc8
from protomodels.spi import SPIController, SPITarget
from protomodels.swd import DPIDR, OK as SWD_OK, WAIT as SWD_WAIT, SWDTarget, parity as swd_parity

DATA, CTRL, EVENT, ERR = (TAGS[t] for t in ("DATA", "CTRL", "EVENT", "ERR"))
MSG = b"TRIPWIRE\x00\xff\x55"


def _candidate_port_map():
    """Load a shape-specific generated fabric map for reduced RTL candidates when requested."""
    spec_path = os.environ.get("TRIPWIRE_SPEC_FILE")
    if not spec_path:
        return None
    spec_path = Path(spec_path)
    if not spec_path.is_file():
        raise FileNotFoundError(f"TRIPWIRE_SPEC_FILE does not exist: {spec_path}")
    spec = importlib.util.spec_from_file_location("candidate_tripwire_spec", spec_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load candidate fabric map from {spec_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_CANDIDATE_SPEC = _candidate_port_map()


def _candidate_port_words(image):
    spec = _CANDIDATE_SPEC
    ports = {consumer: 0 for consumer in spec.FABRIC_CONSUMERS}
    for consumer, producer, mode, accept in image["connect"]:
        source = spec.LEGAL_SOURCES[consumer].index(producer)
        ports[consumer] = int(mode == "tap") << 1 | source << 2 | (accept & 0xF) << 6 | 1
    return [ports[consumer] for consumer in spec.FABRIC_CONSUMERS]


async def load(p, program, run=True, **params):
    """Load programs with a reduced candidate's generated logical fabric numbering when requested."""
    if _CANDIDATE_SPEC is None:
        return await _load(p, program, run=run, **params)
    image = await _load(p, program, run=False, **params)
    await p.write(HM["ports"], _candidate_port_words(image))
    if run:
        lanes = sum(1 << int(name[1:]) for name in image["lanes"])
        await p.write(HM["run"], [lanes])
    return image


async def until(p, cond, clocks, step=50):
    for _ in range(clocks // step):
        if cond():
            return True
        await ClockCycles(p.d.clk, step)
    return cond()


@cocotb.test()
async def test_l3_uart_tx(dut):
    """L3-UART TX: bytes pushed into HOST_IN leave on uo0 as 8N1 frames at the programmed rate."""
    for i, (baud, msg) in enumerate(((1_000_000, MSG), (115_200, MSG), (9_600, b"T\xa5"))):
        cpb = 50e6 / baud
        p = await start(dut, clock=i == 0)
        await load(p, "uart", BAUD=baud)
        w = Wire(p, lambda uo, uout, uoe, bus: ({0: 1}, None), {"tx": lambda uo, bus: uo & 1})
        for b in msg:
            await p.push(b)
        n = round((len(msg) * 10 + 20) * cpb)
        await until(p, lambda: len(uart.decode(w.rec["tx"], cpb)) == len(msg) and w.clocks > n // 2, 4 * n)
        await ClockCycles(dut.clk, round(2 * cpb))
        w.stop()
        assert uart.decode(w.rec["tx"], cpb) == [(b, True) for b in msg], baud
        assert await p.read(0x0010, 1) == [0], "U0: no OVERRUN or LATE"
        write_vcd("uart_tx.vcd", w.rec)
        out = sigrok("uart_tx.vcd", f"uart:rx=tx:baudrate={baud}:format=hex", "uart=rx-data")
        if out is not None:
            assert bytes(hex_bytes(out, r"uart-\d+: ")) == msg, (baud, out[:200])


@cocotb.test()
async def test_l3_uart_rx_framing(dut):
    """L3-UART RX: a reference waveform on ui0, byte 3 with a broken stop bit: the good bytes arrive as DATA,
    the broken frame as one ERR token carrying the raw frame, and nothing overruns. At 460800 and 115200 baud:
    rates the host link can drain (at SCK = clk/8 a HOST_OUT read takes ~560 clocks; CLAIMS.md, Known limits)."""
    for i, baud in enumerate((460_800, 115_200)):
        cpb = 50e6 / baud
        msg = MSG if baud > 200_000 else MSG[:5]
        wave = uart.encode(msg, cpb, bad_stop={3})
        p = await start(dut, ui=1, clock=i == 0)            # idle-high line through reset
        await load(p, "uart", BAUD=baud)
        it = iter(wave)
        w = Wire(p, lambda uo, uout, uoe, bus, it=it: ({0: next(it, 1)}, None), {"rx": lambda uo, bus: 0})
        got = []
        for _ in range(2000):
            tok = await p.pop()
            if tok:
                got.append(tok)
            if len(got) == len(msg):
                break
        w.stop()
        assert [d for t, d in got if t == DATA] == [b for k, b in enumerate(msg) if k != 3], (baud, got)
        errs = [d for t, d in got if t == ERR]
        assert len(errs) == 1 and errs[0] >> 1 & 0xFF == msg[3] and not errs[0] >> 9 & 1, (baud, got)
        assert await p.read(0x0011, 1) == [0], "U1: no OVERRUN"


@cocotb.test()
async def test_l3_midi_tx(dut):
    """L3-MIDI TX: UART firmware at 31,250 baud sends note, control-change and program-change messages."""
    baud, cpb = 31_250, 1600
    msg = bytes([0x90, 60, 100, 0x80, 60, 0, 0xB0, 7, 127, 0xC5, 12])
    p = await start(dut, clock=True)
    await load(p, "uart", BAUD=baud)
    wire = Wire(p, lambda uo, uout, uoe, bus: ({0: 1}, None), {"midi": lambda uo, bus: uo & 1})
    for byte in msg:
        await p.push(byte)
    clocks = round((len(msg) * 10 + 20) * cpb)
    await until(p, lambda: len(uart.decode(wire.rec["midi"], cpb)) == len(msg), 2 * clocks)
    await ClockCycles(dut.clk, 2 * cpb)
    wire.stop()
    assert uart.decode(wire.rec["midi"], cpb) == [(byte, True) for byte in msg]

    write_vcd("midi_tx.vcd", wire.rec)
    out = sigrok("midi_tx.vcd", "uart:rx=midi:baudrate=31250,midi", "midi")
    if out is not None:
        assert "note on (note = 60 'C4', velocity = 100)" in out, out
        assert "note off (note = 60 'C4'" in out and "control change" in out, out
        assert "Channel 6: program change to instrument 13" in out, out


@cocotb.test()
async def test_l3_dmx_tx(dut):
    """L3-DMX TX: 250 kbaud 8N2 packets with valid BREAK/MAB and slot data."""
    stops, mtbp = 3, 20
    packets = [[0, 255, 128, 0, 17, 42], [0] + list(range(1, 25))]
    p = await start(dut, clock=True)
    await load(p, "dmx", STOPS=stops, MTBP=mtbp)
    wire = Wire(p, lambda uo, uout, uoe, bus: ({0: 1}, None), {"dmx": lambda uo, bus: uo & 1})
    for slots in packets:
        await p.push(0, EVENT)
        for byte in slots:
            await p.push(byte)

    clocks = sum(150 * 50 + len(slots) * (9 + stops) * 200 for slots in packets) + 20_000
    await ClockCycles(dut.clk, clocks)
    wire.stop()
    decoded = dmx.decode(wire.rec["dmx"])
    assert [slots for _, _, slots in decoded] == packets, decoded
    assert all(break_us >= 88 and mab_us >= 8 for break_us, mab_us, _ in decoded), decoded

    write_vcd("dmx_tx.vcd", wire.rec)
    out = sigrok("dmx_tx.vcd", "dmx512:dmx=dmx", "dmx512")
    if out is not None:
        first = out[:out.index("Invalid")] if "Invalid" in out else out
        values = [int(value) for value in re.findall(r"dmx512-1: (\d+) / 0x", first)]
        assert first.count("Break") == 1 and "MAB" in first, first
        assert values == packets[0], first


@cocotb.test()
async def test_l3_ws2812_tx(dut):
    """L3-WS2812 TX: packed 12-bit tokens sustain two GRB frames at datasheet pulse timing."""
    frame1, frame2 = [0x00, 0xFF, 0x80, 0x12, 0x34, 0x56], [0xA5, 0x5A, 0x0F]

    def tokens(frame):
        bits = "".join(f"{byte:08b}" for byte in frame)
        assert len(bits) % 12 == 0
        return [0xB000 | int(bits[i:i + 12], 2) for i in range(0, len(bits), 12)]

    p = await start(dut, clock=True)
    await load(p, "ws2812")
    wire = Wire(p, lambda uo, uout, uoe, bus: ({0: 1}, None), {"din": lambda uo, bus: uo & 1})
    for token in tokens(frame1):
        await p.push(token)
    await p.push(0, EVENT)
    for token in tokens(frame2):
        await p.push(token)
    await p.push(0, EVENT)

    clocks = (len(frame1) + len(frame2)) * 8 * 77 + 2 * 3100 + 200
    await ClockCycles(dut.clk, clocks)
    wire.stop()
    frames, errs = pulse.ws2812_decode(wire.rec["din"])
    assert errs == [], errs
    assert frames == [frame1, frame2], frames

    write_vcd("ws2812_tx.vcd", wire.rec)
    out = sigrok("ws2812_tx.vcd", "rgb_led_ws281x:din=din", "rgb_led_ws281x=rgb")
    if out is not None:
        colors = re.findall(r"#([0-9a-fA-F]{6})", out)
        grb = [frame1[0:3], frame1[3:6], frame2]
        expected = [bytes([g[1], g[0], g[2]]).hex() for g in grb]
        assert [color.lower() for color in colors] == expected, out


@cocotb.test()
async def test_l3_dshot_tx(dut):
    """L3-DShot TX: lane-computed checksums and 16-bit packets at all four roadmap rates."""
    values = [(0, 0), (48, 0), (1046, 1), (2047, 0), (1000, 1)]
    for i, rate in enumerate((150, 300, 600, 1200)):
        p = await start(dut, clock=i == 0)
        await load(p, "dshot", RATE=rate)
        wire = Wire(p, lambda uo, uout, uoe, bus: ({0: 1}, None), {"dshot": lambda uo, bus: uo & 1})
        for throttle, telemetry in values:
            await p.push(throttle << 1 | telemetry)

        bit = 50_000 // rate
        clocks = len(values) * (18 * bit + 200) + 500
        await ClockCycles(dut.clk, clocks)
        wire.stop()
        frames, errs = pulse.dshot_decode(wire.rec["dshot"], bit)
        assert errs == [], (rate, errs)
        assert frames == [(throttle, telemetry, True) for throttle, telemetry in values], (rate, frames)


async def _servo_edge(dut, level):
    """Wait for UO0 to reach `level`; the testbench exposes UO as a packed vector."""
    async def edge():
        while True:
            await ValueChange(dut.uo_out)
            await ReadOnly()
            if int(dut.uo_out.value) & 1 == level:
                return get_sim_time(unit="ns") // 20

    # Normal frames are20ms; a missing edge must fail rather than hang CI.
    return await with_timeout(edge(), 25, "ms")


async def _servo_pulse(dut):
    """Return the next UO0 servo pulse edges as 50 MHz clock counts."""
    rise = await _servo_edge(dut, 1)
    fall = await _servo_edge(dut, 0)
    return rise, fall


def _write_edge_vcd(path, transitions):
    """Write a 20 ns VCD from sparse (clock, level) edges."""
    lines = [
        "$timescale 20 ns $end", "$scope module chip $end", "$var wire 1 ! pwm $end",
        "$upscope $end", "$enddefinitions $end", "#0", "0!",
    ]
    for clock, level in transitions:
        tick = int(clock)
        if tick != clock:
            raise ValueError("Sparse VCD edge is not on a whole clock")
        lines.append(f"#{tick}\n{level}!")
    with open(path, "w", encoding="ascii") as vcd:
        vcd.write("\n".join(lines) + "\n")


@cocotb.test()
async def test_l3_servo_pwm(dut):
    """L3-PWM: check 20 ms frames and a host update from 1.5 ms to 1.0 ms on UO0."""
    p = await start(dut, clock=True)
    await load(p, "servo")

    # Send the update early in the first high pulse so it takes effect on the next frame.
    first_rise = await _servo_edge(dut, 1)
    await p.push(1000)
    first_fall = await _servo_edge(dut, 0)
    second = await _servo_pulse(dut)
    next_rise = await _servo_edge(dut, 1)

    widths = [first_fall - first_rise, second[1] - second[0]]
    assert widths == [1500 * 50, 1000 * 50], widths
    periods = [second[0] - first_rise, next_rise - second[0]]
    assert periods == [1_000_000] * 2, periods

    # Keep one falling edge after the last measured rising edge. The PWM decoder
    # needs a sample after that edge to finish reporting the preceding period.
    transitions = [
        (first_rise, 1), (first_fall, 0), (second[0], 1), (second[1], 0),
        (next_rise, 1), (next_rise + 1000 * 50, 0),
    ]
    _write_edge_vcd("servo_pwm.vcd", transitions)
    out = sigrok("servo_pwm.vcd", "pwm:data=pwm", "pwm=duty-cycle")
    if out is not None:
        duty = [float(value) for value in re.findall(r"([\d.]+)%", out)]
        runs = [value for i, value in enumerate(duty) if i == 0 or value != duty[i - 1]]
        assert runs == [7.5, 5.0], out


@cocotb.test()
async def test_l3_i2s(dut):
    """L3-I2S: full-duplex 16-bit stereo against reference models at 48/96/192 kHz."""
    samples = [(0x1234, 0xABCD), (0x8000, 0x7FFF), (0x0001, 0xFFFE),
               (0x5A5A, 0xA5A5), (0x0000, 0xFFFF)]
    expect_tx = [(ch, word) for pair in samples for ch, word in zip(("L", "R"), pair)]
    expect_rx = [0] + [word for pair in samples for word in pair][1:]
    for i, fs in enumerate((48_000, 96_000, 192_000)):
        p = await start(dut, clock=i == 0)
        await load(p, "i2s", FS=fs)

        rx, adc = I2SReceiver(), I2SADC(samples)

        def env(uo, uout, uoe, bus):
            sck, sd, ws = uo & 1, uo >> 1 & 1, uo >> 2 & 1
            rx.step(sck, ws, sd)
            return {0: adc.step(sck, ws)}, None

        wire = Wire(p, env, {
            "sck": lambda uo, bus: uo & 1,
            "sd": lambda uo, bus: uo >> 1 & 1,
            "ws": lambda uo, bus: uo >> 2 & 1,
        })
        for sample_index, (left, right) in enumerate(samples):
            try:
                await p.push(left, tries=100)
                await p.push(right, tries=100)
            except AssertionError as exc:
                wire.stop()
                raise AssertionError(
                    f"fs={fs} sample={sample_index} input push: TX={rx.words}, HOST_OUT={p.outq}, "
                    f"wire clocks={wire.clocks}, recent SCK={wire.rec['sck'][-24:]}, "
                    f"WS={wire.rec['ws'][-24:]}, SD={wire.rec['sd'][-24:]}"
                ) from exc
        got = await _drain_host_until(p, lambda: len(rx.words) >= len(expect_tx) - 1,
                                      len(expect_rx) - 1, max_polls=400)
        wire.stop()

        decoded_tx = [(ch, word) for ch, word, nbits in rx.words]
        assert decoded_tx == expect_tx[:len(decoded_tx)], (fs, decoded_tx)
        assert len(decoded_tx) >= len(expect_tx) - 1, (fs, decoded_tx)
        assert all(nbits == 16 for _, _, nbits in rx.words), (fs, rx.words)
        decoded_rx = [data for tag, data in got if tag == EVENT]
        assert decoded_rx == expect_rx[:len(decoded_rx)] and len(decoded_rx) >= len(expect_rx) - 1, (fs, got)

        name = f"i2s_{fs}.vcd"
        write_vcd(name, wire.rec)
        out = sigrok(name, "i2s:sck=sck:ws=ws:sd=sd", "i2s")
        if out is not None:
            decoded = [(channel[0], int(word, 16))
                       for channel, word in re.findall(r"(Left|Right) channel: ([0-9a-f]{8})", out)]
            assert len(decoded) >= len(expect_tx) - 1 and decoded == expect_tx[:len(decoded)], (fs, out)
            warns = re.findall(r"Received (\d+)-bit word, expected (\d+)-bit word", out)
            assert warns in ([], [("16", "15")]), (fs, out)


@cocotb.test()
async def test_l3_spi_controller(dut):
    """L3-SPI-C mode 0 at 5, 1 and 8.3 MHz SCK: CS low, six bytes, CS high; the reference target receives
    them and answers each with the previous one (the first answer 0xA5), which come back on HOST_OUT."""
    data = [0x01, 0x80, 0xFF, 0x3C, 0x00, 0x5A]
    for i, period in enumerate((10, 50, 6)):
        p = await start(dut, clock=i == 0)
        await load(p, "spi_controller", PERIOD=period)
        tgt = SPITarget(first=0xA5)
        w = Wire(p, lambda uo, uout, uoe, bus, tgt=tgt: ({0: tgt.step(uo & 1, uo >> 1 & 1, uo >> 2 & 1)}, None),
                 {"sck": lambda uo, bus: uo & 1, "mosi": lambda uo, bus: uo >> 1 & 1,
                  "cs": lambda uo, bus: uo >> 2 & 1, "miso": lambda uo, bus, tgt=tgt: tgt.miso})
        await p.push(0, EVENT)                               # CS low
        for b in data:
            await p.push(b)                                  # drains HOST_OUT while it waits
        for _ in range(400):
            if len(p.outq) == len(data):
                break
            await p.poll()
        back = [d for _, d in p.outq]
        await p.push(1, EVENT)                               # CS high
        await ClockCycles(dut.clk, 200)
        w.stop()
        assert tgt.received == data, period
        assert back == [0xA5] + data[:-1], period
        write_vcd("spi.vcd", w.rec)
        for cls, want in (("mosi-data", data), ("miso-data", [0xA5] + data[:-1])):
            out = sigrok("spi.vcd", "spi:clk=sck:mosi=mosi:miso=miso:cs=cs", f"spi={cls}")
            if out is not None:
                assert hex_bytes(out, r"spi-\d+: ") == want, (period, cls, out[:300])


@cocotb.test()
async def test_l3_i2c_controller(dut):
    """L3-I2C-C at ~400 kHz (40 clocks of stretching), 100 kHz (none) and 1 MHz (stretching longer than a
    whole SCL period): START W(A0) W(01) W(02) STOP | START W(A2) STOP (another device: NACK) |
    START W(A0) W(05) rSTART W(A1) R R R(NACK) STOP, against the reference target at 0x50 (0x11 0x22 0x33)."""
    for i, (period, stretch) in enumerate(((124, 40), (500, 0), (50, 2 * 50 + 7))):
        p = await start(dut, uio=0xFF, clock=i == 0)
        await load(p, "i2c_controller", PERIOD=period)
        tgt = I2CTarget(0x50, read_data=[0x11, 0x22, 0x33], stretch=stretch)

        def env(uo, uout, uoe, bus, tgt=tgt):
            scl_rel, sda_rel = tgt.step(bus >> 1 & 1, bus & 1)
            return {}, {1: scl_rel, 0: sda_rel}
        w = Wire(p, env, {"sda": lambda uo, bus: bus & 1, "scl": lambda uo, bus: bus >> 1 & 1})
        S, P = (0, EVENT), (0x8000, EVENT)
        W = lambda b: (b, DATA)
        R = lambda nack: (nack, CTRL)
        seq = [S, W(0xA0), W(0x01), W(0x02), P, S, W(0xA2), P,
               S, W(0xA0), W(0x05), S, W(0xA1), R(0), R(0), R(1), P]
        for data, tag in seq:
            await p.push(data, tag)                          # drains the ACK bits and bytes while it waits
        for _ in range(600):
            if len(p.outq) >= 10 and tgt.log and tgt.log[-1] == ("STOP",):
                break
            await p.poll()
        back = [d for _, d in p.outq]
        await ClockCycles(dut.clk, 4 * period)
        w.stop()
        assert back == [0, 0, 0, 1, 0, 0, 0, 0x11, 0x22, 0x33], (period, back)
        assert tgt.received == [0x01, 0x02, 0x05], period
        assert [e for e in tgt.log if e[0] != "ADDR"] == [("START",), ("STOP",)] * 2 + [("START",), ("START",), ("STOP",)]
        assert [e[1:] for e in tgt.log if e[0] == "ADDR"] == [(0xA0, True), (0xA2, False), (0xA0, True), (0xA1, True)]
        write_vcd("i2c.vcd", w.rec)
        out = sigrok("i2c.vcd", "i2c:scl=scl:sda=sda", "i2c")
        if out is not None:
            lines = [ln.split(": ", 1)[1] for ln in out.splitlines() if ": " in ln]
            assert hex_bytes(out, "Data write: ") == [0x01, 0x02, 0x05], period
            assert hex_bytes(out, "Data read: ") == [0x11, 0x22, 0x33], period
            assert lines.count("Start") == 3 and lines.count("Start repeat") == 1 and lines.count("Stop") == 3


async def _drain_host_until(p, done, count, max_polls=400):
    """Drain blocking HOST_OUT while a pin-level reference controller clocks a target program."""
    got = []
    for _ in range(max_polls):
        token = await p.pop()
        if token is not None:
            got.append(token)
        if done() and len(got) >= count:
            break
        await ClockCycles(p.d.clk, 8)
    assert done(), "reference controller did not finish"
    return got


@cocotb.test()
async def test_l3_spi_target(dut):
    """L3-SPI-T mode 0: reference controller clocks a transaction; chip replies and reports CS/MOSI."""
    t1_out, t1_in = [0x01, 0x02, 0x80], [0x5A, 0x3C, 0x0F]
    p = await start(dut, ui=1 << 2)                      # CS high during reset
    await load(p, "spi_target", run=False)
    await p.push(t1_in[0])                                # HOST_IN is a one-token producer

    ctrl = SPIController(half=62, gap=124, tcss=4)       # ~400 kHz; host refills between response bytes
    ctrl.transfer(t1_out)

    def env(uo, uout, uoe, bus):
        sck, mosi, cs = ctrl.step(bus & 1 if uoe & 1 else 1)
        return {0: mosi, 1: sck, 2: cs}, None

    await p.write(HM["run"], [1])                         # RUN lane 0 before the controller starts CS
    wire = Wire(p, env, {
        "sck": lambda uo, bus: ctrl.sck,
        "mosi": lambda uo, bus: ctrl.mosi,
        "cs": lambda uo, bus: ctrl.cs,
        "miso": lambda uo, bus: bus & 1,
    })
    for byte in t1_in[1:]:
        await p.push(byte)
    got = await _drain_host_until(p, ctrl.done, 5)
    wire.stop()

    write_vcd("spi_target.vcd", wire.rec)
    assert ctrl.results == [t1_in], ctrl.results
    observed = [("CS", data >> 15) if tag == EVENT else data & 0xFF for tag, data in got]
    assert observed == [("CS", 0), *t1_out, ("CS", 1)], observed

    for cls, want in (("mosi-data", t1_out), ("miso-data", t1_in)):
        out = sigrok("spi_target.vcd", "spi:clk=sck:mosi=mosi:miso=miso:cs=cs", f"spi={cls}")
        if out is not None:
            assert hex_bytes(out, r"spi-\d+: ") == want, (cls, out[:300])


@cocotb.test()
async def test_l3_i2c_target(dut):
    """L3-I2C-T: reference controller checks target writes, address NACK, and a read at two rates.

    Writes are separate transactions with bus-free time so the host can drain HOST_OUT; sustained 1 MHz
    writes exceed the documented host polling throughput unless firmware buffers them.
    """
    addr = 0x50
    read_data = [0x11]
    written = [0x01, 0x02, 0xA5]
    expected_w = [
        (0xA0, True), (0x01, True), (0xA2, False),
        (0xA0, True), (0x02, True), (0xA0, True), (0xA5, True), (0xA1, True),
    ]
    expected_r = [(0x11, False)]

    for i, cpb in enumerate((125, 50)):
        p = await start(dut, uio=0xFF, clock=i == 0)
        await load(p, "i2c_target", run=False, ADDR=addr)
        await p.push(read_data[0])                         # HOST_IN holds one token at a time

        ctrl = I2CController(clocks_per_bit=cpb)
        ctrl.write(addr, b"\x01")
        ctrl.idle(700)                                      # leave time for the SPI host to drain HOST_OUT
        ctrl.write(addr + 1, b"\x77")                     # wrong address must be ignored
        ctrl.idle(700)
        ctrl.write(addr, b"\x02")
        ctrl.idle(700)
        ctrl.write(addr, b"\xa5")
        ctrl.idle(700)
        ctrl.read(addr, 1)

        def env(uo, uout, uoe, bus):
            scl_release, sda_release = ctrl.step((bus >> 1) & 1, bus & 1)
            return {}, {0: sda_release, 1: scl_release}

        await p.write(HM["run"], [1])
        wire = Wire(p, env, {
            "scl": lambda uo, bus: (bus >> 1) & 1,
            "sda": lambda uo, bus: bus & 1,
        })
        got = await _drain_host_until(p, ctrl.done, len(written), max_polls=100)
        wire.stop()

        assert [data for tag, data in got if tag == DATA] == written, (cpb, got)
        assert all(tag == DATA for tag, _ in got), (cpb, got)
        assert [(entry[1], entry[2]) for entry in ctrl.log if entry[0] == "W"] == expected_w, (cpb, ctrl.log)
        assert [(entry[1], entry[2]) for entry in ctrl.log if entry[0] == "R"] == expected_r, (cpb, ctrl.log)

        name = f"i2c_target_{cpb}.vcd"
        write_vcd(name, wire.rec)
        out = sigrok(name, "i2c:scl=scl:sda=sda", "i2c")
        if out is not None:
            lines = [line.split(": ", 1)[1] for line in out.splitlines() if ": " in line]
            assert hex_bytes(out, "Data write: ") == written, (cpb, out[:300])
            assert hex_bytes(out, "Data read: ") == read_data, (cpb, out[:300])
            # Four writes (including the deliberately wrong address) and one read.
            assert lines.count("Start") == 5 and lines.count("Stop") == 5, (cpb, lines)


@cocotb.test()
async def test_l3_ps2_device_to_host(dut):
    """L3-PS/2 RX: read device frames, reject one bad-parity frame, and decode the bus with sigrok."""
    sent = [0x1C, 0xF0, 0x1C, 0x5A, 0x00, 0xFF]
    bad_parity = {3}
    p = await start(dut, uio=0xFF, clock=True)
    await load(p, "ps2_host")
    device = PS2Device(half=1500, send=sent, bad_parity=bad_parity)
    mark = {"n": 0, "t": 0}

    def sigrok_clk(uo, bus):
        # sigrok 0.5's PS/2 decoder needs a twelfth falling edge to finish an 11-bit frame.
        # Add a short recorder-only clock pulse after each frame; the device and RTL see the real bus.
        if device.frames_sent > mark["n"]:
            mark["n"], mark["t"] = device.frames_sent, 20
        if mark["t"]:
            mark["t"] -= 1
            return 0 if mark["t"] < 10 else (bus >> 1) & 1
        return (bus >> 1) & 1

    def env(uo, uout, uoe, bus):
        clk_release, data_release = device.step((bus >> 1) & 1, bus & 1)
        return {}, {1: clk_release, 0: data_release}

    wire = Wire(p, env, {"clk": sigrok_clk, "data": lambda uo, bus: bus & 1})
    got = []
    for _ in range(1000):
        token = await p.pop()
        if token is not None:
            got.append(token)
        if len(got) >= len(sent) and device.frames_sent == len(sent):
            break
    wire.stop()

    assert device.frames_sent == len(sent), (device.frames_sent, got, p.outq, device.received)
    assert [data for tag, data in got if tag == DATA] == [0x1C, 0xF0, 0x1C, 0x00, 0xFF], got
    errors = [data for tag, data in got if tag == ERR]
    assert len(errors) == 1 and (errors[0] >> 1) & 0xFF == 0x5A, got
    write_vcd("ps2_rx.vcd", wire.rec)
    out = sigrok("ps2_rx.vcd", "ps2:clk=clk:data=data", "ps2")
    if out is not None:
        decoded = [int(value, 16) for value in re.findall(r"Data: ([0-9A-Fa-f]{2})\b", out)]
        assert decoded == sent, out
        assert out.count("Parity error") == 1, out


@cocotb.test()
async def test_l3_ps2_host_to_device(dut):
    """L3-PS/2 TX: request-to-send, odd parity, stop, device ACK, and multiple host bytes."""
    sent = [0xED, 0x02, 0xFF, 0x00]
    p = await start(dut, uio=0xFF, clock=True)
    await load(p, "ps2_host")
    device = PS2Device(half=1500)

    def env(uo, uout, uoe, bus):
        clk_release, data_release = device.step((bus >> 1) & 1, bus & 1)
        return {}, {1: clk_release, 0: data_release}

    wire = Wire(p, env, {"clk": lambda uo, bus: (bus >> 1) & 1,
                         "data": lambda uo, bus: bus & 1})
    for byte in sent:
        await p.push(byte)
    await until(p, lambda: len(device.received) == len(sent), 500_000)
    await ClockCycles(dut.clk, 100)
    wire.stop()

    assert device.received == [(byte, True, True) for byte in sent], device.received
    assert all(tag != ERR for tag, _ in p.outq), p.outq


@cocotb.test()
async def test_l3_onewire_read_rom(dut):
    """L3-1-Wire: reset/presence, READ ROM, 64 LSB-first data bits, and the ROM CRC-8."""
    reset, read = (0, CTRL), (1, CTRL)
    rom7 = [0x28, 0xFF, 0x4C, 0x59, 0x91, 0x16, 0x04]
    expected_rom = rom7 + [crc8(rom7)]
    p = await start(dut, uio=0xFF, clock=True)
    await load(p, "onewire")
    device = OneWireDevice(rom7=rom7)

    def env(uo, uout, uoe, bus):
        release = device.step(bus & 1)
        return {}, {0: release}

    wire = Wire(p, env, {"dq": lambda uo, bus: bus & 1})
    await p.push(*reset)
    await p.push(0x33, DATA)                              # READ ROM command
    for _ in range(8):
        await p.push(*read)                               # one host command reads one byte

    got = []
    for _ in range(1000):
        token = await p.pop()
        if token is not None:
            got.append(token)
        if len(got) == 9:
            break
    wire.stop()

    assert device.resets == 1 and device.received == [0x33], (device.resets, device.received)
    assert got == [(DATA, 0), *[(DATA, byte) for byte in expected_rom]], got
    assert crc8([data for _, data in got[1:8]]) == got[8][1]
    write_vcd("onewire_l3.vcd", wire.rec)
    out = sigrok("onewire_l3.vcd", "onewire_link:owr=dq,onewire_network", "onewire_network")
    if out is not None:
        # The reference device comparison above checks all eight ROM bytes and CRC. The
        # sigrok network decoder reports the command but does not annotate slave ROM data.
        assert "Read ROM" in out, out


@cocotb.test()
async def test_l3_jtag_idcode(dut):
    """L3-JTAG: walk the TAP to Shift-DR and read the target's 32-bit IDCODE over the chip pads."""
    p = await start(dut, ui=1, clock=True)
    await load(p, "jtag", PERIOD=20)
    target = JTAGTarget()

    def env(uo, uout, uoe, bus):
        tdo = target.step(uo & 1, uo >> 1 & 1, uo >> 2 & 1)
        return {0: tdo}, None

    wire = Wire(p, env, {
        "tck": lambda uo, bus: uo & 1,
        "tms": lambda uo, bus: uo >> 1 & 1,
        "tdi": lambda uo, bus: uo >> 2 & 1,
        "tdo": lambda uo, bus: target.tdo,
    })
    sequences = [([1, 1, 1, 1, 1, 0], [0] * 6),
                 ([1, 0, 0] + [0] * 31 + [1, 1, 0], [0] * 37)]
    chunk_lengths = []
    for tms, tdi in sequences:
        for offset in range(0, len(tms), 12):
            m, d = tms[offset:offset + 12], tdi[offset:offset + 12]
            count = len(m)
            chunk_lengths.append(count)
            await p.push((count - 1) << 12 | sum(bit << i for i, bit in enumerate(m)), EVENT)
            await p.push((count - 1) << 12 | sum(bit << i for i, bit in enumerate(d)), DATA)

    captured = []
    for count in chunk_lengths:
        token = await p.pop()
        assert token is not None and token[0] == EVENT, (count, token, p.outq)
        captured.extend((token[1] >> i) & 1 for i in range(count))
    wire.stop()

    assert target.state == "RTI" and target.ir == IDCODE, (target.state, target.ir)
    assert sum(bit << i for i, bit in enumerate(captured[9:41])) == target.idcode, captured
    write_vcd("jtag_idcode.vcd", wire.rec)
    out = sigrok("jtag_idcode.vcd", "jtag:tdi=tdi:tdo=tdo:tck=tck:tms=tms", "jtag=bitstring-tdo")
    if out is not None:
        decoded = [int(bits, 2) for bits in re.findall(r"TDO: ([01]{32})\b", out)]
        assert target.idcode in decoded, out


@cocotb.test()
async def test_l3_smbus_word_pec(dut):
    """L3-SMBus: write and read a word with PEC checked independently by a reference device."""
    addr, period = 0x2C, 124
    aw, ar = addr << 1, (addr << 1) | 1
    start_event, stop_event = (0, EVENT), (0x8000, EVENT)
    write = lambda byte: (byte, DATA)
    read = lambda nack: (nack, CTRL)
    expected_pec_read = smbus_crc8([aw, 0x05, ar, 0xEF, 0xBE])
    expected_pec_write = smbus_crc8([aw, 0x10, 0x34, 0x12])
    expected_pec_readback = smbus_crc8([aw, 0x10, ar, 0x34, 0x12])
    device = SMBusDevice(addr, regs={0x05: 0xBEEF})
    p = await start(dut, uio=0xFF, clock=True)
    await load(p, "smbus", PERIOD=period)

    def env(uo, uout, uoe, bus):
        scl_release, sda_release = device.step((bus >> 1) & 1, bus & 1)
        return {}, {0: sda_release, 1: scl_release}

    wire = Wire(p, env, {"sda": lambda uo, bus: bus & 1,
                         "scl": lambda uo, bus: (bus >> 1) & 1})
    sequence = [
        start_event, write(aw), write(0x10), write(0x34), write(0x12), (0x8000, DATA), stop_event,
        start_event, write(aw), write(0x05), start_event, write(ar), read(0), read(0), read(1), stop_event,
        start_event, write(aw), write(0x10), start_event, write(ar), read(0), read(0), read(1), stop_event,
    ]
    for data, tag in sequence:
        await p.push(data, tag)

    expected = ([(DATA, 0)] * 5 + [(EVENT, 0)]
                + [(DATA, 0)] * 3 + [(DATA, 0xEF), (DATA, 0xBE), (DATA, expected_pec_read), (EVENT, 0)]
                + [(DATA, 0)] * 3 + [(DATA, 0x34), (DATA, 0x12), (DATA, expected_pec_readback), (EVENT, 0)])
    got = []
    for _ in range(1000):
        token = await p.pop()
        if token is not None:
            got.append(token)
        if len(got) == len(expected):
            break
    wire.stop()

    if got != expected:
        mismatch = [(i, actual, wanted) for i, (actual, wanted) in enumerate(zip(got, expected))
                    if actual != wanted]
        raise AssertionError(f"SMBus HOST_OUT mismatch at {mismatch[:4]}; lengths {len(got)}/{len(expected)}; "
                             f"got={got}; expected={expected}; device writes={device.writes}; "
                             f"device log={device.log[-24:]}")
    assert device.writes == [(0x10, [0x34, 0x12], True)], device.writes
    assert device.regs[0x10] == 0x1234
    write_vcd("smbus_pec.vcd", wire.rec)
    out = sigrok("smbus_pec.vcd", "i2c:scl=scl:sda=sda", "i2c")
    if out is not None:
        assert hex_bytes(out, "Data write: ") == [0x10, 0x34, 0x12, expected_pec_write, 0x05, 0x10], out
        assert hex_bytes(out, "Data read: ") == [0xEF, 0xBE, expected_pec_read,
                                                  0x34, 0x12, expected_pec_readback], out


@cocotb.test()
async def test_l3_swd_dpidr_read_with_wait_retry(dut):
    """L3-SWD: receive WAIT, retry a DP IDCODE read, and check turnaround has no bus contention."""
    period = 6                                    # 8.3 MHz SWCLK, the program's supported ceiling
    p = await start(dut, uio=0xFF, clock=True)
    await load(p, "swd", PERIOD=period)
    target = SWDTarget(wait_on={0})
    rec = {"swclk": [], "swdio": []}
    contentions = {"n": 0}

    async def bus_task():
        while True:
            await RisingEdge(dut.clk)
            await ReadOnly()
            swclk = int(dut.uo_out.value) & 1
            uio_out, uio_oe = int(dut.uio_out.value), int(dut.uio_oe.value)
            host_oe = uio_oe & 1
            if host_oe and target.oe:
                contentions["n"] += 1
            dio = (uio_out & 1) if host_oe else (target.value if target.oe else 1)
            rec["swclk"].append(swclk)
            rec["swdio"].append(dio)
            target.step(swclk, dio)
            await FallingEdge(dut.clk)
            dut.uio_in.value = 0xFE | dio

    task = cocotb.start_soon(bus_task())
    request = 1 | (1 << 2) | (1 << 5) | (1 << 7)       # start, RnW, request parity, park
    token = 0x7000 | request
    await p.push(token, DATA)                            # first request gets WAIT
    await p.push(token, DATA)                            # identical retry gets OK + DPIDR
    got = []
    for _ in range(200):
        response = await p.pop()
        if response is not None:
            got.append(response)
        if len(got) == 5:
            break
    await ClockCycles(dut.clk, 4 * period)
    task.cancel()

    expected = [(DATA, SWD_WAIT), (DATA, SWD_OK), (DATA, DPIDR & 0xFFFF),
                (DATA, DPIDR >> 16)]
    assert got[:4] == expected and len(got) == 5, got
    # RX2 returns parity in bit 0 and the following turnaround sample in bit 1.
    assert got[4][0] == DATA and got[4][1] & 1 == swd_parity(DPIDR), got
    assert contentions["n"] == 0, contentions
    assert target.protocol_errors == 0 and [entry[4] for entry in target.log] == [SWD_WAIT, SWD_OK], target.log
    write_vcd("swd_dpidr.vcd", rec)
    out = sigrok("swd_dpidr.vcd", "swd:swclk=swclk:swdio=swdio", "swd")
    if out is not None:
        assert "WAIT" in out and "IDCODE" in out and "OK" in out, out
        values = [int(value, 16) for value in re.findall(r"0x([0-9a-f]{8})", out)]
        assert DPIDR in values, out


@cocotb.test()
async def test_l3_hdlc_tx_loopback(dut):
    """L3-HDLC: firmware TX flags, stuffing and FCS decode correctly and loop back as valid RX frames."""
    period = 500                                  # leave the SPI host enough bandwidth to queue frame bytes
    frames = [[0x03, 0x3F, 0x7E, 0xFF, 0x7D]]
    p = await start(dut, ui=1, clock=True)
    await load(p, "hdlc", BAUD=100_000)
    await ClockCycles(dut.clk, period * 12)              # settle to the firmware's idle-high line
    delay = [1, 1, 1]

    def env(uo, uout, uoe, bus):
        delayed_tx = delay.pop(0)
        delay.append(uo & 1)
        return {0: delayed_tx}, None

    wire = Wire(p, env, {"tx": lambda uo, bus: uo & 1})
    for frame in frames:
        for byte in frame:
            await p.push(byte)
        await p.push(0, EVENT)

    got = []

    async def drain_frames():
        while sum(tag in (EVENT, ERR) for tag, _ in got) < len(frames):
            token = await p.pop()
            if token is not None:
                got.append(token)

    drain_task = cocotb.start_soon(drain_frames())
    await ClockCycles(dut.clk, period * 200)
    drain_task.cancel()
    wire.stop()

    line = wire.rec["tx"]
    first_zero = line.index(0)
    sampled_bits = [line[k] for k in range(first_zero % period + period // 2, len(line), period)]
    write_vcd("hdlc_l3.vcd", wire.rec)
    decoded = hdlc.decode(sampled_bits)
    assert decoded == [(frame, True) for frame in frames], (decoded, got, first_zero, len(line))

    received, current = [], []
    for tag, data in got:
        if tag == DATA:
            current.append(data)
        else:
            assert tag == EVENT, (tag, data, got)
            received.append(current[:-2])
            current = []
    assert received == frames and current == [], (received, current, got)


@cocotb.test()
async def test_l3_lin_commander_publish_response(dut):
    """L3-LIN: send a protected-ID header and receive a responder's enhanced-checksum payload."""
    baud, fid, data = 100_000, 0x10, [0x11, 0x22, 0x33, 0x44]
    period = round(50_000_000 / baud)
    node = LINResponder(period, publish={fid: data})
    p = await start(dut, ui=1, clock=True)
    await load(p, "lin", BAUD=baud)
    line = {"level": 1}

    def env(uo, uout, uoe, bus):
        level = (uo & 1) & node.drive
        line["level"] = level
        node.step(level)
        return {0: level}, None

    wire = Wire(p, env, {"lin": lambda uo, bus: line["level"]})
    await p.push((len(data) << 8) | fid, EVENT)
    got = []

    async def drain_response():
        while not any(tag == EVENT for tag, _ in got):
            token = await p.pop()
            if token is not None:
                got.append(token)

    drain_task = cocotb.start_soon(drain_response())
    await ClockCycles(dut.clk, round(220 * period))
    drain_task.cancel()
    wire.stop()

    expected = [(DATA, b) for b in data] + [(EVENT, 0)]
    assert node.headers == [(fid, True)], node.headers
    assert got == expected, got
    write_vcd("lin_l3.vcd", wire.rec)
    out = sigrok("lin_l3.vcd", f"uart:rx=lin:baudrate={baud},lin", "lin")
    if out is not None:
        ids = [int(value, 16) for value in re.findall(r"ID: ([0-9A-F]{2}) Parity: \d \(ok\)", out)]
        checksums = [int(value, 16) for value in re.findall(r"Checksum: 0x([0-9A-F]{2})", out)]
        # sigrok's LIN annotation gives the six-bit frame ID; PID parity is reported
        # separately as "ok". The protected ID is checked by the independent responder.
        assert ids == [fid] and checksums == [lin_checksum(fid, data)], out


@cocotb.test()
async def test_l3_can_standard_frame_and_ack(dut):
    """L3-CAN: transmit a standard data frame, receive ACK, and self-monitor the CRC-valid bus frame."""
    period, can_id, data = 400, 0x123, [0xDE, 0xAD]
    node = CANNode(period)
    p = await start(dut, ui=1, clock=True)
    await load(p, "can", PERIOD=period)
    history = [1] * 5
    line = {"level": 1}

    def env(uo, uout, uoe, bus):
        level = (uo & 1) & node.drive
        history.append(level)
        rx = history.pop(0)
        line["level"] = level
        node.step(level)
        return {0: rx}, None

    wire = Wire(p, env, {"can": lambda uo, bus: line["level"]})
    await p.push(0, CTRL)                             # error-active, transmit enabled
    await p.push(len(data), EVENT)
    await p.push(can_id, DATA)
    for byte in data:
        await p.push(byte, DATA)
    await p.push(0, EVENT)
    await ClockCycles(dut.clk, 170 * period)

    got = []
    for _ in range(60):
        token = await p.pop()
        if token is not None:
            got.append(token)
        tx_done = any(tag == EVENT and value & 0xE000 == 0xA000 for tag, value in got)
        if tx_done:
            break
    wire.stop()

    expected_frame = {"id": can_id, "data": data, "ext": False, "rtr": False,
                      "dlc": len(data), "crc_ok": True}
    assert node.received == [expected_frame], node.received
    assert node.errors == [], node.errors
    assert any(tag == EVENT and value == 0x9001 for tag, value in got), got
    assert tx_done, got
    write_vcd("can_l3.vcd", wire.rec)
    out = sigrok("can_l3.vcd", f"can:can_rx=can:nominal_bitrate={50_000_000 // period}:sample_point=75", "can")
    if out is not None:
        ids = [int(value, 16) for value in re.findall(r"Identifier: \d+ \(0x([0-9a-f]+)\)", out)]
        assert ids == [can_id] and "ACK slot: ACK" in out and "error" not in out.lower(), out


@cocotb.test()
async def test_l3_ir_nec_repeat_rx(dut):
    """L3-IR NEC: detect a valid active-low 9 ms leader and 2.25 ms repeat space on ui0."""
    mark = round(nec.MARK)
    segments = [(0, 16 * mark), (1, 4 * mark), (0, mark), (1, 4 * mark)]
    total_clocks = sum(clocks for _, clocks in segments)

    p = await start(dut, ui=1, clock=True)
    await load(p, "ir_nec")
    await ClockCycles(dut.clk, 4 * mark)               # stable idle before the test waveform
    startup = await p.pop()
    assert startup is None, f"IR receiver emitted a token during idle: {startup}"

    state = {"index": 0, "remaining": segments[0][1]}

    def env(uo, uout, uoe, bus):
        index = state["index"]
        level = segments[index][0] if index < len(segments) else 1
        if index < len(segments):
            state["remaining"] -= 1
            if state["remaining"] == 0:
                state["index"] += 1
                if state["index"] < len(segments):
                    state["remaining"] = segments[state["index"]][1]
        return {0: level}, None

    wire = Wire(p, env, {"ir_rx": lambda uo, bus: bus & 1})
    await ClockCycles(dut.clk, total_clocks + 100)
    wire.stop()

    got = []
    for _ in range(4):
        token = await p.pop()
        if token is not None:
            got.append(token)
    assert got == [(EVENT, 0)], got
