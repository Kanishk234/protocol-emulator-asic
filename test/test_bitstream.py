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
from pathlib import Path

import cocotb
from cocotb.triggers import ClockCycles, Timer

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
