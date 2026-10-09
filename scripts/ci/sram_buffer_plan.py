"""Read-only, exact-source row proposal; occupancy and routing remain unproven."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from event_nor2_screen import logical_cells
from native_route_gl import STRENGTH_NETLIST_SHA


def occupancy(text, lef, units):
    if hashlib.sha256(lef.read_bytes()).hexdigest() != 'c47c436758ae87288324aa1f5a84fcc8faf813bf19df1a400b32258fff4e1219':
        raise ValueError('Unreviewed standard-cell geometry')
    sizes = {}
    for name, body in re.findall(r'^MACRO (\S+)(.*?)^END \1\s*$', lef.read_text(), re.M | re.S):
        match = re.search(r'\bSIZE\s+([\d.]+)\s+BY\s+([\d.]+)', body)
        if match:
            sizes[name] = tuple(round(float(v) * units) for v in match.groups())
    sizes['RM_IHPSG13_1P_512x16_c2_bm_bist'] = (236800, 191340)
    section = text.split('COMPONENTS ', 1)[1].split('END COMPONENTS', 1)[0]
    placed = []
    for name, master, attrs in re.findall(r'^\s*- (\S+) (\S+)(.*?);', section, re.M | re.S):
        match = re.search(r'\+ (?:PLACED|FIXED) \(\s*(\d+)\s+(\d+)\s*\) (\S+)', attrs)
        if not match:
            raise ValueError('Unplaced component ' + name)
        if master not in sizes or match[3] not in ('N', 'S', 'FN', 'FS'):
            raise ValueError('Unknown component geometry ' + name)
        x, y = int(match[1]), int(match[2])
        width, height = sizes[master]
        if name != 'wire9447':
            placed.append((name, x, y, x + width, y + height))
    return sizes['sg13cmos5l_buf_4'], placed


def plan(netlist, layout, lef=None):
    if hashlib.sha256(layout.read_bytes()).hexdigest() != 'c2496ceec0cfcd6bf74b4f0f69373c737ef5ed7eb081a1343d0478e7ed1a8e2f':
        raise ValueError('Unreviewed routed layout')
    if hashlib.sha256(netlist.read_bytes()).hexdigest() != STRENGTH_NETLIST_SHA:
        raise ValueError('Unreviewed routed netlist')
    cells = logical_cells(netlist.read_text())
    expected = ('sg13cmos5l_buf_4', tuple(sorted({
        'X': 'net9447', 'A': '\\u_chip.g_lane[0].u_lane.mem_rdata[0] '}.items())))
    if cells.get('wire9447') != expected:
        raise ValueError('Wrong SRAM buffer connectivity')
    text = layout.read_text()
    units = int(re.search(r'UNITS DISTANCE MICRONS (\d+)', text)[1])
    if units != 1000:
        raise ValueError('Unexpected layout units')
    geometry = occupancy(text, lef, units) if lef else None
    if not re.search(r'wire9447 sg13cmos5l_buf_4[^;]*PLACED \( 473760 230580 \) N', text):
        raise ValueError('Wrong SRAM buffer placement')
    # Pin center from pinned macro LEF and observed FS placement (12,40).
    pin_x, pin_y = 22.75, 231.21
    rows = []
    pattern = r'^ROW (\S+) CoreSite (\d+) (\d+) (\S+) DO (\d+) BY 1 STEP (\d+) 0 ;'
    for name, x, y, orient, count, pitch in re.findall(pattern, text, re.M):
        x, y, count, pitch = int(x), int(y), int(count), int(pitch)
        if y / units < 241.92:
            continue  # Macro halo cuts lower rows; do not propose sites inside it.
        index = max(0, min(count - 1, round((pin_x * units - x) / pitch)))
        candidate_x = (x + index * pitch) / units
        distance = abs(candidate_x - pin_x) + abs(y / units - pin_y)
        candidate = dict(row=name, x_um=candidate_x, y_um=y / units,
                         orientation=orient, origin_distance_um=distance)
        if geometry:
            (width, height), placed = geometry
            intervals = sorted((left, right) for _, left, bottom, right, top in placed
                               if bottom < y + height and top > y)
            site = x + index * pitch
            candidate['initial_overlap_count'] = sum(left < site + width and right > site
                                                     for left, right in intervals)
            # Search row gaps, keeping the complete buffer footprint within the row.
            cursor, limit = x, x + count * pitch
            free = []
            for left, right in intervals + [(limit, limit)]:
                end = min(left, limit)
                start = x + max(0, (cursor - x + pitch - 1) // pitch) * pitch
                if start + width <= end:
                    nearest = max(start, min(site, x + (end - width - x) // pitch * pitch))
                    free.append(nearest)
                cursor = max(cursor, right)
            if not free:
                continue
            best = min(free, key=lambda v: abs(v / units - pin_x))
            candidate.update(x_um=best / units,
                             origin_distance_um=abs(best / units - pin_x) + abs(y / units - pin_y),
                             footprint_overlap_count=0)
        rows.append(candidate)
    if not rows:
        raise ValueError('No candidate row')
    return dict(source_route=37954320974, instance='wire9447',
                candidates=sorted(rows, key=lambda r: r['origin_distance_um'])[:3],
                physical_change_applied=False, occupancy_checked=bool(geometry),
                pin_access_checked=False, power_connectivity_checked=False,
                legalization_required=True, official_signoff=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('netlist', type=Path)
    parser.add_argument('layout', type=Path)
    parser.add_argument('--lef', type=Path)
    args = parser.parse_args()
    print(json.dumps(plan(args.netlist, args.layout, args.lef), indent=2))
