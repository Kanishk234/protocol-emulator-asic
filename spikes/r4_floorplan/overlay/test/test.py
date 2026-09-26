# SPDX-FileCopyrightText: © 2026 Kanishk, Krithik
# SPDX-License-Identifier: Apache-2.0

# R4 floorplan spike (branch spike/r4-floorplan): pin-level smoke tests through the host SPI stub, so they
# also run in gl_test on the hardened netlist. They check that every block is alive and connected:
# SRAM through the rotation, a lane forwarding HOST_IN to HOST_OUT, a pin unit sending a UART frame, a
# pin unit event reaching the host, and a routine fetched by the sequencer stub.
# Pins and address map: src/tt_um_tripwire.v on this branch.

import pathlib
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

HALF = 8                         # SCK half period in clocks (the stub needs >= 4)
CSN, SCK, MOSI = 4, 5, 6
MISO = 3

# Encodings from the spec (tools/tripwire_spec.py, generated from spec/tripwire.yaml).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import tripwire_spec as S  # noqa: E402
SLOT_FIELDS, OPS, DST, ASRC, BSEL = S.SLOT_FIELDS, S.OPS, S.DST, S.ASRC, S.BSEL
PIN_FIELDS = S.PIN_CFG_FIELDS


class Host:
    def __init__(self, dut):
        self.dut = dut
        self.ui = 1 << CSN

    def _set(self, bit, v):
        self.ui = (self.ui | 1 << bit) if v else (self.ui & ~(1 << bit))
        self.dut.ui_in.value = self.ui

    async def _xfer_bit(self, b):
        self._set(MOSI, b)
        await ClockCycles(self.dut.clk, HALF)
        v = self.dut.uo_out.value
        assert v.is_resolvable, f"uo_out has X/Z: {v}"
        got = int(v) >> MISO & 1
        self._set(SCK, 1)
        await ClockCycles(self.dut.clk, HALF)
        self._set(SCK, 0)
        return got

    async def _byte(self, x):
        for i in range(7, -1, -1):
            await self._xfer_bit(x >> i & 1)

    async def write(self, addr, words):
        self._set(CSN, 0)
        await ClockCycles(self.dut.clk, HALF)
        await self._byte(0x80)
        await self._byte(addr >> 8)
        await self._byte(addr & 0xFF)
        for w in words:
            for i in range(15, -1, -1):
                await self._xfer_bit(w >> i & 1)
        await ClockCycles(self.dut.clk, HALF)
        self._set(CSN, 1)
        await ClockCycles(self.dut.clk, 4 * HALF)

    async def read(self, addr, n=1):
        self._set(CSN, 0)
        await ClockCycles(self.dut.clk, HALF)
        await self._byte(0x00)
        await self._byte(addr >> 8)
        await self._byte(addr & 0xFF)
        await self._byte(0x00)                       # dummy
        out = []
        for _ in range(n):
            w = 0
            for _ in range(16):
                w = w << 1 | await self._xfer_bit(0)
            out.append(w)
        await ClockCycles(self.dut.clk, HALF)
        self._set(CSN, 1)
        await ClockCycles(self.dut.clk, 4 * HALF)
        return out


def slot(**f):
    v = 0
    for name, val in f.items():
        lsb, width = SLOT_FIELDS[name]
        assert 0 <= val < 1 << width, name
        v |= val << lsb
    return [(v >> (16 * i)) & 0xFFFF for i in range(4)]


def pin_block(**f):
    vals = dict(pin_a=31, pin_b=31, pin_c=31, pin_s=31, pin_n=31, period=256)
    vals.update(f)
    b = 0
    for name, v in vals.items():
        bit, width, _ = PIN_FIELDS[name]
        b |= v << bit
    return [(b >> (16 * w)) & 0xFFFF for w in range(22)]


async def boot(dut, lane0=None, units=None):
    """Reset; write lane 0's 12 slots + K and every pin unit block (§14 H1)."""
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    dut.ena.value = 1
    dut.ui_in.value = 1 << CSN
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    h = Host(dut)
    lane0 = lane0 or {}
    for s in range(13):
        await h.write(0x1000 | s << 4, lane0.get(s, [0, 0, 0, 0]))
    units = units or {}
    for u in range(6):
        await h.write(0x3000 + 32 * u, units.get(u, pin_block()))
    return h


def port(c, sel, en=1, tap=0, accept=0xF):
    return (0x2000 + c, [accept << 6 | sel << 2 | tap << 1 | en])


