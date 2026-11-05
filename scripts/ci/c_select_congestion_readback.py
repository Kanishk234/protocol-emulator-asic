"""Read saved post-route congestion; never repair, place or route anything."""
import hashlib
import json
import math
from pathlib import Path
import sys


def overloaded_edges(grid, layers):
    xs, ys = list(grid.getGridX()), list(grid.getGridY())
    if len(xs) < 2 or len(ys) < 2:
        raise ValueError('Missing congestion grid')
    if sorted(set(xs)) != xs or sorted(set(ys)) != ys:
        raise ValueError('Invalid congestion grid coordinates')
    def center(coords, index):
        span = coords[index+1]-coords[index] if index+1 < len(coords) else coords[-1]-coords[-2]
        return coords[index] + span // 2
    records, totals = [], {}
    for layer in layers:
        name = layer.getName()
        direction = str(layer.getDirection())
        if direction not in ('HORIZONTAL', 'VERTICAL'):
            raise ValueError('Unexpected routing direction')
        capacity = usage = overflow = 0.0
        for x in range(len(xs)):
            for y in range(len(ys)):
                cap, used = float(grid.getCapacity(layer, x, y)), float(grid.getUsage(layer, x, y))
                if not all(math.isfinite(v) and v >= 0 for v in (cap, used)):
                    raise ValueError('Invalid capacity/usage')
                capacity += cap
                usage += used
                excess = max(0.0, used-cap)
                overflow += excess
                if excess:
                    if ((direction == 'HORIZONTAL' and x+1 >= len(xs)) or
                            (direction == 'VERTICAL' and y+1 >= len(ys))):
                        raise ValueError('Overflow at unmappable outer grid edge')
                    start = [center(xs, x), center(ys, y)]
                    end = ([center(xs, x+1), start[1]] if direction == 'HORIZONTAL'
                           else [start[0], center(ys, y+1)])
                    records.append(dict(layer=name, direction=direction, x_index=x, y_index=y,
                                        start_dbu=start, end_dbu=end, capacity=cap, usage=used,
                                        overflow=excess))
        totals[name] = dict(capacity=capacity, usage=usage, overflow=overflow)
    return records, totals


def crossing_nets(routes, edges):
    for edge in edges:
        names = []
        horizontal = edge['direction'] == 'HORIZONTAL'
        start, end = edge['start_dbu'], edge['end_dbu']
        for name, segments in routes.items():
            for a, b in segments:
                if a[2] != edge['layer'] or b[2] != edge['layer']:
                    continue
                if horizontal:
                    covered = (a[1] == b[1] == start[1] and
                               min(a[0], b[0]) <= start[0] and max(a[0], b[0]) >= end[0])
                else:
                    covered = (a[0] == b[0] == start[0] and
                               min(a[1], b[1]) <= start[1] and max(a[1], b[1]) >= end[1])
                if covered:
                    names.append(name)
                    break
        if not names:
            raise ValueError('Overloaded grid edge has no matching exported route')
        edge['crossing_route_names'] = sorted(names)
    return edges


def main():
    from openroad import Tech, Design
    sys.path.insert(0, str(Path('scripts/ci').resolve()))
    from route_segment_audit import parse
    manifest = json.loads(Path('spikes/phase2_stock_flow/c_select_congestion_source.json').read_text())
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
    routes = parse((root / manifest['segments']).read_text())
    crossing_nets(routes, edges)
    if hashlib.sha256(odb.read_bytes()).hexdigest() != digest:
        raise ValueError('Input ODB changed')
    result = dict(source_run=manifest['run']['id'], source_odb_sha256=digest,
                  source_odb_unchanged=True, expected_overflow=manifest['expected_overflow'],
                  layer_totals=totals, overloaded_edges=edges, design_qualified=False,
                  scope='Read-only saved congestion validated against final live routing gate; '
                        'no placement, repair, rerouting, STA or closure claim')
    output = Path('runs/congestion-readback/result.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(overflow=actual, overloaded_edges=len(edges), design_qualified=False)))


if __name__ == '__main__':
    main()
