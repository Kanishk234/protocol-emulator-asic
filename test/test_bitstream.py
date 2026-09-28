# SPDX-FileCopyrightText: © 2026 Kanishk Sama
# SPDX-License-Identifier: Apache-2.0
#
# Real bitstreams on the whole chip (VERIFICATION V4/V6): user designs compiled by tools/compile
# (test/bitstreams/*.wbit, from tools/compile/examples) are loaded through the host SPI interface
# and their behaviour is checked at the pins. Two different bitstreams, loaded one after the
# other into the same chip. Top-level ports only.
#
# Needs a fabric model: WARP_FABRIC=rtl (generated fabric RTL) or gl (CI gl_test: the hardened
# macro's netlists). With the default black box (CI `test` job) these tests are skipped.

import os
import sys
from pathlib import Path

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge, Timer

from warp_host import bit, expect, parked, reset
from compile.bitfile import BitFile
from host.protocol import (ErrorCode, Op, State, checked_load_transactions, parse_byte, parse_read_id,
                           tx_ch_read, tx_ch_write, tx_read_id, tx_simple, tx_user_status)

BITS = Path(__file__).resolve().parent / "bitstreams"
REAL_FABRIC = os.environ.get("WARP_FABRIC", "stub") in ("rtl", "gl")


def fab_out(dut):
    return (int(dut.uo_out.value) >> 2) & 0xF          # FAB_OUT0..3 (the example designs' four)


async def settle_routing_loops(dut):
    """Real fabric models only (D-023). The fabric's unused routing sits on default mux inputs
    and forms combinational loops; in 4-state simulation a loop that starts at X stays X, and the
    gate-level LUTs pass X on from inputs the configured function ignores. In silicon such a loop
    always holds some definite 0/1. With the configuration loaded (mux selects known) and the
    design still held in reset, tb.v pulses the inter-tile routing wires to 0 for 1 ns
    (test/fabric_settle_{gl,rtl}.vh), so each loop settles to a definite value. Used routing is
    driven again by its source at once; the configuration path is not touched."""
    dut.settle_routing.value = 1
    await Timer(2, "ns")
    dut.settle_routing.value = 0
    await Timer(1, "ns")


def hold_x(dut, on):
    """Real fabric models only (D-023): while a configuration is written over another, a
    half-written one can close a loop that rings; silicon rings until the load completes (design
    in reset, pins parked), a zero-delay simulator never gets past it. So tb.v holds the fabric's
    nets (not the configuration path) at X for the whole load; the latches update underneath."""
    if REAL_FABRIC:
        dut.hold_x.value = 1 if on else 0


async def leave_fabric(dut):
    """End of a real-fabric test: the fabric is frozen at X until the next load (D-023)."""
    await ClockCycles(dut.clk, 1)
    hold_x(dut, True)
    await Timer(1, "ns")


async def load_and_run(host, name):
    bf = BitFile.load(BITS / f"{name}.wbit")
    ok, chip_arch = parse_read_id(await host.xfer(tx_read_id()))
    assert ok
    hold_x(host.dut, True)
    await Timer(1, "ns")
    for i, t in enumerate(checked_load_transactions(bf.words, bf.arch_version, chip_arch, chunk=16)):
        host.dut._log.debug(f"{name}: load transaction {i}")
        await host.xfer(t)
    await expect(host, State.LOADED)
    hold_x(host.dut, False)
    await Timer(1, "ns")
    host.dut._log.info(f"{name}: loaded")
    if REAL_FABRIC:
        await settle_routing_loops(host.dut)
        host.dut._log.info(f"{name}: routing settled")
    await host.xfer(tx_simple(Op.RUN))
    await expect(host, State.RUNNING)


@cocotb.test(skip=not REAL_FABRIC)
async def test_counter4(dut):
    host = await reset(dut)
    await load_and_run(host, "counter4")

    host.set_fab_in(0b00)                               # en = 0: holds
    await ClockCycles(dut.clk, 8)
    held = fab_out(dut)
    await ClockCycles(dut.clk, 20)
    assert fab_out(dut) == held, "counter must hold while en is low"

    host.set_fab_in(0b01)                               # en = 1: counts every clk
    await ClockCycles(dut.clk, 8)
    a = fab_out(dut)
    await ClockCycles(dut.clk, 5)
    b = fab_out(dut)
    assert (b - a) % 16 == 5, f"counted {a} -> {b} in 5 clk"

    # FAB_IO0: input while dir = 0 (oe 0); FAB_IO1 echoes its pad value
    host.set_fab_in(0b00)
    for v in (0, 1, 0):
        dut.uio_in.value = v
        await ClockCycles(dut.clk, 6)
        assert bit(dut.uio_oe, 0) == 0
        assert bit(dut.uio_oe, 1) == 1 and bit(dut.uio_out, 1) == v
    # dir = 1: FAB_IO0 drives the counter LSB
    host.set_fab_in(0b10)
    await ClockCycles(dut.clk, 6)
    assert bit(dut.uio_oe, 0) == 1
    assert bit(dut.uio_out, 0) == fab_out(dut) & 1

    # USER_RESET clears the counter; STOP parks every fabric pin
    host.set_fab_in(0b00)
    await host.xfer(tx_simple(Op.USER_RESET))
    await ClockCycles(dut.clk, 6)
    assert fab_out(dut) == 0
    await host.xfer(tx_simple(Op.STOP))
    assert parked(dut)
    await leave_fabric(dut)