@cocotb.test()
async def test_sram_and_registers(dut):
    """SRAM words through the host rotation slot; lane registers read back 0 after reset; time runs."""
    h = await boot(dut)
    await h.write(0x8000, [0x1234, 0xBEEF, 0x0F0F])
    await h.write(0x81FF, [0xA5A5])
    assert await h.read(0x8000, 3) == [0x1234, 0xBEEF, 0x0F0F]
    assert await h.read(0x81FF) == [0xA5A5]
    assert await h.read(0x5000, 6) == [0] * 6
    t1, t2 = await h.read(0x0001), await h.read(0x0001)
    assert t1 != t2


@cocotb.test()
async def test_lane_forwards_host_in_to_host_out(dut):
    """HOST_IN -> L0.I0 -> slot 0 (MOV, dequeue, keep tag) -> L0.O0 -> HOST_OUT."""
    fwd = slot(V=1, OP=OPS["MOV"], DST=DST["O0"], ASRC=ASRC["I0"], DQ=1, KT=1, BSEL=BSEL["imm"])
    h = await boot(dut, lane0={0: fwd})
    for c, sel in ((0, 6), (12, 0)):            # L0.I0 <- HOST_IN; HOST_OUT <- L0.O0
        await h.write(*port(c, sel))
    await h.write(0x0000, [0b001])              # RUN lane 0
    for tag, data in ((0, 0x1234), (2, 0x8001), (0, 0x00FF)):
        await h.write(0x6000 + tag, [data])
        st, d = await h.read(0x6004, 2)         # status, then data (pops)
        assert st == 0x8000 | tag and d == data, (hex(st), hex(d))
    assert (await h.read(0x6004))[0] >> 15 == 0


@cocotb.test()
async def test_pin_unit_uart_tx(dut):
    """HOST_IN -> U2.tx; U2 SHIFT at 20 clocks/bit on uo0 (owner U2): a UART 8N1 frame on the pad."""
    blk = pin_block(txmode=1, idle=1, pin_a=8, period=20 * 256, nbits=9)
    h = await boot(dut, units={2: blk})
    await h.write(0x30C0, [2])                  # pad 8 (uo0) owned by U2
    await h.write(*port(8, 6))                  # U2.tx <- HOST_IN
    await h.write(0x0000, [0b001])              # live
    byte = 0xA6
    frame = 0x200 | byte << 1
    bits = []

    async def sample():
        while (int(dut.uo_out.value) & 1) == 1:
            await ClockCycles(dut.clk, 1)
        await ClockCycles(dut.clk, 10)          # middle of the start bit
        for _ in range(10):
            bits.append(int(dut.uo_out.value) & 1)
            await ClockCycles(dut.clk, 20)

    task = cocotb.start_soon(sample())
    await h.write(0x6000, [frame])
    await ClockCycles(dut.clk, 400)
    await task
    assert sum(b << i for i, b in enumerate(bits)) == frame


@cocotb.test()
async def test_pin_unit_event_to_host(dut):
    """U1 event generator on ui0 (both edges) -> HOST_OUT (sel 7 = U1.rx): EVENT with the new level."""
    blk = pin_block(pin_a=0, ev_edge=3)
    h = await boot(dut, units={1: blk})
    await h.write(*port(12, 7))
    await h.write(0x0000, [0b001])
    h._set(0, 1)                                # ui0 rises (and stays high through the SPI reads)
    await ClockCycles(dut.clk, 20)
    st, d = await h.read(0x6004, 2)
    assert st == 0x8002 and d >> 15 == 1, (hex(st), hex(d))
    assert (await h.read(0x0002))[0] == 0      # no OVERRUN / LATE


@cocotb.test()
async def test_routine_through_the_rotation(dut):
    """Slot 0 CALLs routine 0 once (STATE 0 -> 1); the sequencer stub reads the entry table and fetches
    SETST 2, RET from SRAM on lane 0's rotation slot; STATE ends at 2 with RB = 0."""
    call = slot(V=1, SE=1, SV=0, OP=OPS["CALL"], IMM=0, NSE=1, NS=1, DST=DST["none"], BSEL=BSEL["imm"])
    h = await boot(dut, lane0={0: call})
    sys_w = lambda fn, arg: 0x8000 | 7 << 12 | fn << 8 | arg
    await h.write(0x8000, [0x0020])             # entry table: routine 0 at word 0x20
    await h.write(0x8020, [sys_w(2, 2), sys_w(1, 0)])   # SETST 2; RET
    await h.write(0x0000, [0b001])
    await ClockCycles(dut.clk, 100)
    state, flags = await h.read(0x5004, 2)
    assert state == 2 and (flags >> 3) & 1 == 0, (state, hex(flags))
