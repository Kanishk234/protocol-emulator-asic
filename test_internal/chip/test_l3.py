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

The tests provide implementation-level evidence for these exercised cases only. Other roadmap programs need
matching RTL and hardened-netlist checks before they have implementation-level evidence.
"""

import importlib.util
import os
import re
from pathlib import Path

import cocotb
from cocotb.triggers import ClockCycles, ReadOnly, ValueChange
from cocotb.utils import get_sim_time

from chiplib import HM, TAGS, Wire, hex_bytes, load as _load, sigrok, start, write_vcd
from protomodels import dmx, pulse, uart
from protomodels.i2c import I2CController, I2CTarget
from protomodels.i2s import I2SADC, I2SReceiver
from protomodels.spi import SPIController, SPITarget

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
    while True:
        await ValueChange(dut.uo_out)
        await ReadOnly()
        if int(dut.uo_out.value) & 1 == level:
            return get_sim_time(unit="ns") // 20


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
    lines.extend(f"#{clock}\n{level}!" for clock, level in transitions)
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