async def check_logic4(dut, host):
    for a in range(16):
        host.set_fab_in(a)
        await ClockCycles(dut.clk, 6)
        a0, a1, a2, a3 = (a >> 0) & 1, (a >> 1) & 1, (a >> 2) & 1, (a >> 3) & 1
        want = (a0 & a1) | (a0 ^ a1) << 1 | (1 - a2) << 2 | (a2 ^ a3) << 3
        assert fab_out(dut) == want, f"a={a:04b}: {fab_out(dut):04b} != {want:04b}"
        # FAB_IO2 open drain: pulled low (oe 1, out 0) while a3, released otherwise
        assert bit(dut.uio_oe, 2) == a3 and bit(dut.uio_out, 2) == 0
    # the open-drain pad's value is echoed on FAB_IO3
    host.set_fab_in(0)
    for v in (0, 1):
        dut.uio_in.value = v << 2
        await ClockCycles(dut.clk, 6)
        assert bit(dut.uio_out, 3) == v


@cocotb.test(skip=not REAL_FABRIC)
async def test_two_bitstreams(dut):
    """Load counter4, then logic4 into the same chip: the second design fully replaces the first."""
    host = await reset(dut)
    await load_and_run(host, "counter4")
    host.set_fab_in(0b01)
    await ClockCycles(dut.clk, 10)
    await host.xfer(tx_simple(Op.STOP))
    await load_and_run(host, "logic4")
    await check_logic4(dut, host)
    await leave_fabric(dut)


@cocotb.test(skip=not REAL_FABRIC)
async def test_logic4(dut):
    """The second bitstream on its own. Runs last (D-023): the tests share one simulation and the
    configuration latches survive reset, so each load writes over the previous test's design; with
    the RTL fabric model, loading counter4 over logic4 passes through a half-written configuration
    whose routing loop oscillates, which a zero-delay simulator cannot step past (silicon rings
    until the load ends, design in reset, pins parked). Gate level handles any order."""
    host = await reset(dut)
    await load_and_run(host, "logic4")
    await check_logic4(dut, host)
    await leave_fabric(dut)


@cocotb.test(skip=not REAL_FABRIC)
async def test_host_channel(dut):
    """ARCHITECTURE §7.3 end to end through the fabric (hostecho): bytes written with CH_WRITE
    come back plus one from CH_READ; USER_STATUS counts them; a byte marked last raises the
    design's attention (STATUS bit 1 and HOST_IRQ)."""
    host = await reset(dut)
    await load_and_run(host, "hostecho")
    st = await host.status()
    assert st.tx_ready and not st.rx_valid and not st.user_attention
    sent = [0x10, 0x7F, 0xFF]
    for i, b in enumerate(sent):
        await host.xfer(tx_ch_write(b, last=(i == len(sent) - 1)))
        await ClockCycles(dut.clk, 8)
        st = await host.status()
        assert st.rx_valid, f"no reply to byte {i}"
        assert parse_byte(await host.xfer(tx_ch_read())) == (b + 1) & 0xFF
    st = await host.status()
    assert not st.rx_valid and st.user_attention and bit(dut.uo_out, 1) == 1
    assert parse_byte(await host.xfer(tx_user_status())) == len(sent)
    await host.xfer(tx_simple(Op.USER_RESET))
    await ClockCycles(dut.clk, 4)
    assert not (await host.status()).user_attention
    assert parse_byte(await host.xfer(tx_user_status())) == 0
    await host.xfer(tx_simple(Op.STOP))
    await leave_fabric(dut)


def fab_out6(dut):
    return (int(dut.uo_out.value) >> 2) & 0x3F         # FAB_OUT0..5


