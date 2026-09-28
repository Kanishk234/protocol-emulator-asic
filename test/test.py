# SPDX-FileCopyrightText: © 2026 Kanishk, Krithik
# SPDX-License-Identifier: Apache-2.0

# R4 run 6 (branch spike/r4-floorplan): pin-level smoke tests of the real chip (trw_chip at the protocol floor,
# 2 lanes / 4 units) through the host SPI link, so they also run in gl_test on the hardened netlist. Taken from
# main's test_internal/chip/test_chip.py (same frames, tools/host), with the template testbench's pins: the
# identity, time and SRAM through the rotation; a lane forwarding HOST_IN to HOST_OUT; a UART frame from a full
# unit (U0) and a lean one (U3); a routine running from SRAM on the rotation.

import pathlib
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import tripwire_spec as S  # noqa: E402
from host import HM, frame_read, frame_write, port_word, slot_words  # noqa: E402

H = 4                                         # SCK half period (clk/8, the §9 limit)
CSN, SCK, MOSI, MISO = 4, 5, 6, 3
OP, DST, ASRC, BSEL = S.OPS, S.DST, S.ASRC, S.BSEL
DATA, CTRL, EVENT, ERR = (S.TAGS[t] for t in ("DATA", "CTRL", "EVENT", "ERR"))


class Pins:
    """A cocotb SPI controller on the chip's host pins; speaks tools/host frames."""

    def __init__(self, dut):
        self.d = dut
        self.ui = 1 << CSN

    def _set(self, bit, v):
        self.ui = (self.ui | 1 << bit) if v else (self.ui & ~(1 << bit))
        self.d.ui_in.value = self.ui

    async def xfer(self, data):
        d = self.d
        self._set(CSN, 0)
        await ClockCycles(d.clk, H, rising=False)
        reply = []
        for byte in data:
            r = 0
            for i in range(7, -1, -1):
                self._set(MOSI, byte >> i & 1)
                await ClockCycles(d.clk, H, rising=False)
                v = d.uo_out.value
                assert v.is_resolvable, f"uo_out has X/Z: {v}"
                r = r << 1 | (int(v) >> MISO & 1)
                self._set(SCK, 1)
                await ClockCycles(d.clk, H, rising=False)
                self._set(SCK, 0)
            reply.append(r)
        await ClockCycles(d.clk, H, rising=False)
        self._set(CSN, 1)
        await ClockCycles(d.clk, 2 * H, rising=False)
        return bytes(reply)

    async def write(self, addr, words):
        await self.xfer(frame_write(addr, list(words)))

    async def read(self, addr, n=1):
        out, parse = frame_read(addr, n)
        return parse(await self.xfer(out))


def slot(**f):
    f.setdefault("V", 1)
    w = 0
    for name, v in f.items():
        lsb, width = S.SLOT_FIELDS[name]
        w |= v << lsb
    return w


def pin_block(**f):
    vals = dict(pin_a=31, pin_b=31, pin_c=31, pin_s=31, pin_n=31, period=256)
    vals.update(f)
    b = 0
    for name, v in vals.items():
        bit, width, _ = S.PIN_CFG_FIELDS[name]
        b |= v << bit
    return [(b >> (16 * w)) & 0xFFFF for w in range(22)]


def lane_addr(k, word):
    return HM["lanes"] + S.HOST_LANE_STRIDE * k + S.HOST_LANE_WORDS.index(word)


async def boot(dut, lane0=None, units=None):
    """Reset, then §14 H1 by hand: lane 0's 12 slots + K, every pin unit block."""
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    p = Pins(dut)
    dut.ena.value, dut.uio_in.value, dut.ui_in.value = 1, 0, p.ui
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    lane0 = lane0 or {}
    for s in range(12):
        await p.write(HM["slots"] | s << 4, slot_words(lane0.get(s, 0)))
    await p.write(HM["slots"] | 12 << 4, [0, 0, 0, 0])
    units = units or {}
    for u in range(len(S.PIN_UNIT_FEATURES)):
        await p.write(HM["pin_cfg"] + 32 * u, units.get(u, pin_block()))
    return p


@cocotb.test()
async def test_identity_time_sram(dut):
    p = await boot(dut)
    major, minor = (int(x) for x in S.VERSION.split("."))
    assert await p.read(HM["version"], 2) == [major << 8 | minor, S.HOST_ID]
    t0, t1 = (await p.read(HM["time"]))[0], (await p.read(HM["time"]))[0]
    assert t0 != t1
    await p.write(HM["sram"], [0x1234, 0xBEEF, 0x0F0F])
    await p.write(HM["sram"] + 511, [0xA5A5])
    assert await p.read(HM["sram"], 3) == [0x1234, 0xBEEF, 0x0F0F]
    assert await p.read(HM["sram"] + 511) == [0xA5A5]
    assert await p.read(lane_addr(0, "r0"), 6) == [0] * 6
    await p.write(lane_addr(1, "r2"), [0x4242])            # E2: halted lane, host write
    assert await p.read(lane_addr(1, "r2")) == [0x4242]


