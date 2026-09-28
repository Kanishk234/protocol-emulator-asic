"""The CAN 2.0A reference node: frames between model nodes, arbitration, ACK, CRC."""

import pytest

from refmodels import can


def run(nodes, clocks):
    drives = [1] * len(nodes)
    bus = 1
    for _ in range(clocks):
        drives = [n.step(bus) for n in nodes]
        bus = min(drives)
    return bus


def test_crc15_known():
    # a frame's bits followed by its own CRC give a zero remainder
    bits = can.frame_bits(0x123, [1, 2, 3])
    assert can.crc15(bits) == 0


def test_stuffing():
    assert can.stuff([0] * 5) == [0] * 5 + [1]
    assert can.stuff([1, 1, 1, 1, 1, 1]) == [1] * 5 + [0, 1]


@pytest.mark.parametrize("data", [[], [0x55], [0, 0, 0, 0, 0, 0, 0, 0], [0xFF] * 8, [1, 2, 3, 4, 5]])
def test_frame_between_two_nodes(data):
    a, b = can.Node(20), can.Node(20)
    a.send(0x0F0, data)
    run([a, b], 20 * 200)
    assert a.sent == [(0x0F0, data)] and a.errors == []
    assert b.received == [(0x0F0, data)] and b.errors == []


def test_arbitration_lower_id_wins():
    a, b, c = can.Node(20), can.Node(20), can.Node(20)
    a.send(0x100, [0xAA])
    b.send(0x0FF, [0xBB])                             # lower identifier = more dominant: wins
    run([a, b, c], 20 * 400)
    assert b.sent[0] == (0x0FF, [0xBB])
    assert a.lost == 1 and a.sent == [(0x100, [0xAA])]   # retried after losing
    assert c.received == [(0x0FF, [0xBB]), (0x100, [0xAA])]


def test_no_ack_without_receivers():
    a = can.Node(20)
    a.send(0x001, [0x01])
    run([a], 20 * 120)
    assert "no ACK" in a.errors