@cocotb.test(skip=not REAL_FABRIC)
async def test_prims(dut):
    """The hard primitives (D-026, ARCHITECTURE §8) configured by a real bitstream (prims2): a
    timer with RELOAD 5 pulses every 6 enabled clocks (tick toggles FAB_OUT0); a 6-step LSB-first
    shift register loads 0xA5, shifts on each `step` pulse and raises `done` after 6."""
    host = await reset(dut)
    host.set_fab_in(0)
    await load_and_run(host, "prims2")

    # timer: with en high, FAB_OUT0 toggles exactly every 6 clocks
    host.set_fab_in(0b0001)
    await ClockCycles(dut.clk, 10)
    edges, prev, t = [], fab_out6(dut) & 1, 0
    while len(edges) < 4 and t < 60:
        await ClockCycles(dut.clk, 1)
        t += 1
        v = fab_out6(dut) & 1
        if v != prev:
            edges.append(t)
        prev = v
    assert len(edges) == 4, f"tick toggled {len(edges)} times in 60 clk"
    assert [b - a for a, b in zip(edges, edges[1:])] == [6, 6, 6], f"toggle times {edges}"
    host.set_fab_in(0)                                   # en low: no more ticks
    await ClockCycles(dut.clk, 6)
    held = fab_out6(dut) & 1
    await ClockCycles(dut.clk, 20)
    assert fab_out6(dut) & 1 == held

    def shift_state():
        o = fab_out6(dut)
        q = ((o >> 4) & 1) | ((o >> 5) & 1) << 1 | (bit(dut.uio_out, 0) << 2) | (bit(dut.uio_out, 1) << 3)
        return (o >> 2) & 1, (o >> 3) & 1, q            # sout, done, q[3:0]

    host.set_fab_in(0b0010)                              # load 0xA5
    await ClockCycles(dut.clk, 2)
    host.set_fab_in(0)
    await ClockCycles(dut.clk, 6)
    assert shift_state() == (1, 0, 0x5), f"after load: {shift_state()}"
    sr = 0xA5
    for n in range(1, 7):                                # sin = 0
        host.set_fab_in(0b0100)                          # one step (a 1-clock pulse at the pin)
        await ClockCycles(dut.clk, 1)
        host.set_fab_in(0)
        await ClockCycles(dut.clk, 6)
        sr >>= 1
        want = (sr & 1, int(n == 6), sr & 0xF)
        assert shift_state() == want, f"after step {n}: {shift_state()} != {want}"
    await host.xfer(tx_simple(Op.STOP))
    assert parked(dut)
    await leave_fabric(dut)


UART_DIV = 16                                           # tools/compile/examples/uart16.yaml


@cocotb.test(skip=not REAL_FABRIC)
async def test_uart(dut):
    """The design-set UART on the hard primitives (uart16) through the host interface: bytes
    written with CH_WRITE leave on FAB_OUT0 as 8N1 frames; frames driven into FAB_IN0 arrive
    through CH_READ."""
    host = await reset(dut)
    host.set_fab_in(1)                                   # RX line idle high
    await load_and_run(host, "uart16")

    wave = []

    async def record(n):
        for _ in range(n):
            await ClockCycles(dut.clk, 1)
            wave.append(bit(dut.uo_out, 2))

    def decode(w):
        """8N1 frames in a line sampled once per clock (mid-bit sampling)."""
        out, i = [], 0
        while i < len(w) - 10 * UART_DIV:
            if w[i] == 0:
                mid = i + UART_DIV // 2
                assert w[mid] == 0, "start bit too short"
                out.append(sum(w[mid + (k + 1) * UART_DIV] << k for k in range(8)))
                assert w[mid + 9 * UART_DIV] == 1, "stop bit"
                i = mid + 9 * UART_DIV
            else:
                i += 1
        return out

    sent = [0x55, 0x00, 0xC3]
    rec = cocotb.start_soon(record(40 * UART_DIV + 2000))
    for b in sent:
        await host.xfer(tx_ch_write(b))
    await rec
    assert decode(wave) == sent

    for b in (0xA5, 0x3C):
        for level in [0] + [(b >> i) & 1 for i in range(8)] + [1]:
            host.set_fab_in(level)
            await ClockCycles(dut.clk, UART_DIV)
        await ClockCycles(dut.clk, 4 * UART_DIV)
        assert (await host.status()).rx_valid, f"byte {b:#04x} not received"
        assert parse_byte(await host.xfer(tx_ch_read())) == b
    assert parse_byte(await host.xfer(tx_user_status())) & 0x06 == 0   # no overrun, no framing error
    await host.xfer(tx_simple(Op.STOP))
    await leave_fabric(dut)


async def ch_send(host, byte, last=False):
    """CH_WRITE once the shell's host->design FIFO has room."""
    for _ in range(200):
        if (await host.status()).tx_ready:
            await host.xfer(tx_ch_write(byte, last=last))
            return
    raise AssertionError(f"host channel never ready for {byte:#04x}")


async def ch_recv(host):
    """CH_READ once the design has put a byte in the design->host FIFO."""
    for _ in range(400):
        if (await host.status()).rx_valid:
            return parse_byte(await host.xfer(tx_ch_read()))
    raise AssertionError("no byte from the design")


@cocotb.test(skip=not REAL_FABRIC)
async def test_spi_ctrl(dut):
    """The design-set SPI controller on the hard primitives (spi8, mode 0) through the host
    interface, against the reference SPI target (tools/refmodels/spi.py) on the pins: the
    target receives the bytes the host wrote, and the host reads back the target's replies."""
    from refmodels.spi import Target
    host = await reset(dut)
    host.set_fab_in(1)                                   # MISO idle high
    await load_and_run(host, "spi8")
    tgt = Target(cpol=0, cpha=0, responses=[0xC3, 0x3C, 0x81])
    stop = False

    async def bench():
        while not stop:
            await RisingEdge(dut.clk)
            o = int(dut.uo_out.value)
            sck, mosi, cs_n = (o >> 2) & 1, (o >> 3) & 1, (o >> 4) & 1
            host.set_fab_in(tgt.step(cs_n, sck, mosi))

    b = cocotb.start_soon(bench())
    sent = [0xA5, 0x5A, 0xF0]
    for i, byte in enumerate(sent):
        await ch_send(host, byte, last=(i == len(sent) - 1))
    got = [await ch_recv(host) for _ in sent]
    await ClockCycles(dut.clk, 40)                       # CS released, end gap
    stop = True
    await b
    assert tgt.transactions == [sent], f"target saw {tgt.transactions}"
    assert got == [0xC3, 0x3C, 0x81], f"host read {[hex(g) for g in got]}"
    assert (int(dut.uo_out.value) >> 4) & 1 == 1, "CS_N released after the last byte"
    await host.xfer(tx_simple(Op.STOP))
    await leave_fabric(dut)


