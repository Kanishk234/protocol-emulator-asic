"""Model-side state snapshots for the Phase 2 L2 scoreboard.

This module has no RTL or simulator dependency. A testbench can map its observed
debug taps into the same tree and use :func:`first_difference` for a stable,
field-level mismatch report.
"""

from collections.abc import Mapping

import tripwire_spec as _S


def snapshot(chip):
    """Return the architectural comparison state after a model clock.

    Lane words come through the generated D-046 debug map. Producer registers
    are included directly because L2 compares valid/seq/tag/data every clock.
    Names and address ranges are generated from ``spec/tripwire.yaml``.
    """
    lane_base = _S.HOST_MAP["lanes"][0]
    ports_base = _S.HOST_MAP["ports"][0]
    dropped_base = _S.HOST_MAP["dropped"][0]

    lanes = tuple({
        "name": f"L{k}",
        "debug": tuple(
            chip.host_read(lane_base + k * _S.HOST_LANE_STRIDE + word)
            for word in range(len(_S.HOST_LANE_WORDS))
        ),
    } for k in range(len(chip.lanes)))

    producers = tuple(
        (name, (int(p.valid), p.seq, p.tag, p.data))
        for name in _S.FABRIC_PRODUCERS
        if (p := chip.fabric.producers.get(name)) is not None
    )
    ports = tuple(
        (name, chip.host_read(ports_base + i), chip.host_read(dropped_base + i))
        for i, name in enumerate(_S.FABRIC_CONSUMERS)
        if name in chip.fabric.ports
    )

    return {
        "cycle": chip.cycle,
        "run": chip.host_read(_S.HOST_MAP["run"][0]),
        "lanes": lanes,
        "producers": producers,
        "ports": ports,
        "unit_flags": tuple(chip.host_read(_S.HOST_MAP["unit_flags"][0] + u)
                             for u in range(len(chip.pins))),
        "pads": chip.outputs(),
    }


def first_difference(expected, observed, path=""):
    """Return ``(path, expected, observed)`` for the first mismatch, else None."""
    if isinstance(expected, Mapping) and isinstance(observed, Mapping):
        keys = sorted(expected.keys() | observed.keys(), key=repr)
        for key in keys:
            child = f"{path}.{key}" if path else str(key)
            if key not in expected:
                return child, "<missing>", observed[key]
            if key not in observed:
                return child, expected[key], "<missing>"
            difference = first_difference(expected[key], observed[key], child)
            if difference is not None:
                return difference
        return None

    if isinstance(expected, (tuple, list)) and isinstance(observed, (tuple, list)):
        if len(expected) != len(observed):
            return f"{path}.length", len(expected), len(observed)
        for i, (left, right) in enumerate(zip(expected, observed)):
            difference = first_difference(left, right, f"{path}[{i}]")
            if difference is not None:
                return difference
        return None

    return None if expected == observed else (path or "$", expected, observed)
