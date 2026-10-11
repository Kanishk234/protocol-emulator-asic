"""Read-only exact-source SRAM interface locality proposal; no physical changes."""
import hashlib
import argparse
import json
import re
from pathlib import Path
from event_nor2_screen import logical_cells
from fanout_sram_plan import occupancy

NL_SHA = '4b2759eb6aaea642c9f4c6d3efd273edf914ffacef76205ebe252f201ade4a43'
DEF_SHA = 'd7bd995f86e72be6a6a409b1bb3b5d5da34957353b11d7480c66519935260217'
MACRO_LEF_SHA = '845c080938b5e9d1200774190430dad67eea7f1e209fb3094488614e70bb1c2c'
CLEAN_NL_SHA = '2b3925b0d3fb308d16ea07b3b10e9f72598b74cec330c1b147072a8ac47ba9f0'
CLEAN_DEF_SHA = '337c6b32c5325e2da7a68d139f4f7ecc7b80d836e85e8e3456470302e5f8661d'


def allocate(rows, boxes, name, width, height, pin):
    """Find a complete legal-row footprint; boxes include previous proposals."""
    best = None
    for x, y, orient, count, pitch in sorted(rows, key=lambda r: abs(r[1]-pin[1])):
        if best and abs(y-pin[1]) > best[0]:
            break
        intervals = sorted((left, right) for n, left, bottom, right, top in boxes
                           if n != name and bottom < y+height and top > y)
        limit = x+count*pitch
        cursor = x
        for left, right in intervals+[(limit, limit)]:
            end = min(left, limit)
            start = x+max(0, (cursor-x+pitch-1)//pitch)*pitch
            if start+width <= end:
                nearest = x+round((pin[0]-x)/pitch)*pitch
                site = max(start, min(nearest, x+(end-width-x)//pitch*pitch))
                candidate = (abs(site-pin[0])+abs(y-pin[1]), site, y, orient)
                if best is None or candidate < best:
                    best = candidate
            cursor = max(cursor, right)
    if best is None:
        raise ValueError('No free complete buffer footprint')
    return best


def plan(netlist, layout, std_lef, macro_lef, clean_postgpl=False):
    nl_sha, def_sha = (CLEAN_NL_SHA, CLEAN_DEF_SHA) if clean_postgpl else (NL_SHA, DEF_SHA)
    if (hashlib.sha256(netlist.encode()).hexdigest() != nl_sha
            or hashlib.sha256(layout.encode()).hexdigest() != def_sha
            or hashlib.sha256(macro_lef.read_bytes()).hexdigest() != MACRO_LEF_SHA):
        raise ValueError('Wrong reviewed bank source or macro geometry')
    if not re.search(r'UNITS DISTANCE MICRONS 1000\b', layout):
        raise ValueError('Wrong DEF units')
    if not re.search(r'- u_chip.u_sram.sram RM_IHPSG13_1P_512x16_c2_bm_bist\s+\+ FIXED \( 12000 40000 \) FS', layout):
        raise ValueError('Wrong macro placement/orientation')
    cells = logical_cells(netlist)
    (width, height), boxes = occupancy(layout, std_lef, 1000, '__none__', 'sg13cmos5l_buf_4')
    rows = [(int(x), int(y), orient, int(count), int(pitch))
            for x, y, orient, count, pitch in re.findall(
                r'^ROW \S+ CoreSite (\d+) (\d+) (N|FS) DO (\d+) BY 1 STEP (\d+) 0 ;', layout, re.M)
            if int(y) >= 241920]
    if not rows:
        raise ValueError('No reviewed rows above macro halo')
    proposals = []
    macro_text = macro_lef.read_text()
    for bit in range(16):
        net = f'\\u_chip.g_lane[0].u_lane.mem_rdata[{bit}] '
        names = [n for n, (m, pins) in cells.items()
                 if m == 'sg13cmos5l_buf_4' and dict(pins).get('A') == net]
        if len(names) != 1:
            raise ValueError('Expected one BUF4 per SRAM output')
        name = names[0]
        match = re.search(re.escape(name)+r' sg13cmos5l_buf_4[^;]*PLACED \( (\d+) (\d+) \) (N|FS)', layout)
        if not match:
            raise ValueError('Missing SRAM buffer placement')
        old = [int(match[1]), int(match[2]), match[3]]
        body = re.search(r'PIN A_DOUT\['+str(bit)+r'\](.*?)END A_DOUT\['+str(bit)+r'\]', macro_text, re.S)
        rect = re.search(r'RECT\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', body[1]) if body else None
        if not rect:
            raise ValueError('Missing reviewed macro output pin')
        x1, y1, x2, y2 = map(float, rect.groups())
        pin = [round((12+(x1+x2)/2)*1000), round((40+191.34-(y1+y2)/2)*1000)]
        old_distance = abs(old[0]-pin[0])+abs(old[1]-pin[1])
        if old_distance <= 40000:
            continue
        distance, x, y, orient = allocate(rows, boxes, name, width, height, pin)
        if distance >= old_distance:
            raise ValueError('Proposed site does not improve macro proximity')
        boxes = [b for b in boxes if b[0] != name]+[(name, x, y, x+width, y+height)]
        proposals.append(dict(bit=bit, instance=name, master='sg13cmos5l_buf_4',
                              pins=dict(cells[name][1]), old_location=old,
                              new_location=[x, y, orient], old_origin_distance_dbu=old_distance,
                              new_origin_distance_dbu=distance))
    for p in proposals:
        x, y, orient = p['new_location']
        if any(n != p['instance'] and left < x+width and right > x and bottom < y+height and top > y
               for n, left, bottom, right, top in boxes):
            raise ValueError('Combined bank proposal overlap')
    return dict(source_run=37990280838 if clean_postgpl else 38172640071,
                source_stage='postgpl-clean' if clean_postgpl else 'drt',
                netlist_sha256=nl_sha, def_sha256=def_sha,
                proposals=proposals, added_cells=0, changed_logical_cells=0,
                footprint_overlap_count=0, physical_timing_measured=False,
                pin_access_checked=False, power_connectivity_checked=False,
                official_signoff=False)


def placement_fragment(proposal):
    """Reviewable built-in placement input, not an approved official config."""
    sources = {(38172640071, 'drt', NL_SHA, DEF_SHA),
               (37990280838, 'postgpl-clean', CLEAN_NL_SHA, CLEAN_DEF_SHA)}
    if ((proposal.get('source_run'), proposal.get('source_stage'),
         proposal.get('netlist_sha256'), proposal.get('def_sha256')) not in sources
            or proposal.get('added_cells') != 0 or proposal.get('changed_logical_cells') != 0
            or proposal.get('footprint_overlap_count') != 0):
        raise ValueError('Wrong bank proposal provenance')
    placements = {}
    for item in proposal['proposals']:
        name = item['instance']
        x, y, orientation = item['new_location']
        if name in placements or orientation not in ('N', 'FS') or x < 0 or y < 0:
            raise ValueError('Duplicate or invalid placement')
        placements[name] = dict(location=[x/1000, y/1000], orientation=orientation)
    return {'MANUAL_GLOBAL_PLACEMENTS': placements}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('netlist', type=Path)
    parser.add_argument('layout', type=Path)
    parser.add_argument('standard_lef', type=Path)
    parser.add_argument('macro_lef', type=Path)
    parser.add_argument('--clean-postgpl', action='store_true')
    args = parser.parse_args()
    proposal = plan(args.netlist.read_text(), args.layout.read_text(), args.standard_lef, args.macro_lef,
                    clean_postgpl=args.clean_postgpl)
    print(json.dumps(dict(proposal=proposal, candidate_placement_fragment=placement_fragment(proposal)), indent=2))
