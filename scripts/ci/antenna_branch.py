"""Exact-source, one-buffer branch audit; no timing or antenna pass implied."""
import hashlib
from event_nor2_screen import logical_cells
from native_route_gl import STRENGTH_NETLIST_SHA

SOURCE_NET = '_03831_'
BUFFER = 'tripwire_antenna_branch_buf'
NEW_NET = 'tripwire_antenna_branch_net'
SINKS = {('ANTENNA_2', 'A'), ('ANTENNA_3', 'A'), ('ANTENNA_4', 'A'), ('ANTENNA_5', 'A'),
         ('_28936_', 'B'), ('_28973_', 'B'), ('_29032_', 'B'), ('_29046_', 'B')}


def validate_source(before):
    if hashlib.sha256(before.encode()).hexdigest() != STRENGTH_NETLIST_SHA:
        raise ValueError('Wrong timing-passing branch source')
    old = logical_cells(before)
    if any(net == NEW_NET for _, pins in old.values() for _, net in pins):
        raise ValueError('Branch output net already exists')
    if old.get('_28807_', (None,))[0] != 'sg13cmos5l_nand3_1':
        raise ValueError('Wrong branch driver')
    loads = {(name, pin) for name, (_, pins) in old.items() for pin, net in pins
             if net == SOURCE_NET and (name, pin) != ('_28807_', 'Y')}
    if len(loads) != 15 or not SINKS <= loads:
        raise ValueError('Wrong audited branch connectivity')
    for name, pin in SINKS:
        if name.startswith('ANTENNA_') and old[name][0] != 'sg13cmos5l_antennanp':
            raise ValueError('Wrong antenna master')
    return old, loads


def validate_change(before, after):
    old, loads = validate_source(before)
    new = logical_cells(after)
    if set(new) != set(old) | {BUFFER} or BUFFER in old:
        raise ValueError('Expected exactly one added buffer and no deleted cells')
    for name, (master, pins) in old.items():
        expected = (master, tuple(sorted((pin, NEW_NET if (name, pin) in SINKS else net)
                                        for pin, net in pins)))
        if new[name] != expected:
            raise ValueError('Unexpected branch logical or connectivity change')
    if new[BUFFER] != ('sg13cmos5l_buf_4', tuple(sorted([('A', SOURCE_NET), ('X', NEW_NET)]))):
        raise ValueError('Wrong identity buffer connectivity')
    # Count actual attached signal pins, not weighted STA fanout.
    return dict(added_buffers=1, moved_pins=8, retained_antenna_cells=True,
                upstream_sink_pins=len(loads)-len(SINKS)+1, downstream_sink_pins=len(SINKS),
                topology_only=True, official_signoff=False)
