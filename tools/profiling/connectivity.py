"""Placed user-net locality census; no physical capacity or timing inference."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re


def analyze(document):
    modules = document.get('modules', {})
    if len(modules) != 1:
        raise ValueError('Expected exactly one flattened placed module')
    module = next(iter(modules.values()))
    nets = defaultdict(lambda: {'cells': set(), 'drivers': set(), 'sinks': set()})
    locations = {}
    for name, cell in module['cells'].items():
        bel = cell.get('attributes', {}).get('NEXTPNR_BEL', '')
        match = re.fullmatch(r'X([0-9]+)Y([0-9]+)/[^/]+', bel)
        if not match:
            raise ValueError('Missing/unsupported placed BEL: ' + name)
        locations[name] = tuple(map(int, match.groups()))
        for port, bits in cell['connections'].items():
            direction = cell['port_directions'].get(port)
            if direction not in ('input', 'output', 'inout'):
                raise ValueError('Missing/unsupported port direction')
            for index, bit in enumerate(bits):
                if isinstance(bit, str) and bit in ('0', '1', 'x', 'z'):
                    continue
                if type(bit) is not int or bit < 0:
                    raise ValueError('Invalid net bit')
                net = nets[bit]
                endpoint = (name, port, index)
                net['cells'].add(name)
                if direction in ('output', 'inout'):
                    net['drivers'].add(endpoint)
                if direction in ('input', 'inout'):
                    net['sinks'].add(endpoint)
    rows = []
    for bit, net in sorted(nets.items()):
        points = {locations[name] for name in net['cells']}
        xs, ys = zip(*points)
        groups = {}
        for width, height in ((1, 1), (2, 1), (1, 2), (2, 2)):
            groups[f'{width}x{height}'] = len({(x//width, y//height) for x, y in points})
        rows.append(dict(bit=bit, endpoint_cells=len(net['cells']), driver_pins=len(net['drivers']),
                         sink_pins=len(net['sinks']), distinct_tiles=len(points),
                         tile_bbox_span=max(xs)-min(xs)+max(ys)-min(ys),
                         cluster_groups=groups))
    return dict(placed_cells=len(locations), signal_bits=len(rows),
                multi_tile_bits=sum(r['distinct_tiles'] > 1 for r in rows),
                single_tile_bits=sum(r['distinct_tiles'] == 1 for r in rows),
                max_sink_pins=max((r['sink_pins'] for r in rows), default=0),
                aggregate_tile_bbox_span=sum(r['tile_bbox_span'] for r in rows),
                aggregate_cluster_groups_minus_one={key: sum(r['cluster_groups'][key]-1 for r in rows)
                                                    for key in ('1x1', '2x1', '1x2', '2x2')},
                nets=rows, physical_acceptance=False, timing_acceptance=False,
                scope='Existing placed user-net endpoint locality, including clock/reset/IO/primitives; tile-coordinate proxies, not routed lengths, switch demand, chip configuration wiring or physical capacity')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('placed_json', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    data = args.placed_json.read_bytes()
    result = analyze(json.loads(data))
    result['input_sha256'] = hashlib.sha256(data).hexdigest()
    with args.out.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')


if __name__ == '__main__':
    main()
