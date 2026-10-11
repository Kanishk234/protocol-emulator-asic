"""One NOR4 strength change on the timing-qualified dominant route."""
import hashlib
import json
from event_nor2_screen import logical_cells

NL_SHA = '402b87e6f798a8c760b277bf148a048527a74e92a87069db2801d148a0301e90'
DEF_SHA = '73abf7de3ab00c578ca5d6718d6670f930d189c26ecb30ae8bd5d4c3d083d3eb'


def plan(before, layout, kind):
    if kind != 'setup' or hashlib.sha256(before.encode()).hexdigest() != NL_SHA or hashlib.sha256(layout.encode()).hexdigest() != DEF_SHA:
        raise ValueError('Wrong measured fanout setup source')
    cell = logical_cells(before).get('_25245_')
    if cell is None or cell[0] != 'sg13cmos5l_nor4_1' or set(dict(cell[1])) != {'A', 'B', 'C', 'D', 'Y'}:
        raise ValueError('Wrong reviewed setup buffer')
    return dict(source_run=38116800326, kind=kind, netlist_sha256=NL_SHA,
                def_sha256=DEF_SHA, instance='_25245_', old_master=cell[0],
                new_master='sg13cmos5l_nor4_2', pins=dict(cell[1]),
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
    def word(value):
        value = value.strip().removeprefix('\\')
        value = value.replace('[', '\\[').replace(']', '\\]')
        if any(c in value for c in '{}\n\r'):
            raise ValueError('Unsafe Tcl target')
        return '{' + value + '}'
    pins = ' '.join(word(k) + ' ' + word(v) for k, v in sorted(p['pins'].items()))
    return ('tripwire_size_native_hold100 {{' + word(p['instance']) + ' '
            + word(p['old_master']) + ' ' + word(p['new_master']) + ' {' + pins + '}}}\n')