@cocotb.test(skip=not REAL_FABRIC)
async def test_i2c_ctrl(dut):
    """The design-set I2C controller on the hard primitives (i2c8) through the host interface,
    on an open-drain bus (wired-AND of the chip's output enables and the reference register-map
    target, tools/refmodels/i2c.py): write a register, read it back through a repeated START,
    and see an unknown address NACKed."""
    from refmodels.i2c import Target, wired_and
    START, WRITE, READ_NACK, STOP = 0x00, 0x40, 0x81, 0xC0
    host = await reset(dut)
    dut.uio_in.value = 0b11                              # both lines pulled up
    await load_and_run(host, "i2c8")
    tgt = Target(0x42)
    stop = False

    async def bench():
        drive = (1, 1)
        while not stop:
            await RisingEdge(dut.clk)
            oe = int(dut.uio_oe.value)
            sda = wired_and(1 - (oe & 1), drive[0])
            scl = wired_and(1 - ((oe >> 1) & 1), drive[1])
            drive = tgt.step(sda, scl)
            dut.uio_in.value = sda | scl << 1

    b = cocotb.start_soon(bench())

    async def cmd(*bytes_):
        for x in bytes_:
            await ch_send(host, x)

    await cmd(START, WRITE, 0x42 << 1)                   # address, write
    assert await ch_recv(host) == 0x00, "address not ACKed"
    await cmd(WRITE, 0x03)                               # register pointer
    assert await ch_recv(host) == 0x00
    await cmd(WRITE, 0x5A)                               # data
    assert await ch_recv(host) == 0x00
    await cmd(STOP)
    await ClockCycles(dut.clk, 200)
    assert tgt.regs.get(3) == 0x5A, f"target registers {tgt.regs}"

    await cmd(START, WRITE, 0x42 << 1)
    assert await ch_recv(host) == 0x00
    await cmd(WRITE, 0x03)
    assert await ch_recv(host) == 0x00
    await cmd(START, WRITE, 0x42 << 1 | 1)               # repeated START, read
    assert await ch_recv(host) == 0x00
    await cmd(READ_NACK)
    assert await ch_recv(host) == 0x5A, "read back"
    await cmd(STOP)

    await cmd(START, WRITE, 0x50 << 1)                   # nobody there
    assert await ch_recv(host) == 0x01, "unknown address must be NACKed"
    await cmd(STOP)
    await ClockCycles(dut.clk, 200)
    status = parse_byte(await host.xfer(tx_user_status()))
    assert status & 0x0C == 0, f"err/overrun set: {status:#04x}"
    assert status & 0x01 == 0, "bus released after STOP"
    stop = True
    await b
    await host.xfer(tx_simple(Op.STOP))
    await leave_fabric(dut)


def _board_modules():
    """tools/board (the code that runs on the demo board's RP2040) and cocotb's bridge/resume."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "board"))
    import warp
    import examples
    try:
        from cocotb import bridge, resume
    except ImportError:                                  # cocotb 2.0.x: not yet public
        from cocotb._bridge import bridge, resume
    return warp, examples, bridge, resume


def _board_pins(dut, resume):
    """The demo board's pin access, as blocking calls the board code makes (cocotb resume).
    `ext` holds ui_in bits driven by a device outside the board (mask, value): they win over
    the board's writes, as a wire from that device would."""
    from types import SimpleNamespace
    ext = [0, 0]

    @resume
    async def write_ui(v):
        dut.ui_in.value = (v & ~ext[0]) | (ext[1] & ext[0])
        await Timer(1, "ns")

    @resume
    async def wait(n):
        await ClockCycles(dut.clk, n)

    @resume
    async def read_uo():
        return bit(dut.uo_out, 0)                       # only HOST_MISO matters to the loader

    return SimpleNamespace(write_ui=write_ui, read_uo=read_uo, wait=wait, ext=ext)


async def _board_load(dut, name, fab_in=0, chunk=16):
    """Checked load of test/bitstreams/<name>.wbit by the board loader itself; returns its Warp."""
    warp, _, bridge, resume = _board_modules()
    pins = _board_pins(dut, resume)
    box = {}

    @bridge
    def load():
        w = warp.Warp(pins)
        w.set_fab_in(fab_in)
        w.load_file(str(BITS / f"{name}.wbit"), chunk=chunk)
        box["w"] = w

    hold_x(dut, True)                                    # D-023, as load_and_run
    await Timer(1, "ns")
    await load()
    hold_x(dut, False)
    await Timer(1, "ns")
    await settle_routing_loops(dut)
    return box["w"], pins