@cocotb.test()
async def test_lane_forwards_host_in_to_host_out(dut):
    """HOST_IN -> L0.I0 -> slot 0 (MOV, dequeue, keep tag) -> L0.O0 -> HOST_OUT."""
    fwd = slot(OP=OP["MOV"], DST=DST["O0"], ASRC=ASRC["I0"], DQ=1, KT=1, BSEL=BSEL["imm"])
    p = await boot(dut, lane0={0: fwd})
    cons = S.FABRIC_CONSUMERS
    await p.write(HM["ports"] + cons.index("L0.I0"), [port_word("L0.I0", "HOST_IN")])
    await p.write(HM["ports"] + cons.index("HOST_OUT"), [port_word("HOST_OUT", "L0.O0")])
    await p.write(HM["run"], [0b001])
    for tag, data in ((DATA, 0x1234), (EVENT, 0x8001), (ERR, 0x00FF)):
        await p.write(HM["host_in"] + tag, [data])
        st, d = await p.read(HM["host_status"], 2)          # status, then data (takes it)
        assert st >> 15 == 1 and st & 3 == tag and d == data, (hex(st), hex(d))
    assert (await p.read(HM["host_status"]))[0] >> 15 == 0


@cocotb.test()
async def test_pin_units_uart_tx_full_and_lean(dut):
    """HOST_IN -> Uu.tx; SHIFT at 20 clocks/bit on uo0 (owner Uu): a UART 8N1 frame, on the full unit (U0)
    and a lean one (U3)."""
    for u in (0, 3):
        blk = pin_block(txmode=1, idle=1, pin_a=8, period=20 * 256, nbits=9)
        p = await boot(dut, units={u: blk})
        await p.write(HM["owners"] + 0, [u])                 # pad 8 (uo0)
        cons = S.FABRIC_CONSUMERS
        await p.write(HM["ports"] + cons.index(f"U{u}.tx"), [port_word(f"U{u}.tx", "HOST_IN")])
        await p.write(HM["run"], [0b001])                    # live
        frame = 0x200 | 0xA6 << 1
        bits = []

        async def sample():
            while int(dut.uo_out.value) & 1:
                await ClockCycles(dut.clk, 1)
            await ClockCycles(dut.clk, 10)
            for _ in range(10):
                bits.append(int(dut.uo_out.value) & 1)
                await ClockCycles(dut.clk, 20)
        task = cocotb.start_soon(sample())
        await p.write(HM["host_in"], [frame])
        await ClockCycles(dut.clk, 400)
        await task
        assert sum(b << i for i, b in enumerate(bits)) == frame, (u, bits)


@cocotb.test()
async def test_routine_on_the_rotation(dut):
    """Slot 0 CALLs routine 3 once; the lane's routine controller reads the entry table and runs
    LDI, ST, LD, SETST, RET from SRAM on lane 0's slot."""
    call = slot(SE=1, SV=0, OP=OP["CALL"], IMM=3, NSE=1, NS=1, DST=DST["none"])
    p = await boot(dut, lane0={0: call})

    def ctrl(name, **v):
        code, fields = S.ROUTINE_CTRL[name]
        w = 1 << 15 | code << 12
        for k, x in v.items():
            msb, lsb = fields[k]
            w |= (x & ((1 << (msb - lsb + 1)) - 1)) << lsb
        return w
    await p.write(HM["sram"] + 3, [0x40])
    await p.write(HM["sram"] + 0x40, [ctrl("LDI", rd=1, imm=0x2A5), ctrl("LDI", rd=0, imm=0x100),
                                      ctrl("ST", rd=1, ra=0, off=3), ctrl("LD", rd=2, ra=0, off=3),
                                      ctrl("SYS", fn=S.SYS["SETST"], arg=9), ctrl("SYS", fn=S.SYS["RET"], arg=0)])
    await p.write(HM["run"], [0b001])
    await ClockCycles(dut.clk, 120)
    await p.write(HM["run"], [0])
    lane = dict(zip(S.HOST_LANE_WORDS, await p.read(lane_addr(0, "r0"), len(S.HOST_LANE_WORDS))))
    assert lane["state"] == 9 and not lane["flags"] >> 3 & 1, lane
    assert lane["r1"] == 0x2A5 and lane["r2"] == 0x2A5
    assert await p.read(HM["sram"] + 0x103) == [0x2A5]
