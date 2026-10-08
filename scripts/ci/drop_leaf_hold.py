"""Exact nine-leaf hold repair inventory for successful screen37803300460."""
from event_nor2_screen import logical_cells

TARGETS = (
    ('_46568_', '_00384_', '_34844_', 'sg13cmos5l_inv_1'),
    ('_46523_', '_00339_', '_34677_', 'sg13cmos5l_a21oi_1'),
    ('_46565_', '_00381_', '_34838_', 'sg13cmos5l_inv_1'),
    ('_47657_', '_01449_', '_42488_', 'sg13cmos5l_nor3_1'),
    ('_48411_', '_00010_', '_28711_', 'sg13cmos5l_nor4_1'),
    ('_46522_', '_00338_', '_34661_', 'sg13cmos5l_a21oi_1'),
    ('_47656_', '_01448_', '_42482_', 'sg13cmos5l_nor2_1'),
    ('_47559_', '_01351_', '_42037_', 'sg13cmos5l_a21oi_1'),
    ('_46519_', '_00335_', '_34611_', 'sg13cmos5l_a21oi_1'),
)


def validate_drop_leaf_hold(before, after):
    original, changed = logical_cells(before), logical_cells(after)
    for sink, net, driver, master in TARGETS:
        dcell, scell = original.get(driver), original.get(sink)
        if (dcell is None or dcell[0] != master or dict(dcell[1]).get('Y') != net
                or scell is None or scell[0] != 'sg13cmos5l_dfrbpq_1'
                or dict(scell[1]).get('D') != net):
            raise ValueError('Unreviewed dropped-event hold source')
        terminals = sorted((name, pin) for name, (_, ports) in original.items()
                           for pin, value in ports if value == net)
        if terminals != sorted(((driver, 'Y'), (sink, 'D'))):
            raise ValueError('Dropped-event hold branch fanout changed')
        new_net, buffer = f'tripwire_drop_hold_net{sink}', f'tripwire_drop_hold_buf{sink}'
        if buffer in original or any(v == new_net for _, ports in original.values() for _, v in ports):
            raise ValueError('Duplicate dropped-event hold repair')
        ports = dict(scell[1])
        ports['D'] = new_net
        original[sink] = (scell[0], tuple(sorted(ports.items())))
        original[buffer] = ('sg13cmos5l_buf_1', (('A', net), ('X', new_net)))
    if original != changed:
        raise ValueError('Dropped-event hold repair changed additional logic or wiring')
