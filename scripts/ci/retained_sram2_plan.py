"""One unchanged-cell relocation on exact selected setup-route checkpoint."""
import hashlib
import re
from event_nor2_screen import logical_cells

NL_SHA = '402b87e6f798a8c760b277bf148a048527a74e92a87069db2801d148a0301e90'
DEF_SHA = '73abf7de3ab00c578ca5d6718d6670f930d189c26ecb30ae8bd5d4c3d083d3eb'


def plan(before, layout, kind):
    if kind != 'relocate' or hashlib.sha256(before.encode()).hexdigest() != NL_SHA or hashlib.sha256(layout.encode()).hexdigest() != DEF_SHA:
        raise ValueError('Wrong selected SRAM relocation source')
    cell = logical_cells(before).get('wire9439')
    if cell != ('sg13cmos5l_buf_4', tuple(sorted([('A', '\\u_chip.g_lane[0].u_lane.mem_rdata[2] '), ('X', 'net9439')]))):
        raise ValueError('Wrong selected SRAM output buffer')
    if not re.search(r'wire9439 sg13cmos5l_buf_4[^;]*PLACED \( 341280 230580 \) N', layout):
        raise ValueError('Wrong original SRAM buffer placement')
    return dict(source_run=38116800326, kind=kind, netlist_sha256=NL_SHA,
                def_sha256=DEF_SHA, instance='wire9439', master=cell[0],
                old_location=[341280,230580,'N'], new_location=[45120,245700,'N'],
                changed_cells=0, added_buffers=0, relocated_instances=1,
                physical_timing_measured=False, official_signoff=False)


def validate_change(before, layout, after, proposal):
    if plan(before, layout, proposal['kind']) != proposal:
        raise ValueError('Wrong selected SRAM proposal')
    if logical_cells(before) != logical_cells(after):
        raise ValueError('Relocation must preserve every cell and net')
    return proposal


def verify_location(layout):
    if not re.search(r'wire9439 sg13cmos5l_buf_4[^;]*PLACED \( 45120 245700 \) N', layout):
        raise ValueError('Selected SRAM buffer moved from audited destination')
