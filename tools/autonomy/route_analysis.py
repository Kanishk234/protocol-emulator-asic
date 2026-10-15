"""Read-only measurements of validated native global-route segment exports."""
import argparse
import json
from collections import Counter
from collections import deque
from pathlib import Path


def summarize(segments, box=(121440, 15120, 1241760, 684180)):
    """DBU lengths exclude vias; strict OBS interior excludes boundary touching."""
    layers = Counter()
    crossings = []
    vias = 0
    for segment in segments:
        if len(segment) != 6:
            raise ValueError('Expected six fields')
        x, y, layer, xx, yy, other = segment
        if any(type(v) is not int for v in (x, y, xx, yy)):
            raise ValueError('Coordinates must be integer DBU')
        if layer not in ('Metal1', 'Metal2', 'Metal3', 'Metal4') or other not in ('Metal1', 'Metal2', 'Metal3', 'Metal4'):
            raise ValueError('Unsupported layer')
        if (x != xx and y != yy) or (layer != other and (x != xx or y != yy)):
            raise ValueError('Non-Manhattan segment')
        if layer != other:
            vias += 1
            continue
        length = abs(x-xx)+abs(y-yy)
        layers[layer] += length
        left, bottom, right, top = box
        horizontal = y == yy and bottom < y < top and max(min(x, xx), left) < min(max(x, xx), right)
        vertical = x == xx and left < x < right and max(min(y, yy), bottom) < min(max(y, yy), top)
        if horizontal or vertical:
            crossings.append(segment)
    return {'planar_dbu': sum(layers.values()), 'layer_planar_dbu': dict(layers),
            'via_segment_count': vias, 'obs_interior_segments': crossings,
            'scope': 'failed coarse global route, not detailed routing or physical acceptance'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('targets', type=Path)
    parser.add_argument('--grid', type=Path, help='Optional calibrated D-087 native-grid.tsv')
    parser.add_argument('--release-group', action='append', default=[],
                        help='Comma-separated target names to free together in the static graph; requires --grid')
    args = parser.parse_args()
    data = json.loads(args.targets.read_text())
    if args.release_group and not args.grid:
        parser.error('--release-group requires --grid')
    result = {name: summarize(segments) for name, segments in data['targets'].items()}
    if args.grid:
        result['peripheral_slices'] = peripheral_slices(args.grid)
        result['static_residual_connectivity'] = residual_connectivity(
            args.grid, data['targets'], [group.split(',') for group in args.release_group])
    print(json.dumps(result, indent=2))


def peripheral_slices(path):
    """Fixed alternative-path samples; not a corridor feasibility proof."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'test_internal'))
    from audit_native_grid import audit
    audit(path)  # Reuse strict completeness/numeric/duplicate validation.
    lines = Path(path).read_text().splitlines()
    xs = list(map(int, lines[1].split('\t')[1].split()))
    ys = list(map(int, lines[2].split('\t')[1].split()))
    if xs != list(range(0, 1281601, 7200)) or ys != list(range(0, 698401, 7200)):
        raise ValueError('Unexpected grid for measured fixed slices')
    cells = {}
    for row in lines[3:]:
        _, layer, x, y, capacity, usage = row.split('\t')
        cells[layer, int(x), int(y)] = (float(capacity), float(usage))
    result = {}
    for name, layers, indices, location in (
        ('west', ('Metal2', 'Metal4'), range(33, 95), lambda index: (16, index)),
        ('north', ('Metal1', 'Metal3'), range(16, 108), lambda index: (index, 95)),
    ):
        result[name] = {'simultaneously_saturated_indices': [], 'layers': {}}
        for layer in layers:
            values = [cells[(layer, *location(index))] for index in indices]
            result[name]['layers'][layer] = {
                'minimum_residual': min(capacity-usage for capacity, usage in values),
                'zero_capacity_samples': sum(capacity == 0 for capacity, usage in values),
            }
        result[name]['simultaneously_saturated_indices'] = [index for index in indices
            if all(cells[(layer, *location(index))][1] >= cells[(layer, *location(index))][0]
                   for layer in layers)]
    return result


def release_allocations(cells, targets, names):
    """Free unique edges per net, preserving multiplicity across different nets."""
    if not names or len(set(names)) != len(names):
        raise ValueError('Release group must contain distinct target names')
    adjusted = dict(cells)
    for name in names:
        if name not in targets:
            raise ValueError('Unknown release target: ' + name)
        for edge in planar_edges(targets[name]):
            if edge not in adjusted:
                raise ValueError('Own route edge outside observed grid')
            adjusted[edge] += 1
    return adjusted


def residual_connectivity(path, targets, groups=()):
    """Optimistic graph with free vias; current-net usage is NOT removed."""
    # Validate before independently interpreting preferred-direction cell edges.
    peripheral_slices(path)
    rows = Path(path).read_text().splitlines()
    xs = list(map(int, rows[1].split('\t')[1].split()))
    ys = list(map(int, rows[2].split('\t')[1].split()))
    cells = {}
    for row in rows[3:]:
        _, layer, x, y, capacity, usage = row.split('\t')
        cells[layer, int(x), int(y)] = float(capacity)-float(usage)
    original = residual_paths(cells, len(xs)-1, len(ys)-1, targets)
    released = {}
    for name, segments in targets.items():
        own = planar_edges(segments)
        adjusted = release_allocations(cells, targets, [name])
        observation = residual_paths(adjusted, len(xs)-1, len(ys)-1, {name: segments})[name]
        observation['released_unique_planar_edges'] = len(own)
        observation['scope'] = 'Read-only unit own-allocation release; free vias; boundary access exempt; not a negotiated reroute'
        released[name] = observation
    grouped = []
    for names in groups:
        observation = residual_paths(release_allocations(cells, targets, names),
                                     len(xs)-1, len(ys)-1, targets)
        grouped.append({'released_targets': names, 'connectivity': observation,
                        'scope': 'Optimistic static unit-allocation release; free vias; boundary access exempt; not simultaneous route feasibility'})
    return {'original': original, 'one_target_released': released,
            'target_groups_released': grouped}


def planar_edges(segments):
    """Native positive-direction edge indices, once per net/layer edge."""
    edges = set()
    for x, y, layer, xx, yy, other in segments:
        if layer != other:
            continue
        if any((value-3600) % 7200 for value in (x,y,xx,yy)):
            raise ValueError('Segment is not on observed grid centers')
        a,b,aa,bb = ((value-3600)//7200 for value in (x,y,xx,yy))
        if y == yy:
            if layer not in ('Metal1', 'Metal3'):
                raise ValueError('Nonpreferred planar segment cannot be released')
            edges.update((layer, i, b) for i in range(min(a,aa),max(a,aa)))
        elif x == xx:
            if layer not in ('Metal2', 'Metal4'):
                raise ValueError('Nonpreferred planar segment cannot be released')
            edges.update((layer, a, j) for j in range(min(b,bb),max(b,bb)))
        else:
            raise ValueError('Diagonal planar segment')
    return edges


def residual_paths(cells, nx, ny, targets, box=(121440, 15120, 1241760, 684180)):
    """Static preferred-direction graph; DBU7200 grid, center offset3600."""
    def index(x, y):
        if (x-3600) % 7200 or (y-3600) % 7200:
            raise ValueError('Endpoint outside measured grid centers')
        return (x-3600)//7200, (y-3600)//7200

    def outside(point):
        x, y = (v*7200+3600 for v in point)
        return not (box[0] < x < box[2] and box[1] < y < box[3])

    def neighbors(point):
        x, y = point
        for xx, yy in ((x-1,y), (x+1,y), (x,y-1), (x,y+1)):
            if not (0 <= xx < nx and 0 <= yy < ny) or not outside((xx, yy)):
                continue
            layers = ('Metal1', 'Metal3') if y == yy else ('Metal2', 'Metal4')
            if any(cells.get((layer, min(x,xx), min(y,yy)), 0) > 0 for layer in layers):
                yield xx, yy

    result = {}
    for name, segments in targets.items():
        degree = Counter()
        for x,y,l,xx,yy,ll in segments:
            degree[x,y,l] += 1
            degree[xx,yy,ll] += 1
        terminals = sorted({index(x,y) for (x,y,l), count in degree.items() if count == 1})
        starts = [p for p in terminals if outside(p)]
        if not starts:
            raise ValueError('No shell terminal')
        # Macro snap points lie inside OBS. Model one outward boundary portal,
        # exempt only this pin-access step; it is not claimed physically legal.
        portals = []
        for x,y in terminals:
            if not outside((x,y)):
                direction = 1 if y*7200+3600 > (box[1]+box[3])/2 else -1
                yy = y
                while 0 <= yy < ny and not outside((x,yy)):
                    yy += direction
                portals.append((x, yy))
        distances = {starts[0]: 0}
        queue = deque([starts[0]])
        while queue:
            p = queue.popleft()
            for q in neighbors(p):
                if q not in distances:
                    distances[q] = distances[p]+1
                    queue.append(q)
        cut = []
        for x,y in distances:
            for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if not (0 <= xx < nx and 0 <= yy < ny) or not outside((xx,yy)) or (xx,yy) in distances:
                    continue
                layers = ('Metal1', 'Metal3') if y == yy else ('Metal2', 'Metal4')
                cut.append({'from': (x,y), 'to': (xx,yy), 'residual': {
                    layer: cells.get((layer,min(x,xx),min(y,yy)),0) for layer in layers}})
        result[name] = {'reachable_peripheral_centers': len(distances),
            'shell_terminals_reachable': [p in distances for p in starts],
            'macro_portals': [{'grid_index':p, 'reachable':p in distances,
                'static_path_dbu':distances[p]*7200 if p in distances else None} for p in portals],
            'saturated_cut_edges': sorted(cut, key=lambda item: (item['from'],item['to'])),
            'scope': 'Optimistic free-via static residual graph; own net usage retained; boundary pin-access step exempt'}
    return result


if __name__ == '__main__':
    main()
