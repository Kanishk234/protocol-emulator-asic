"""One identity-buffer strength change on the selected extracted fanout route."""
import hashlib
import json
from event_nor2_screen import logical_cells

NL_SHA = '388d1b91816f8ce1ad3cdbae071998617637979425e46d3a4b13af618ec4cb67'
DEF_SHA = '344286c41b56c9d279b4556b5e8ff24be5a8c4f2c68163e19016d9f56dd84ccd'


def plan(before, layout, kind):
    if kind != 'setup' or hashlib.sha256(before.encode()).hexdigest() != NL_SHA or hashlib.sha256(layout.encode()).hexdigest() != DEF_SHA:
        raise ValueError('Wrong measured fanout setup source')
    cell = logical_cells(before).get('place7307')
    if cell is None or cell[0] != 'sg13cmos5l_buf_1' or set(dict(cell[1])) != {'A', 'X'}:
        raise ValueError('Wrong reviewed setup buffer')
    return dict(source_run=38103189246, kind=kind, netlist_sha256=NL_SHA,
                def_sha256=DEF_SHA, instance='place7307', old_master=cell[0],
                new_master='sg13cmos5l_buf_4', pins=dict(cell[1]),
                changed_cells=1, added_buffers=0, repair_receipts=1,
                physical_timing_measured=False, official_signoff=False)


def validate_change(before, layout, after, proposal):
    canonical = plan(before, layout, proposal['kind'])
    if canonical != proposal:
        raise ValueError('Wrong setup proposal')
    expected = logical_cells(before)
    name = canonical['instance']
    expected[name] = (canonical['new_master'], expected[name][1])
    if logical_cells(after) != expected:
        raise ValueError('Expected only one buffer master change; preserve all wiring/cells')
    return canonical


def target_call(before, layout, kind):
    p = plan(before, layout, kind)
    if any(not v.replace('_', '').isalnum() for v in p['pins'].values()):
        raise ValueError('Unsafe setup target net')
    pins = ' '.join(f'{k} {v}' for k, v in sorted(p['pins'].items()))
    return f"tripwire_size_native_hold100 {{{{{p['instance']} {p['old_master']} {p['new_master']} {{{pins}}}}}}}\n"