@cocotb.test(skip=not REAL_FABRIC)
async def test_board_loader(dut):
    """The demo-board loader itself (tools/board/warp.py, the code that runs on the board's
    RP2040, D-032) drives the chip's pins: a checked load of uart16, RUN, bytes to the design
    (tools/board/examples.py uart_send) that leave on FAB_OUT0 as UART frames, and a frame into
    FAB_IN0 read back (uart_recv). The board code is plain blocking code; cocotb's bridge/resume
    run it against the chip."""
    await reset(dut)
    _, ex, bridge, _ = _board_modules()
    w, pins = await _board_load(dut, "uart16", fab_in=1)   # UART RX line idle high

    wave = []

    async def record(n):
        for _ in range(n):
            await ClockCycles(dut.clk, 1)
            wave.append(bit(dut.uo_out, 2))

    sent = [0x5A, 0xC3]

    @bridge
    def board_session():
        w.run()
        ex.uart_send(w, sent)
        # a frame into the design's RX pin: start bit, 8 data bits LSB first, stop bit
        for level in [0] + [(0x96 >> i) & 1 for i in range(8)] + [1]:
            w.set_fab_in(level)
            pins.wait(UART_DIV)
        pins.wait(4 * UART_DIV)
        return ex.uart_recv(w, 1), ex.uart_errors(w), w.status()

    rec = cocotb.start_soon(record(60 * UART_DIV + 6000))
    got, errs, st = await board_session()
    await rec

    # 8N1 frames on FAB_OUT0, from the first idle-high level (the pin is parked low until RUN)
    frames, i = [], wave.index(1)
    while i < len(wave) - 10 * UART_DIV:
        if wave[i] == 0:
            mid = i + UART_DIV // 2
            frames.append(sum(wave[mid + (k + 1) * UART_DIV] << k for k in range(8)))
            i = mid + 9 * UART_DIV
        else:
            i += 1
    assert frames[:len(sent)] == sent, f"TX frames {[hex(f) for f in frames]}"
    assert got == [0x96], f"host read {got}"
    assert errs[:2] == (False, False) and st["state"] == "RUNNING"
    await leave_fabric(dut)


@cocotb.test(skip=not REAL_FABRIC)
async def test_board_examples_spi(dut):
    """Board example spi_transfer (tools/board/examples.py) with the SPI controller bitstream
    (spi8) against the reference SPI target (tools/refmodels/spi.py) on the pins."""
    from refmodels.spi import Target
    await reset(dut)
    _, ex, bridge, _ = _board_modules()
    w, pins = await _board_load(dut, "spi8", fab_in=1)    # MISO idle high
    tgt = Target(cpol=0, cpha=0, responses=[0x3C, 0x42, 0x99])
    stop = False
    pins.ext[0] = 0x08                                   # FAB_IN0 = ui_in[3] is the target's MISO

    async def bench():
        while not stop:
            await RisingEdge(dut.clk)
            o = int(dut.uo_out.value)
            pins.ext[1] = tgt.step((o >> 4) & 1, (o >> 2) & 1, (o >> 3) & 1) << 3
            v = int(dut.ui_in.value)
            dut.ui_in.value = (v & ~0x08) | pins.ext[1]

    b = cocotb.start_soon(bench())

    @bridge
    def board_session():
        w.run()
        return ex.spi_transfer(w, [0x9F, 0x00, 0x00])

    got = await board_session()
    await ClockCycles(dut.clk, 40)
    stop = True
    await b
    # CS_N is on a uo_out pin, parked at 0 until RUN: the target sees CS low with no clocks
    # before the design starts (BUGS #19, docs/EXAMPLES.md); no data moves then.
    assert tgt.transactions[:-1] in ([], [[]]), f"target saw {tgt.transactions}"
    assert tgt.transactions[-1] == [0x9F, 0x00, 0x00], f"target saw {tgt.transactions}"
    assert got == [0x3C, 0x42, 0x99], f"board read {got}"
    await leave_fabric(dut)


@cocotb.test(skip=not REAL_FABRIC)
async def test_board_examples_i2c(dut):
    """Board examples i2c_write_regs / i2c_read_regs / i2c_probe (tools/board/examples.py) with
    the I2C controller bitstream (i2c8) on an open-drain bus with the reference register-map
    target (tools/refmodels/i2c.py)."""
    from refmodels.i2c import Target, wired_and
    await reset(dut)
    dut.uio_in.value = 0b11
    _, ex, bridge, _ = _board_modules()
    w, pins = await _board_load(dut, "i2c8")
    tgt = Target(0x48)
    stop = False

    async def bench():
        drive = (1, 1)
        while not stop:
            await RisingEdge(dut.clk)
            oe = int(dut.uio_oe.value)
            sda = wired_and(1 - (oe & 1), drive[0])
            scl = wired_and(1 - ((oe >> 1) & 1), drive[1])
            drive = tgt.step(sda, scl)
            dut.uio_in.value = sda | scl << 1

    b = cocotb.start_soon(bench())

    @bridge
    def board_session():
        w.run()
        ex.i2c_write_regs(w, 0x48, 0x02, [0xDE, 0xAD])
        back = ex.i2c_read_regs(w, 0x48, 0x02, 2)
        return back, ex.i2c_probe(w, 0x48), ex.i2c_probe(w, 0x21)

    back, here, absent = await board_session()
    await ClockCycles(dut.clk, 200)
    stop = True
    await b
    assert tgt.regs.get(2) == 0xDE and tgt.regs.get(3) == 0xAD, f"target registers {tgt.regs}"
    assert back == [0xDE, 0xAD], f"read back {back}"
    assert here and not absent
    await leave_fabric(dut)


