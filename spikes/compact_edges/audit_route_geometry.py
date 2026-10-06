#!/usr/bin/env python3
"""Measure saved routing-marker locality against actual rows, cells and pins.

Pin proximity and clustered markers guide diagnosis; neither proves a cause.
Uses only exported physical geometry/native reports, never writes an ODB.
"""
import argparse
import csv
import html
import json
import math
from pathlib import Path
import re


def area(box):
    return max(0, box[2]-box[0]) * max(0, box[3]-box[1])


def intersect(a, b):
    return (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))


def distance(a, b):
    return math.hypot(max(a[0]-b[2], b[0]-a[2], 0),
                      max(a[1]-b[3], b[1]-a[3], 0))


def audit(geometry, report, out):
    lines = list(csv.reader(geometry.open(), delimiter='\t'))
    dbu = float(next(row[1] for row in lines if row[0] == 'DBU'))
    rows, cells, pins = [], [], []
    for row in lines:
        if row[0] == 'ROW':
            rows.append(tuple(float(x)/dbu for x in row[2:6]))
        elif row[0] == 'CELL':
            cells.append(dict(name=row[1], master=row[2], macro=row[3]=='1',
                              box=tuple(float(x)/dbu for x in row[4:8])))
        elif row[0] == 'PIN':
            pins.append(dict(inst=row[1], port=row[2], net=row[3], layer=row[4],
                             box=tuple(float(x)/dbu for x in row[5:9])))
    markers = []
    for block in report.read_text().split('violation type:')[1:]:
        m = re.search(r'bbox = \(([-\d.]+), ([-\d.]+)\) - '
                      r'\(([-\d.]+), ([-\d.]+)\) on Layer (\S+)', block)
        if not m:
            raise ValueError('Unrecognized native routing marker')
        markers.append(dict(box=tuple(map(float, m.groups()[:4])), layer=m[5],
                            nets=sorted(set(re.findall(r'net:(\S+)', block)))))
    std = [cell for cell in cells if not cell['macro']]
    # Actual intersecting row rectangles are the available placement area.
    bins = []
    for y in range(0, 750, 50):
        for x in (0, 50, 100):
            box = (x, y, min(x+50, 121.44), y+50)
            ra = sum(area(intersect(r, box)) for r in rows)
            ca = sum(area(intersect(c['box'], box)) for c in std)
            count = sum(x <= (m['box'][0]+m['box'][2])/2 < box[2] and
                        y <= (m['box'][1]+m['box'][3])/2 < y+50 for m in markers)
            np = sum(x <= (p['box'][0]+p['box'][2])/2 < box[2] and
                     y <= (p['box'][1]+p['box'][3])/2 < y+50 for p in pins)
            if ra or count:
                bins.append(dict(box_um=box, row_area_um2=ra, cell_area_um2=ca,
                                 utilization=ca/ra if ra else None,
                                 signal_pin_rectangles=np, routing_markers=count))
    # A pin on a lower layer can require a via at the same XY. This is a
    # distance measurement, not classification as a proven pin-access failure.
    pin_by_net = {}
    for p in pins:
        pin_by_net.setdefault(p['net'], []).append(p)
    distances = []
    for marker in markers:
        nearby = [p for n in marker['nets'] for p in pin_by_net.get(n, [])]
        distances.append(min((distance(marker['box'], p['box']) for p in nearby),
                             default=math.inf))
    parent = list(range(len(markers)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, a in enumerate(markers):
        for j, b in enumerate(markers[:i]):
            if distance(a['box'], b['box']) <= 1:
                parent[find(i)] = find(j)
    clusters = {}
    for i, m in enumerate(markers):
        clusters.setdefault(find(i), []).append(m)
    details = []
    for group in clusters.values():
        details.append(dict(markers=len(group),
            bbox_um=(min(m['box'][0] for m in group), min(m['box'][1] for m in group),
                     max(m['box'][2] for m in group), max(m['box'][3] for m in group)),
            nets=sorted(set(n for m in group for n in m['nets']))))
    result = dict(geometry=str(geometry.resolve()), report=str(report.resolve()),
                  markers=len(markers), cluster_join_distance_um=1,
                  spatial_clusters=sorted(details, key=lambda c:-c['markers']),
                  marker_pin_distance_counts={str(d):sum(x <= d for x in distances)
                                               for d in (0, .5, 1, 2)},
                  west_bins=sorted(bins, key=lambda b:-b['routing_markers']),
                  interpretation='Proximity/occupancy evidence, not causal proof or signoff')
    out.mkdir(exist_ok=False)
    (out/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    # A standalone physical artifact, with the west channel enlarged.
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-5 -5 140 720">',
           '<rect x="-5" y="-5" width="140" height="720" fill="white"/>']
    for cell in std:
        x1, y1, x2, y2 = cell['box']
        if x1 >= 125:
            continue
        color = '#7aa6c2' if cell['name'].startswith('hold') else '#999999'
        title = html.escape(cell['name']+' '+cell['master'])
        svg.append(f'<rect x="{x1}" y="{710-y2}" width="{x2-x1}" height="{y2-y1}" '
                   f'fill="{color}" opacity="0.55"><title>{title}</title></rect>')
    for m in markers:
        x1, y1, x2, y2 = m['box']
        svg.append(f'<circle cx="{(x1+x2)/2}" cy="{710-(y1+y2)/2}" r="1" fill="#d90027">'
                   f'<title>{html.escape(" ".join(m["nets"]))}</title></circle>')
    svg.append('</svg>')
    (out/'west_cells_markers.svg').write_text('\n'.join(svg)+'\n')
    print(json.dumps({k:result[k] for k in ('markers', 'marker_pin_distance_counts')}))
    print('Spatial clusters:', len(clusters))
    print('Top west bins:', json.dumps(result['west_bins'][:5]))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--geometry', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    audit(a.geometry, a.report, a.out)
