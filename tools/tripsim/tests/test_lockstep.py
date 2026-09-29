"""Model-side L2 snapshot/comparator coverage; no RTL dependency."""

import tripwire_spec as S
from tripsim import Chip
from tripsim.lockstep import first_difference, snapshot


def test_snapshot_captures_generated_debug_and_channel_state():
    chip = Chip()
    lane_base = S.HOST_MAP["lanes"][0]
    assert chip.host_write(lane_base, 0xA55A)
    producer = chip.fabric.producers["U0.rx"]
    producer.valid, producer.seq, producer.tag, producer.data = 1, 1, 2, 0xC35A
    chip.pins[0].flags.update(OVERRUN=1, LATE=1)
    chip.own(S.PAD_GROUPS["uo"][0], 0)

    state = snapshot(chip)

    assert state["cycle"] == chip.cycle
    assert state["lanes"][0]["debug"][0] == 0xA55A
    assert len(state["lanes"]) == len(chip.lanes)
    assert len(state["unit_flags"]) == len(chip.pins)
    producer_states = dict(state["producers"])
    assert producer_states["U0.rx"] == (1, 1, 2, 0xC35A)
    assert len(state["ports"]) == len(chip.fabric.ports)
    assert state["unit_flags"][0] == 3
    assert state["pads"] == chip.outputs()


def test_first_difference_identifies_the_first_field_mismatch():
    expected = {
        "cycle": 12,
        "producers": (("U0.rx", (1, 0, 2, 0x1234)),),
    }
    observed = {
        "cycle": 12,
        "producers": (("U0.rx", (1, 1, 2, 0x1234)),),
    }
    assert first_difference(expected, observed) == ("producers[0][1][1]", 0, 1)
    assert first_difference(expected, expected) is None