@cocotb.test(skip=not REAL_FABRIC)
async def test_ws2812(dut):
    """Held-out H1 (docs/design/HELDOUT.md) on the frozen chip: the WS2812 transmitter bitstream
    (ws2812), loaded through the host interface; 8 LEDs (24 bytes) streamed over the host
    channel leave on FAB_OUT0 within the WS2812B datasheet's timing (independent decoder,
    tools/refmodels/ws2812.py), then the latch gap."""
    from refmodels import ws2812
    import random
    host = await reset(dut)
    await load_and_run(host, "ws2812")
    wave, stop = [], [False]

    async def rec():
        while not stop[0]:
            await ClockCycles(dut.clk, 1)
            wave.append(bit(dut.uo_out, 2))

    r = cocotb.start_soon(rec())
    rng = random.Random(7)
    data = [rng.randrange(256) for _ in range(24)]
    for i, b in enumerate(data):
        await ch_send(host, b, last=(i == len(data) - 1))
    await ClockCycles(dut.clk, 60 * 62)
    stop[0] = True
    await r
    frames, errors = ws2812.decode(wave, 20)
    assert errors == [], errors[:5]
    assert frames == [data], f"decoded {frames}"
    assert parse_byte(await host.xfer(tx_user_status())) & 0x02 == 0, "no underrun"
    await host.xfer(tx_simple(Op.STOP))
    await leave_fabric(dut)


@cocotb.test(skip=not REAL_FABRIC)
async def test_onewire(dut):
    """Held-out H2 on the frozen chip: the 1-Wire controller bitstream (onewire), loaded through
    the host interface, on an open-drain line (FAB_IO0) with the independent reference device
    (tools/refmodels/onewire.py): reset + presence, READ ROM (0x33), the 8-byte ROM read back
    with a valid CRC-8."""
    from refmodels import onewire
    host = await reset(dut)
    dut.uio_in.value = 0b1
    await load_and_run(host, "onewire")
    rom = onewire.rom_code(0x28, 0x0000_C0FF_EE42)
    dev = onewire.Device(rom, 20)
    stop = [False]

    async def bench():
        drive = 1
        while not stop[0]:
            await RisingEdge(dut.clk)
            line = min(1 - (int(dut.uio_oe.value) & 1), drive)
            drive = dev.step(line)
            dut.uio_in.value = min(1 - (int(dut.uio_oe.value) & 1), drive)

    b = cocotb.start_soon(bench())

    async def idle():
        for _ in range(400):
            if not parse_byte(await host.xfer(tx_user_status())) & 1:
                return
            await ClockCycles(dut.clk, 500)
        raise AssertionError("1-Wire controller stays busy")

    await ch_send(host, 0x00)                            # RESET
    await idle()
    assert parse_byte(await host.xfer(tx_user_status())) & 0x08, "presence"
    await ch_send(host, 0x40)                            # WRITE 0x33 (READ ROM)
    await ch_send(host, 0x33)
    await idle()
    got = []
    for _ in range(8):
        await ch_send(host, 0x80)                        # READ
        got.append(await ch_recv(host))
    stop[0] = True
    await b
    assert ("byte", 0x33) in dev.log
    assert got == rom, [hex(x) for x in got]
    assert onewire.crc8(got) == 0
    await host.xfer(tx_simple(Op.STOP))
    await leave_fabric(dut)


@cocotb.test(skip=not REAL_FABRIC)
async def test_swd(dut):
    """Held-out H3 on the frozen chip: the SWD host bit engine (swd) loaded through the host
    interface, driven by the host library tools/board/swd.py over the host channel, against the
    independent reference target (tools/refmodels/swd.py, ADIv5): connect, DPIDR, an AP register
    written and read back (posted read), one WAIT retried."""
    from refmodels import swd as ref
    _, _, bridge, resume = _board_modules()
    import swd as swdhost
    host = await reset(dut)
    await load_and_run(host, "swd")
    tgt = ref.Target(dpidr=0x6BA02477)
    stop = [False]

    async def bench():
        while not stop[0]:
            await RisingEdge(dut.clk)
            swclk = bit(dut.uo_out, 2)
            hdrive = bit(dut.uio_out, 0) if bit(dut.uio_oe, 0) else None
            tdrive = tgt.step(swclk, hdrive)
            line = hdrive if hdrive is not None else (tdrive if tdrive is not None else 1)
            dut.uio_in.value = line

    b = cocotb.start_soon(bench())

    @resume
    async def send(v):
        await ch_send(host, v)

    @resume
    async def recv():
        return await ch_recv(host)

    class Link:
        def send(self, *bytes_):
            for v in bytes_:
                send(v)

        def reply(self):
            return recv()

    s = swdhost.Swd(Link())

    @bridge
    def session():
        s.connect()
        idr = s.dp_read(0x0)
        tgt.wait_next = 1
        s.ap_write(0, 0x04, 0x1234_5678)
        return idr, s.ap_read(0, 0x04)

    idr, back = await session()
    stop[0] = True
    await b
    assert idr == 0x6BA02477, hex(idr)
    assert back == 0x1234_5678, hex(back)
    assert tgt.errors == [], tgt.errors
    await host.xfer(tx_simple(Op.STOP))
    await leave_fabric(dut)


