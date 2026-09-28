"""RTL tests for protocols/can (CAN 2.0A controller) on a bus with independent reference nodes
(tools/refmodels/can.py, written from the Bosch CAN 2.0 specification)."""

import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, ReadOnly, NextTimeStep

from refmodels import can

CLK_NS = 20
BIT = int(os.environ.get("BIT", "20"))


def pack(ident, data):
    """Host bytes for a frame: the bits after SOF through the data, MSB first, zero padded."""
    bits = can.frame_bits(ident, data)[1:19 + 8 * len(data)]
    bits += [0] * (-len(bits) % 8)
    return [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]


def unpack(pushes):
    """(ident, data) from the bytes the design pushed: full bytes, then a last one with 2 bits."""
    bits = []
    for b in pushes[:-1]:
        bits += [(b >> (7 - i)) & 1 for i in range(8)]
    bits += [(pushes[-1] >> 1) & 1, pushes[-1] & 1]
    ident = int("".join(map(str, bits[0:11])), 2)
    dlc = int("".join(map(str, bits[14:18])), 2)
    data = [int("".join(map(str, bits[18 + 8 * i:26 + 8 * i])), 2) for i in range(dlc)]
    return ident, data


class Bus:
    def __init__(self, dut, nodes):
        self.dut, self.nodes = dut, nodes
        self.drives = [1] * len(nodes)
        self.pushes = []

    async def run(self):
        dut = self.dut
        while True:
            await RisingEdge(dut.clk)
            await ReadOnly()
            oe = int(dut.tx_oe.value)
            if int(dut.h_rvalid.value) and int(dut.h_rready.value):
                self.pushes.append(int(dut.h_rdata.value))
            bus = min([1 - oe] + self.drives)
            self.drives = [n.step(bus) for n in self.nodes]
            await NextTimeStep()
            dut.rx_i.value = min([1 - oe] + self.drives)


async def setup(dut, nodes):
    cocotb.start_soon(Clock(dut.clk, CLK_NS, unit="ns").start())
    dut.rst_n.value = 0
    dut.rx_i.value = 1
    dut.h_wdata.value = 0
    dut.h_wlast.value = 0
    dut.h_wvalid.value = 0
    dut.h_rready.value = 1                      # the host takes every byte at once
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    bus = Bus(dut, nodes)
    cocotb.start_soon(bus.run())
    await ClockCycles(dut.clk, 12 * BIT)        # bus integration
    return bus


async def host_send(dut, frame_bytes):
    for i, b in enumerate(frame_bytes):
        dut.h_wdata.value = b
        dut.h_wlast.value = int(i == len(frame_bytes) - 1)
        dut.h_wvalid.value = 1
        while True:
            await RisingEdge(dut.clk)
            if int(dut.h_wready.value):
                break
    dut.h_wvalid.value = 0
    dut.h_wlast.value = 0


def status(dut):
    s = int(dut.h_status.value)
    return {"crc_ok": s >> 7 & 1, "acked": s >> 6 & 1, "arb_lost": s >> 5 & 1, "err": s >> 4 & 1,
            "overrun": s >> 3 & 1, "underrun": s >> 2 & 1}


@cocotb.test()
async def test_transmit(dut):
    """The design sends a frame; a reference node receives it and acknowledges."""
    node = can.Node(BIT)
    bus = await setup(dut, [node])
    await host_send(dut, pack(0x3A5, [0xDE, 0xAD, 0xBE, 0xEF]))
    await ClockCycles(dut.clk, 140 * BIT)
    assert node.received == [(0x3A5, [0xDE, 0xAD, 0xBE, 0xEF])], (node.received, node.errors)
    assert node.errors == []
    st = status(dut)
    assert st["acked"] and st["crc_ok"] and not st["err"], st
    assert unpack(bus.pushes) == (0x3A5, [0xDE, 0xAD, 0xBE, 0xEF])      # our own frame echoed


@cocotb.test()
async def test_receive(dut):
    """A reference node sends; the design receives the frame and acknowledges it."""
    node = can.Node(BIT)
    bus = await setup(dut, [node])
    node.send(0x07F, [0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0x55, 0xAA])   # stuffing-heavy
    await ClockCycles(dut.clk, 160 * BIT)
    assert node.sent == [(0x07F, [0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0x55, 0xAA])], node.errors
    assert "no ACK" not in node.errors
    assert unpack(bus.pushes) == (0x07F, [0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0x55, 0xAA])
    assert status(dut)["crc_ok"]


@cocotb.test()
async def test_arbitration(dut):
    """The design and a reference node start together; the lower identifier (the node's) wins,
    the design receives it, and the design's frame goes out on the host's retry."""
    node, other = can.Node(BIT), can.Node(BIT)
    bus = await setup(dut, [node, other])
    node.send(0x100, [0x11])
    mine = pack(0x200, [0x22])
    await host_send(dut, mine)                   # starts at the same idle point as the node
    await ClockCycles(dut.clk, 80 * BIT)
    assert status(dut)["arb_lost"], status(dut)
    assert other.received[:1] == [(0x100, [0x11])]
    bus.pushes.clear()
    await host_send(dut, mine)                   # retry
    await ClockCycles(dut.clk, 80 * BIT)
    assert (0x200, [0x22]) in other.received, other.received
    assert status(dut)["acked"]
