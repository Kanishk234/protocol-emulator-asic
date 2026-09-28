"""L3 on the RTL (VERIFICATION.md §6): the three phase 2 protocols on trw_chip, through its pins only. Each
program is compiled by tripc from programs/, loaded with tools/host over the SPI pins, and checked against
the reference models in tools/protomodels (written from the protocol specifications) and against sigrok's
decoders on a VCD of the pads (an oracle we did not write, §9 rule 3).

  L3-UART   programs/uart.trw            TX at 1 Mbaud and 115200 (model + sigrok `uart`); RX with a framing error
  L3-SPI-C  programs/spi_controller.trw  mode 0 against the reference target (model + sigrok `spi`)
  L3-I2C-C  programs/i2c_controller.trw  writes, NACK, repeated START, reads, clock stretching (model + sigrok `i2c`)
"""

import cocotb
from cocotb.triggers import ClockCycles

from chiplib import TAGS, Wire, hex_bytes, load, sigrok, start, write_vcd
from protomodels import uart
from protomodels.i2c import I2CTarget
from protomodels.spi import SPITarget

DATA, CTRL, EVENT, ERR = (TAGS[t] for t in ("DATA", "CTRL", "EVENT", "ERR"))
MSG = b"TRIPWIRE\x00\xff\x55"


async def until(p, cond, clocks, step=50):
    for _ in range(clocks // step):
        if cond():
            return True
        await ClockCycles(p.d.clk, step)
    return cond()


@cocotb.test()
async def test_l3_uart_tx(dut):
    """L3-UART TX: bytes pushed into HOST_IN leave on uo0 as 8N1 frames at the programmed rate."""
    for baud in (1_000_000, 115_200):
        cpb = 50e6 / baud
        p = await start(dut)
        await load(p, "uart", BAUD=baud)
        w = Wire(p, lambda uo, uout, uoe, bus: ({0: 1}, None), {"tx": lambda uo, bus: uo & 1})
        for b in MSG:
            await p.push(b)
        n = round((len(MSG) * 10 + 20) * cpb)
        await until(p, lambda: len(uart.decode(w.rec["tx"], cpb)) == len(MSG) and w.clocks > n // 2, 4 * n)
        await ClockCycles(dut.clk, round(20 * cpb))
        w.stop()
        assert uart.decode(w.rec["tx"], cpb) == [(b, True) for b in MSG], baud
        assert await p.read(0x0010, 1) == [0], "U0: no OVERRUN or LATE"
        write_vcd("uart_tx.vcd", w.rec)
        out = sigrok("uart_tx.vcd", f"uart:rx=tx:baudrate={baud}:format=hex", "uart=rx-data")
        if out is not None:
            assert bytes(hex_bytes(out, r"uart-\d+: ")) == MSG, (baud, out[:200])


@cocotb.test()
async def test_l3_uart_rx_framing(dut):
    """L3-UART RX: a reference waveform on ui0 at 460800 baud, byte 3 with a broken stop bit: the good bytes
    arrive as DATA, the broken frame as one ERR token carrying the raw frame, and nothing overruns. (The
    rate is one the host link can drain: at SCK = clk/8 a HOST_OUT read takes ~560 clocks; faster streams
    need a lane that buffers, or a faster host clock.)"""
    baud = 460_800
    cpb = 50e6 / baud
    wave = uart.encode(MSG, cpb, bad_stop={3})
    p = await start(dut, ui=1)                          # idle-high line through reset
    await load(p, "uart", BAUD=baud)
    it = iter(wave)
    w = Wire(p, lambda uo, uout, uoe, bus: ({0: next(it, 1)}, None), {"rx": lambda uo, bus: 0})
    got = []
    for _ in range(400):
        tok = await p.pop()
        if tok:
            got.append(tok)
        if len(got) == len(MSG):
            break
    w.stop()
    assert [d for t, d in got if t == DATA] == [b for i, b in enumerate(MSG) if i != 3], got
    errs = [d for t, d in got if t == ERR]
    assert len(errs) == 1 and errs[0] >> 1 & 0xFF == MSG[3] and not errs[0] >> 9 & 1, got
    assert await p.read(0x0011, 1) == [0], "U1: no OVERRUN"


@cocotb.test()
async def test_l3_spi_controller(dut):
    """L3-SPI-C mode 0 at 5 MHz SCK: CS low, six bytes, CS high; the reference target receives them and
    answers each with the previous one (the first answer 0xA5), which come back on HOST_OUT."""
    data = [0x01, 0x80, 0xFF, 0x3C, 0x00, 0x5A]
    p = await start(dut)
    await load(p, "spi_controller", PERIOD=10)
    tgt = SPITarget(first=0xA5)
    w = Wire(p, lambda uo, uout, uoe, bus: ({0: tgt.step(uo & 1, uo >> 1 & 1, uo >> 2 & 1)}, None),
             {"sck": lambda uo, bus: uo & 1, "mosi": lambda uo, bus: uo >> 1 & 1,
              "cs": lambda uo, bus: uo >> 2 & 1, "miso": lambda uo, bus: tgt.miso})
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
    assert tgt.received == data
    assert back == [0xA5] + data[:-1]
    write_vcd("spi.vcd", w.rec)
    for cls, want in (("mosi-data", data), ("miso-data", [0xA5] + data[:-1])):
        out = sigrok("spi.vcd", "spi:clk=sck:mosi=mosi:miso=miso:cs=cs", f"spi={cls}")
        if out is not None:
            assert hex_bytes(out, r"spi-\d+: ") == want, (cls, out[:300])


@cocotb.test()
async def test_l3_i2c_controller(dut):
    """L3-I2C-C at ~400 kHz with 40 clocks of clock stretching: START W(A0) W(01) W(02) STOP | START W(A2)
    STOP (another device: NACK) | START W(A0) W(05) rSTART W(A1) R R R(NACK) STOP, against the reference
    target at 0x50, which serves 0x11 0x22 0x33."""
    p = await start(dut, uio=0xFF)
    await load(p, "i2c_controller", PERIOD=124)
    tgt = I2CTarget(0x50, read_data=[0x11, 0x22, 0x33], stretch=40)

    def env(uo, uout, uoe, bus):
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
    for _ in range(300):
        if len(p.outq) >= 10 and tgt.log and tgt.log[-1] == ("STOP",):
            break
        await p.poll()
    back = [d for _, d in p.outq]
    await ClockCycles(dut.clk, 500)
    w.stop()
    assert back == [0, 0, 0, 1, 0, 0, 0, 0x11, 0x22, 0x33], back
    assert tgt.received == [0x01, 0x02, 0x05]
    assert [e for e in tgt.log if e[0] != "ADDR"] == [("START",), ("STOP",)] * 2 + [("START",), ("START",), ("STOP",)]
    assert [e[1:] for e in tgt.log if e[0] == "ADDR"] == [(0xA0, True), (0xA2, False), (0xA0, True), (0xA1, True)]
    write_vcd("i2c.vcd", w.rec)
    out = sigrok("i2c.vcd", "i2c:scl=scl:sda=sda", "i2c")
    if out is not None:
        lines = [ln.split(": ", 1)[1] for ln in out.splitlines() if ": " in ln]
        assert hex_bytes(out, "Data write: ") == [0x01, 0x02, 0x05]
        assert hex_bytes(out, "Data read: ") == [0x11, 0x22, 0x33]
        assert lines.count("Start") == 3 and lines.count("Start repeat") == 1 and lines.count("Stop") == 3
