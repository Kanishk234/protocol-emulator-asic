"""One unchanged-cell relocation on exact selected setup-route checkpoint."""
import hashlib
import re
from event_nor2_screen import logical_cells

NL_SHA = 'df372dc6760b2cd7b1168637025154b6254aae71c7f6c1a8a526bb2aa35f0427'
DEF_SHA = 'e058534eb8f3e4c872481fa8bc4654539a853e12026e9ba9ddb24d862ae71c06'


def plan(before, layout, kind):
    if kind != 'relocate' or hashlib.sha256(before.encode()).hexdigest() != NL_SHA or hashlib.sha256(layout.encode()).hexdigest() != DEF_SHA:
        raise ValueError('Wrong selected SRAM relocation source')
    cell = logical_cells(before).get('wire9447')
    if cell != ('sg13cmos5l_buf_4', tuple(sorted([('A', '\\u_chip.g_lane[0].u_lane.mem_rdata[0] '), ('X', 'net9447')]))):
        raise ValueError('Wrong selected SRAM output buffer')
    if not re.search(r'wire9447 sg13cmos5l_buf_4[^;]*PLACED \( 473760 230580 \) N', layout):
        raise ValueError('Wrong original SRAM buffer placement')
    return dict(source_run=38108912678, kind=kind, netlist_sha256=NL_SHA,
                def_sha256=DEF_SHA, instance='wire9447', master=cell[0],
                old_location=[473760,230580,'N'], new_location=[25920,245700,'N'],
                changed_cells=0, added_buffers=0, relocated_instances=1,
                physical_timing_measured=False, official_signoff=False)


def validate_change(before, layout, after, proposal):
    if plan(before, layout, proposal['kind']) != proposal:
        raise ValueError('Wrong selected SRAM proposal')
    if logical_cells(before) != logical_cells(after):
        raise ValueError('Relocation must preserve every cell and net')
    return proposal


def verify_location(layout):
    if not re.search(r'wire9447 sg13cmos5l_buf_4[^;]*PLACED \( 25920 245700 \) N', layout):
        raise ValueError('Selected SRAM buffer moved from audited destination')
