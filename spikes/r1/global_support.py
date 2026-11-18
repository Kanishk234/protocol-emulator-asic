"""Cross-tile binary feedback diagnostics, not delay/hazard or timing waivers."""
import argparse
import json
from pathlib import Path
import re

from boolean_support import cone, sha

SNAPSHOT_SHA = '0491a427285f53b27db8166c875d76536fe237c4e619277be297d8791ed94ba7'
NATIVE_SHA = '64922d92969e229e8562d9cc0c4bd1cb5add15766ec10709576f0255ebf2ce06'
LIB_SHA = '3ee222c580ba33acb2131ac2bf224ff8ee9700751835b73aaec72b670bb31d3c'
TOP_SHA = 'acc67f9c76939a832ba2f70e08d5ecd0ae0a73172643945098c6c56c90506c45'
ROOTS = ['Tile_X2Y3_LUT4x8_ha/L'+letter+'_O' for letter in 'DEG']


def flatten(top, modules, snapshot):
    """Unify real port aliases before expanding native cells; retain every latch."""
    parent = {}
    def find(node):
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]
    def node(tile, bit):
        if isinstance(bit, str):
            if bit not in ('0', '1'):
                raise ValueError('Unknown literal in native graph')
            return ('constant', bit)
        return (tile, bit)
    def join(a, b):
        a, b = find(a), find(b)
        if a == b:
            return
        if a[0] == b[0] == 'constant':
            raise ValueError('Conflicting constant aliases')
        if b[0] == 'constant':
            a, b = b, a
        parent[b] = a
    if set(top['cells']) != set(snapshot):
        raise ValueError('Configuration tile population differs')
    for tile, instance in top['cells'].items():
        kind = instance['type']; module = modules[kind]
        extra = set(module['ports']) - set(instance['connections'])
        wire_power = (kind == 'NE_term' and not module['cells'] and
                      extra == {'VPWR', 'VGND'} and
                      all(module['ports'][p]['direction'] == 'inout' for p in extra))
        if (snapshot[tile]['tile_type'] != kind or
                set(instance['connections']) - set(module['ports']) or (extra and not wire_power)):
            raise ValueError('Native tile type/port mismatch')
        for pin, port in module['ports'].items():
            if pin in extra:
                continue
            outer = instance['connections'][pin]
            if len(outer) != len(port['bits']):
                raise ValueError('Native port width mismatch')
            for a, b in zip(port['bits'], outer):
                join(node(tile, a), node('top', b))
        for cell in module['cells'].values():
            if cell['type'] in ('sg13cmos5l_tiehi', 'sg13cmos5l_tielo'):
                outputs = [p for p, d in cell['port_directions'].items() if d == 'output']
                if len(outputs) != 1 or len(cell['connections'][outputs[0]]) != 1:
                    raise ValueError('Unexpected native tie-cell shape')
                join(node(tile, cell['connections'][outputs[0]][0]),
                     ('constant', '1' if cell['type'].endswith('tiehi') else '0'))
    numbers = {}
    def bit(tile, value):
        root = find(node(tile, value))
        if root[0] == 'constant':
            return root[1]
        if root not in numbers:
            numbers[root] = len(numbers)+2
        return numbers[root]
    combined = dict(cells={}, netnames={}, ports={}); state = {}
    for tile, instance in top['cells'].items():
        module = modules[instance['type']]
        q = snapshot[tile]['q']
        latches = {n for n, c in module['cells'].items() if c['type'] == 'sg13cmos5l_dlhq_1'}
        if set(q) != latches or any(v not in ('0', '1') for v in q.values()):
            raise ValueError('Configuration latch population/value mismatch')
        for name, cell in module['cells'].items():
            if cell['type'] in ('sg13cmos5l_tiehi', 'sg13cmos5l_tielo'):
                continue
            full = tile+'/'+name
            combined['cells'][full] = dict(type=cell['type'], port_directions=cell['port_directions'],
                connections={p:[bit(tile, b) for b in bits] for p, bits in cell['connections'].items()})
            if name in q:
                state[full] = q[name]
        for name, net in module['netnames'].items():
            combined['netnames'][tile+'/'+name] = dict(bits=[bit(tile, b) for b in net['bits']])
    for name, port in top['ports'].items():
        combined['ports'][name] = dict(direction=port['direction'], bits=[bit('top', b) for b in port['bits']])
    return combined, state


