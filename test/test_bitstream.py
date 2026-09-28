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
from host.protocol import (Op, State, checked_load_transactions, parse_byte, parse_read_id,
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


@cocotb.test(skip=not REAL_FABRIC)
async def test_board_loader(dut):
    """The demo-board loader itself (tools/board/warp.py, the code that runs on the board's
    RP2040, D-032) drives the chip's pins: a checked load of uart16, RUN, bytes to the design
    that leave on FAB_OUT0 as UART frames, and a frame into FAB_IN0 read back over the host
    channel. The loader is plain blocking code; cocotb's bridge/resume run it against the chip."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "board"))
    import warp
    from types import SimpleNamespace
    try:
        from cocotb import bridge, resume
    except ImportError:                                  # cocotb 2.0.x: not yet public
        from cocotb._bridge import bridge, resume

    await reset(dut)

    @resume
    async def write_ui(v):
        dut.ui_in.value = v
        await Timer(1, "ns")

    @resume
    async def wait(n):
        await ClockCycles(dut.clk, n)

    @resume
    async def read_uo():
        return bit(dut.uo_out, 0)                       # only HOST_MISO matters to the loader

    pins = SimpleNamespace(write_ui=write_ui, read_uo=read_uo, wait=wait)
    board = {}

    @bridge
    def board_load():
        w = warp.Warp(pins)
        w.set_fab_in(1)                                  # UART RX line idle high
        w.load_file(str(BITS / "uart16.wbit"), chunk=16)
        board["w"] = w

    hold_x(dut, True)                                    # D-023, as load_and_run
    await Timer(1, "ns")
    await board_load()
    hold_x(dut, False)
    await Timer(1, "ns")
    await settle_routing_loops(dut)

    wave = []

    async def record(n):
        for _ in range(n):
            await ClockCycles(dut.clk, 1)
            wave.append(bit(dut.uo_out, 2))

    sent = [0x5A, 0xC3]

    @bridge
    def board_session():
        w = board["w"]
        w.run()
        for b in sent:
            w.ch_write(b)
        # a frame into the design's RX pin: start bit, 8 data bits LSB first, stop bit
        for level in [0] + [(0x96 >> i) & 1 for i in range(8)] + [1]:
            w.set_fab_in(level)
            pins.wait(UART_DIV)
        pins.wait(4 * UART_DIV)
        got = w.ch_read()
        return got, w.user_status(), w.status()

    rec = cocotb.start_soon(record(60 * UART_DIV + 6000))
    got, ustat, st = await board_session()
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
    assert got == 0x96, f"host read {got}"
    assert ustat & 0x06 == 0 and st["state"] == "RUNNING"
    await leave_fabric(dut)