@cocotb.test(skip=not REAL_FABRIC)
async def test_corrupt_load_over_running_design(dut):
    """Phase 4 robustness: a real design runs (counter4, outputs toggling); STOP parks every pin;
    a corrupt load (logic4 with a bad CRC) writes its words into the fabric before LOAD_END
    rejects it, so the fabric holds a half-written configuration: the chip must end in ERROR,
    refuse RUN and keep every fabric pin parked whatever the inputs do; a valid load then runs
    correctly (ARCHITECTURE §3-4)."""
    from host.protocol import tx_load_begin, tx_load_data, tx_load_end, crc32_words
    host = await reset(dut)
    await load_and_run(host, "counter4")
    host.set_fab_in(0b01)
    await ClockCycles(dut.clk, 20)
    assert not parked(dut) or fab_out(dut) != 0, "counter4 should be driving its outputs"
    await host.xfer(tx_simple(Op.STOP))
    await expect(host, State.LOADED)
    assert parked(dut)

    bad = BitFile.load(BITS / "logic4.wbit").words
    hold_x(dut, True)
    await Timer(1, "ns")
    await host.xfer(tx_load_begin(len(bad)))
    for i in range(0, len(bad), 16):
        await host.xfer(tx_load_data(bad[i:i + 16]))
    await host.xfer(tx_load_end(crc32_words(bad) ^ 0x8000_0000))
    await expect(host, State.ERROR, ErrorCode.CRC)
    hold_x(dut, False)
    await Timer(1, "ns")
    await settle_routing_loops(dut)

    for v in (0b00000, 0b11111, 0b10101):
        host.set_fab_in(v)
        dut.uio_in.value = 0xFF if v & 1 else 0x00
        await ClockCycles(dut.clk, 8)
        assert parked(dut), f"pins must stay parked in ERROR (inputs {v:05b})"
    await host.xfer(tx_simple(Op.RUN))
    await expect(host, State.ERROR, ErrorCode.BAD_COMMAND)
    assert parked(dut)

    await load_and_run(host, "logic4")                 # a valid load recovers
    await check_logic4(dut, host)
    await leave_fabric(dut)


@cocotb.test(skip=not REAL_FABRIC)
async def test_uart_input_phase(dut):
    """Phase 4 robustness: external edges at arbitrary phases of the system clock. UART frames
    into FAB_IN0 with every bit edge placed a random 1-19 ns after a clock edge (the shell's
    synchronizers take the pin into the clock domain); every byte must arrive intact."""
    import random
    rng = random.Random(11)
    host = await reset(dut)
    host.set_fab_in(1)
    await load_and_run(host, "uart16")
    sent = [rng.randrange(256) for _ in range(12)]
    got = []
    for b in sent:
        for level in [0] + [(b >> i) & 1 for i in range(8)] + [1]:
            await RisingEdge(dut.clk)
            await Timer(rng.randrange(1, 20), "ns")
            host.set_fab_in(level)
            await ClockCycles(dut.clk, UART_DIV - 1)
        await ClockCycles(dut.clk, 2 * UART_DIV)
        got.append(await ch_recv(host))                # one byte at a time: the design holds 1
    assert got == sent, f"{[hex(x) for x in got]}"
    assert parse_byte(await host.xfer(tx_user_status())) & 0x06 == 0, "no overrun, no framing error"
    await host.xfer(tx_simple(Op.STOP))
    await leave_fabric(dut)


