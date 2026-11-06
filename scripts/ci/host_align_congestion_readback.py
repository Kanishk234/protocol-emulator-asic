"""Read saved host-screen congestion without initializing or modifying routing."""
import hashlib
import json
from pathlib import Path
import sys
from c_select_congestion_readback import overloaded_edges


def parse_guides(text):
    nets = {}; name = None; opened = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line: continue
        if line == '(':
            if name is None or opened: raise ValueError('Unexpected guide opening')
            opened = True
        elif line == ')':
            if not opened or not nets[name]: raise ValueError('Empty guide')
            opened = False; name = None
        elif not opened:
            if name is not None or line in nets: raise ValueError('Duplicate guide net')
            name = line; nets[name] = []
        else:
            fields = line.split()
            if len(fields) != 5: raise ValueError('Bad guide width')
            x1,y1,x2,y2 = map(int,fields[:4])
            if x1 >= x2 or y1 >= y2: raise ValueError('Bad guide rectangle')
            nets[name].append((x1,y1,x2,y2,fields[4]))
    if name is not None or opened or not nets: raise ValueError('Incomplete guides')
    return nets


def match_guides(guides, edges):
    for edge in edges:
        a,b = edge['start_dbu'],edge['end_dbu']
        candidates = []
        for name, boxes in guides.items():
            if any(layer == edge['layer'] and x1 <= min(a[0],b[0]) and
                   max(a[0],b[0]) <= x2 and y1 <= min(a[1],b[1]) and
                   max(a[1],b[1]) <= y2 for x1,y1,x2,y2,layer in boxes):
                candidates.append(name)
        if not candidates: raise ValueError('Overflow edge has no guide candidate')
        edge['guide_overlap_candidates'] = sorted(candidates)
    return edges


def main():
    from openroad import Tech, Design
    sys.path.insert(0, str(Path('scripts/ci').resolve()))
    manifest = json.loads(Path('spikes/phase2_stock_flow/host_align_congestion_source.json').read_text())
    root = Path('frozen-artifact')
    odb = root / manifest['odb']['path']
    digest = hashlib.sha256(odb.read_bytes()).hexdigest()
    if digest != manifest['odb']['sha256']:
        raise ValueError('Wrong edited ODB')
    tech = Tech()
    design = Design(tech)
    design.readDb(str(odb))
    db = tech.getDB()
    block = db.getChip().getBlock()
    grid = block.getGCellGrid()
    if grid is None:
        raise ValueError('Missing saved congestion map')
    layers = [db.getTech().findLayer(name) for name in ('Metal2', 'Metal3', 'Metal4')]
    if any(layer is None for layer in layers):
        raise ValueError('Missing routing layer')
    edges, totals = overloaded_edges(grid, layers)
    actual = sum(row['overflow'] for row in totals.values())
    if abs(actual - manifest['expected_overflow']) > 1e-6:
        raise ValueError(f'Saved congestion does not match live gate: {actual}')
    guide = root / manifest['segments']
    if hashlib.sha256(guide.read_bytes()).hexdigest() != manifest['guide_sha256']:
        raise ValueError('Wrong final guide geometry')
    match_guides(parse_guides(guide.read_text()), edges)
    if hashlib.sha256(odb.read_bytes()).hexdigest() != digest:
        raise ValueError('Input ODB changed')
    result = dict(source_run=manifest['run']['id'], source_odb_sha256=digest,
                  source_odb_unchanged=True, expected_overflow=manifest['expected_overflow'],
                  layer_totals=totals, overloaded_edges=edges, design_qualified=False,
                  scope='Read-only saved congestion validated against final live routing gate; '
                        'guide-overlap candidates only, not exact crossings or connectivity; '
                        'no placement, repair, rerouting, STA or closure claim')
    output = Path('runs/congestion-readback/result.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(overflow=actual, overloaded_edges=len(edges), design_qualified=False)))


if __name__ == '__main__':
    main()