def prepare(capsule, native, out):
    capsule, native, out = (Path(p).resolve() for p in (capsule, native, out))
    snapshot = capsule/'functional/quiescent/configuration-state.json'
    top = capsule/'analysis/top.json'
    library = capsule/'pinned-pdk/sg13cmos5l_stdcell_slow_1p08V_125C.lib'
    if (sha(snapshot) != SNAPSHOT_SHA or sha(native) != NATIVE_SHA or
            sha(library) != LIB_SHA or sha(top) != TOP_SHA):
        raise ValueError('Require exact authenticated configuration/native/library views')
    top_graph = json.loads(top.read_text())['modules']['eFPGA']
    state = json.loads(snapshot.read_text())['tiles']
    if len(top_graph['cells']) != 40:
        raise ValueError('Frozen grid census changed')
    module, q = flatten(top_graph, json.loads(native.read_text())['modules'], state)
    if len(q) != 8736:
        raise ValueError('Frozen configuration census changed')
    out.mkdir(parents=True, exist_ok=False)
    (out/'flattened.json').write_text(json.dumps(module)+'\n')
    cases = {}
    for root in ROOTS:
        for strong in (False, True):
            name = root.split('/')[-1]+('_all_feedback' if strong else '_own_feedback')
            text, row = cone(module, q, root, depth=128, limit=8192, all_feedback=strong)
            (out/(name+'.v')).write_text(text); cases[name] = row
    for name in ('positive_control', 'negative_control'):
        if name == 'negative_control':
            text = 'module miter(input x, output diff);assign diff=x;endmodule\n'
        else:
            text = "module miter(output diff);assign diff=1'b0;endmodule\n"
        (out/(name+'.v')).write_text(text);cases[name] = dict(control=True)
    inputs = [Path(__file__), Path(__file__).with_name('boolean_support.py'), snapshot, top, native, library]
    for name in cases:
        source = out/(name+'.v');inputs.append(source)
        script = out/(name+'.ys')
        script.write_text(f'read_liberty -ignore_miss_func {json.dumps(str(library))}\n'
                          f'read_verilog {json.dumps(str(source))}\n'
                          'hierarchy -check -top miter\nflatten\nopt\n'
                          'sat -prove diff 0 -show-inputs\n')
        inputs.append(script)
    (out/'plan.json').write_text(json.dumps(dict(input_sha256={str(p):sha(p) for p in inputs},
        cases=cases, tiles=40, configuration_bits=8736, depth=128, cell_bound=8192,
        scope='Stable binary support across real tile connections only; no delay/hazard/settling proof or timing waiver.'), indent=2)+'\n')


def audit(out):
    out = Path(out).resolve();plan = json.loads((out/'plan.json').read_text())
    if any(sha(p) != digest for p, digest in plan['input_sha256'].items()):
        raise ValueError('Global support input changed')
    rows = {}
    for name in plan['cases']:
        text = (out/(name+'.log')).read_text()
        code = int((out/(name+'.exit')).read_text())
        passed = text.count('SAT proof finished - no model found: SUCCESS!') == 1
        failed = text.count('SAT proof finished - model found: FAIL!') == 1
        if code != 0 or passed == failed or re.search(r'^ERROR:', text, re.M):
            raise ValueError('Incomplete or ambiguous SAT diagnostic: '+name)
        rows[name] = dict(binary_support_proved=passed)
    if not rows['positive_control']['binary_support_proved'] or rows['negative_control']['binary_support_proved']:
        raise ValueError('SAT controls disagree')
    result = dict(diagnostic_complete=True, cases=rows, timing_acceptance=False,
                  physical_acceptance=False, scope=plan['scope'])
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__);sub = p.add_subparsers(dest='mode', required=True)
    prep = sub.add_parser('prepare')
    for name in ('capsule', 'native', 'out'):
        prep.add_argument('--'+name, type=Path, required=True)
    sub.add_parser('audit').add_argument('--out', type=Path, required=True)
    args = vars(p.parse_args()); mode = args.pop('mode')
    (prepare if mode == 'prepare' else audit)(**args)