@cocotb.test(skip=not REAL_FABRIC)
async def test_showcase_protocol_switching(dut):
    """Showcase (D-036): one chip, never reset, loads six protocols one after another through the
    host interface, and each works against its independent reference device on the pins:
    UART, SPI controller, I2C controller (design set) and WS2812, 1-Wire, SWD (held out: the
    architecture was frozen before they were written)."""
    from refmodels import ws2812, onewire, i2c as i2cref, spi as spiref, swd as swdref
    _, _, bridge, resume = _board_modules()
    import swd as swdhost
    host = await reset(dut)
    done = []

    async def run_bench(step):
        """Run `step(bus_state)` every clock until stopped; returns the stop flag list."""
        flag = [False]

        async def loop():
            while not flag[0]:
                await RisingEdge(dut.clk)
                step()
        return flag, cocotb.start_soon(loop())

    async def stop_bench(fb):
        fb[0][0] = True
        await fb[1]

    # ---- 1: UART
    host.set_fab_in(1)
    await load_and_run(host, "uart16")
    wave = []
    fb = await run_bench(lambda: wave.append(bit(dut.uo_out, 2)))
    await ch_send(host, 0xA5)
    await ClockCycles(dut.clk, 14 * UART_DIV + 400)
    await stop_bench(fb)
    i = wave.index(1)
    while wave[i] == 1:
        i += 1
    mid = i + UART_DIV // 2
    assert sum(wave[mid + (k + 1) * UART_DIV] << k for k in range(8)) == 0xA5
    await host.xfer(tx_simple(Op.STOP))
    done.append("uart")

    # ---- 2: SPI controller
    tgt = spiref.Target(cpol=0, cpha=0, responses=[0x5C])

    def spi_step():
        o = int(dut.uo_out.value)
        host.set_fab_in(tgt.step((o >> 4) & 1, (o >> 2) & 1, (o >> 3) & 1))
    await load_and_run(host, "spi8")
    fb = await run_bench(spi_step)
    await ch_send(host, 0x3E, last=True)
    got = await ch_recv(host)
    await ClockCycles(dut.clk, 40)
    await stop_bench(fb)
    assert tgt.transactions[-1] == [0x3E] and got == 0x5C
    await host.xfer(tx_simple(Op.STOP))
    done.append("spi")

    # ---- 3: I2C controller
    dut.uio_in.value = 0b11
    it = i2cref.Target(0x42)
    drive = [(1, 1)]

    def i2c_step():
        oe = int(dut.uio_oe.value)
        sda = i2cref.wired_and(1 - (oe & 1), drive[0][0])
        scl = i2cref.wired_and(1 - ((oe >> 1) & 1), drive[0][1])
        drive[0] = it.step(sda, scl)
        dut.uio_in.value = sda | scl << 1
    await load_and_run(host, "i2c8")
    fb = await run_bench(i2c_step)
    for b in (0x00, 0x40, 0x84):
        await ch_send(host, b)
    assert await ch_recv(host) == 0x00
    for b in (0x40, 0x01):
        await ch_send(host, b)
    assert await ch_recv(host) == 0x00
    for b in (0x40, 0x77):
        await ch_send(host, b)
    assert await ch_recv(host) == 0x00
    await ch_send(host, 0xC0)
    await ClockCycles(dut.clk, 300)
    await stop_bench(fb)
    assert it.regs.get(1) == 0x77
    await host.xfer(tx_simple(Op.STOP))
    done.append("i2c")

    # ---- 4: WS2812 (held out)
    host.set_fab_in(0)
    await load_and_run(host, "ws2812")
    wave = []
    fb = await run_bench(lambda: wave.append(bit(dut.uo_out, 2)))
    data = [0x12, 0x34, 0x56]
    for k, b in enumerate(data):
        await ch_send(host, b, last=(k == len(data) - 1))
    await ClockCycles(dut.clk, 60 * 62)
    await stop_bench(fb)
    frames, errors = ws2812.decode(wave, 20)
    assert errors == [] and frames == [data], (frames, errors[:3])
    await host.xfer(tx_simple(Op.STOP))
    done.append("ws2812")

    # ---- 5: 1-Wire (held out)
    dut.uio_in.value = 0b1
    rom = onewire.rom_code(0x28, 0x0000_0000_BEEF)
    dev = onewire.Device(rom, 20)
    dq = [1]

    def ow_step():
        line = min(1 - (int(dut.uio_oe.value) & 1), dq[0])
        dq[0] = dev.step(line)
        dut.uio_in.value = min(1 - (int(dut.uio_oe.value) & 1), dq[0])
    await load_and_run(host, "onewire")
    fb = await run_bench(ow_step)

    async def ow_idle():
        for _ in range(400):
            if not parse_byte(await host.xfer(tx_user_status())) & 1:
                return
            await ClockCycles(dut.clk, 500)
        raise AssertionError("busy")
    await ch_send(host, 0x00)
    await ow_idle()
    assert parse_byte(await host.xfer(tx_user_status())) & 0x08, "presence"
    await ch_send(host, 0x40)
    await ch_send(host, 0x33)
    await ow_idle()
    first = []
    for _ in range(2):
        await ch_send(host, 0x80)
        first.append(await ch_recv(host))
    await stop_bench(fb)
    assert first == rom[:2], first
    await host.xfer(tx_simple(Op.STOP))
    done.append("onewire")

    # ---- 6: SWD (held out)
    st = swdref.Target(dpidr=0x4BA00477)

    def swd_step():
        hd = bit(dut.uio_out, 0) if bit(dut.uio_oe, 0) else None
        td = st.step(bit(dut.uo_out, 2), hd)
        dut.uio_in.value = hd if hd is not None else (td if td is not None else 1)
    await load_and_run(host, "swd")
    fb = await run_bench(swd_step)

    @resume
    async def send(v):
        await ch_send(host, v)

    @resume
    async def recv():
        return await ch_recv(host)

    class Link:
        def send(self, *bs):
            for v in bs:
                send(v)

        def reply(self):
            return recv()
    s = swdhost.Swd(Link())

    @bridge
    def swd_session():
        s.connect()
        return s.dp_read(0x0)
    idr = await swd_session()
    await stop_bench(fb)
    assert idr == 0x4BA00477
    await host.xfer(tx_simple(Op.STOP))
    done.append("swd")

    assert done == ["uart", "spi", "i2c", "ws2812", "onewire", "swd"]
    await leave_fabric(dut)
