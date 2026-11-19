"""Read-only signal contact audit of finished R1 tiles; no geometry signoff."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import tempfile

from assembly_catalog import GRAPH_SHA, prepare as prepare_catalog, sha

NATIVE_SHA = '64922d92969e229e8562d9cc0c4bd1cb5add15766ec10709576f0255ebf2ce06'


class Union:
    def __init__(self):
        self.parent = {}

    def find(self, value):
        self.parent.setdefault(value, value)
        root = value
        while self.parent[root] != root:
            root = self.parent[root]
        while value != root:
            value, self.parent[value] = self.parent[value], root
        return root

    def join(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.parent[b] = a


def inventory(text):
    ports = {}; boxes = defaultdict(list)
    for line in text.splitlines():
        row = line.split('\t')
        if row[0] == 'PORT':
            if len(row) != 5 or row[1] in ports:
                raise ValueError('Malformed or duplicate physical port')
            ports[row[1]] = dict(net=row[2], direction=row[3], kind=row[4])
        elif row[0] == 'PBOX':
            if len(row) != 7:
                raise ValueError('Malformed physical port box')
            box = tuple(map(int, row[3:]))
            if box[0] >= box[2] or box[1] >= box[3]:
                raise ValueError('Empty physical port box')
            boxes[row[1]].append((row[2], box))
    if not ports or set(ports) != set(boxes):
        raise ValueError('Missing physical ports or pin boxes')
    return ports, dict(boxes)


def scalar_connections(cell):
    result = {}
    for name, bits in cell['connections'].items():
        # All frozen R1 bus ports have zero offset, descending indices.
        for i, bit in enumerate(bits):
            pin = name if len(bits) == 1 else f'{name}[{i}]'
            if type(bit) is not int or pin in result:
                raise ValueError('Unexpected constant or duplicate signal connection')
            result[pin] = bit
    return result


def audit(top, placements, views, modules):
    """Compare logical aliases to actual same-layer abutment contacts.

    Leaf internal connectivity is admitted from its passed final ODB inventory.
    This checks only signal pin boxes, not hidden metal, power, vias or DRC.
    """
    logical = Union(); physical = Union(); endpoints = {}; edges = defaultdict(list)
    for instance in placements:
        name = instance['instance']; case = instance['context']
        ports, boxes = views[case]
        connections = scalar_connections(top['cells'][name])
        module = modules[top['cells'][name]['type']]
        native = {}
        for pin, port in module['ports'].items():
            if pin in ('VPWR', 'VGND'):
                continue
            if port.get('offset', 0) != 0 or port.get('upto', 0) != 0:
                raise ValueError('Unexpected native port indexing')
            for i, bit in enumerate(port['bits']):
                native[pin if len(port['bits']) == 1 else f'{pin}[{i}]'] = bit
        signals = {p for p, v in ports.items() if v['kind'] not in ('POWER', 'GROUND')}
        if set(connections) != signals or set(connections) != set(native):
            raise ValueError('Physical signal ports differ from frozen logical graph')
        aliases = {}; native_aliases = {}; ox, oy = instance['origin_dbu']
        width, height = instance['size_dbu']
        for pin, bit in connections.items():
            key = (name, pin); endpoints[key] = bit; physical.find(key); logical.find(bit)
            native_net = native[pin]
            if type(native_net) is not int:
                raise ValueError('Unexpected native port constant')
            if native_net in native_aliases:
                logical.join(bit, connections[native_aliases[native_net]])
            else:
                native_aliases[native_net] = pin
            net = ports[pin]['net']
            if net in aliases:
                other = aliases[net]
                physical.join(key, (name, other))
            else:
                aliases[net] = pin
            for layer, (x0, y0, x1, y1) in boxes[pin]:
                if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
                    raise ValueError('Signal box outside its tile')
                for side, at, low, high in (
                    ('W', ox, oy+y0, oy+y1), ('E', ox+width, oy+y0, oy+y1),
                    ('S', oy, ox+x0, ox+x1), ('N', oy+height, ox+x0, ox+x1)):
                    if dict(W=x0 == 0, E=x1 == width, S=y0 == 0, N=y1 == height)[side]:
                        edges[(side, layer, at)].append((low, high, key))
    shorts = []; contacts = set()
    for (side, layer, at), spans in edges.items():
        if side not in ('E', 'N'):
            continue
        peers = edges.get(('W' if side == 'E' else 'S', layer, at), [])
        for lo, hi, a in spans:
            for plo, phi, b in peers:
                if a[0] != b[0] and min(hi, phi) > max(lo, plo):
                    pair = tuple(sorted((a, b)))
                    if pair in contacts:
                        continue
                    contacts.add(pair); physical.join(a, b)
                    if logical.find(endpoints[a]) != logical.find(endpoints[b]):
                        shorts.append(dict(pins=pair, layer=layer, coordinate_dbu=at))
    nets = defaultdict(list)
    for key, bit in endpoints.items():
        nets[logical.find(bit)].append(key)
    opens = []
    for bit, pins in nets.items():
        groups = defaultdict(list)
        for key in pins:
            groups[physical.find(key)].append(key)
        if len(groups) > 1:
            opens.append(dict(logical_bit=bit, components=list(groups.values())))
    return dict(passed=not shorts and not opens, signal_endpoints=len(endpoints),
        logical_signal_nets=len(nets), abutting_pin_pairs=len(contacts),
        short_count=len(shorts), open_net_count=len(opens), shorts=shorts, opens=opens,
        geometry_written=False, assembly_acceptance=False, timing_acceptance=False,
        scope='Final ODB signal pin-box/port-alias contact preflight only; no hidden-metal, power, via, GDS DRC/LVS, RC or clock/shell timing acceptance.')


def prepare(capsule, catalog, sources, native, out):
    capsule, catalog, sources, native, out = map(Path, (capsule, catalog, sources, native, out))
    graph = capsule/'mapped/input/connections.json'
    if sha(graph) != GRAPH_SHA or sha(native) != NATIVE_SHA:
        raise ValueError('Frozen physical/native graph changed')
    plan = json.loads(catalog.read_text()); roots = json.loads(sources.read_text())
    with tempfile.TemporaryDirectory(prefix='r1-contact-catalog-') as temp:
        fresh = Path(temp)/'catalog.json'
        prepare_catalog(capsule, fresh)
        if plan != json.loads(fresh.read_text()):
            raise ValueError('Assembly catalog differs from current qualified receipts')
    if (plan.get('preflight_passed') is not True or plan.get('leaf_contexts') != 26
            or plan.get('grid_instances') != 40 or set(roots) != set(plan['contexts'])):
        raise ValueError('Incomplete source catalog')
    inputs = [Path(__file__), graph, catalog, sources, native]; views = {}
    for case, row in plan['contexts'].items():
        root = Path(roots[case]); result = root/'result.json'
        final = json.loads(result.read_text())
        for key in ('passed', 'physical_gate_metrics', 'odb_sha256', 'gds_sha256', 'nl_sha256'):
            if final[key] != row[key]:
                raise ValueError('Finished source differs from admitted context')
        state = root/'run/27-checker-lvs/state_out.json'
        for key in ('odb', 'gds', 'nl'):
            name = json.loads(state.read_text())[key]
            if name.count('/build/leaf_finish/') != 1:
                raise ValueError('Unknown finished view location')
            path = root/name.split('/build/leaf_finish/', 1)[1]
            if sha(path) != row[key+'_sha256']:
                raise ValueError('Qualified finished view changed')
            inputs.append(path)
        text = root/'final.txt'; inputs.extend((result, state, text))
        views[case] = inventory(text.read_text())
    places = [dict(p, size_dbu=[plan['contexts'][p['context']]['width_dbu'],
                               plan['contexts'][p['context']]['height_dbu']])
              for p in plan['instances']]
    result = audit(json.loads(graph.read_text())['modules']['eFPGA'], places, views,
                   json.loads(native.read_text())['modules'])
    result['input_sha256'] = {str(p):sha(p) for p in inputs}
    if out.exists():
        raise ValueError('Refusing to overwrite a contact audit')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('capsule', 'catalog', 'sources', 'native', 'out'):
        p.add_argument('--'+name, type=Path, required=True)
    result = prepare(**vars(p.parse_args()))
    if not result['passed']:
        raise SystemExit('R1 signal contact preflight failed; see retained report')
