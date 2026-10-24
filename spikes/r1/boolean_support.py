"""Bounded binary feedback-support diagnostics, never a timing-arc waiver.

A cone replaces sequential outputs, module inputs and recursion/depth boundaries
with unconstrained binary variables. The own-feedback copies share those variables, except
one feedback value is 0 in one copy and 1 in the other. A stronger variant
compares all recursively encountered feedback cuts fixed at 0 against arbitrary
values, while sharing all other boundaries. An UNSAT difference
proves independence for this overapproximation of stable binary behavior only.
It says nothing about glitches, analog settling or delay through reconvergence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

SNAPSHOT_SHA = '0491a427285f53b27db8166c875d76536fe237c4e619277be297d8791ed94ba7'
TILE = 'Tile_X2Y3_LUT4x8_ha'
ROOTS = ['L'+letter+'_O' for letter in 'ABCDEFGH']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(plan):
    for path, digest in plan['input_sha256'].items():
        if sha(path) != digest:
            raise ValueError('Changed diagnostic input: '+path)


def cone(module, state, root, depth=64, limit=2048, all_feedback=False):
    if depth < 1 or limit < 1:
        raise ValueError('Positive cone bounds required')
    constants = {}
    for name, value in state.items():
        cell = module['cells'][name]
        if cell['type'] != 'sg13cmos5l_dlhq_1' or value not in ('0', '1'):
            raise ValueError('Unexpected configuration state or storage')
        bits = cell['connections']['Q']
        if len(bits) != 1 or bits[0] in constants:
            raise ValueError('Configuration output is not unique and scalar')
        constants[bits[0]] = value
    drivers = {}
    for name, cell in module['cells'].items():
        for pin, direction in cell['port_directions'].items():
            if direction not in ('input', 'output'):
                raise ValueError('Unsupported cell direction')
            if direction == 'output':
                for bit in cell['connections'][pin]:
                    if bit in drivers:
                        raise ValueError('Multiple output drivers')
                    drivers[bit] = (name, pin)
    nodes, cuts, wires, cache, reasons = [], {}, [], {}, {}

    def cut(bit, reason):
        if bit not in cuts:
            cuts[bit] = 'i'+str(len(cuts))
            reasons[bit] = reason
        return cuts[bit]

    def visit(bit, stack=()):
        if isinstance(bit, str):
            if bit not in ('0', '1'):
                raise ValueError('Nonbinary literal')
            return "1'b"+bit
        if bit in constants:
            return "1'b"+constants[bit]
        if bit in cache:
            return cache[bit]
        if bit not in drivers:
            return cut(bit, 'undriven_or_module_input')
        if bit in stack:
            return cut(bit, 'feedback')
        if len(stack) >= depth or len(wires) >= limit:
            return cut(bit, 'bound')
        name, output = drivers[bit]
        cell = module['cells'][name]
        if not re.fullmatch(r'sg13cmos5l_[a-z0-9]+_[1248]', cell['type']):
            raise ValueError('Unsupported native master')
        if re.search(r'_(?:df|dl)', cell['type']):
            return cut(bit, 'sequential_output')
        if sum(d == 'output' for d in cell['port_directions'].values()) != 1:
            raise ValueError('Only scalar single-output combinational cells supported')
        index = len(wires)
        wire = 'w'+str(index)
        wires.append(wire)
        inputs = {}
        for pin, bits in cell['connections'].items():
            if len(bits) != 1 or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', pin):
                raise ValueError('Only scalar native cell ports supported')
            if cell['port_directions'][pin] == 'input':
                inputs[pin] = visit(bits[0], stack+(bit,))
        ports = ['.'+pin+'('+value+')' for pin, value in inputs.items()]
        ports.append('.'+output+'('+wire+')')
        nodes.append(cell['type']+' g'+str(index)+' ('+','.join(ports)+');')
        cache[bit] = wire
        return wire

    root_bits = module['netnames'][root]['bits']
    if len(root_bits) != 1:
        raise ValueError('Non-scalar root')
    y = visit(root_bits[0])
    target = cuts.get(root_bits[0])
    if target is None:
        raise ValueError('Root feedback was not exposed; no feedback proof requested')
    text = 'module cone(input '+','.join(cuts.values())+', output y);\n'
    if wires:
        text += 'wire '+','.join(wires)+';\n'
    text += '\n'.join(nodes)+'\nassign y='+y+';\nendmodule\n'
    varying = {port for bit, port in cuts.items() if reasons[bit] == 'feedback'} if all_feedback else {target}
    shared = list(cuts.values()) if all_feedback else [value for value in cuts.values() if value != target]
    text += 'module miter('+('input '+','.join(shared)+', ' if shared else '')+'output diff);wire a,b;\n'
    for i, value in enumerate(('0', '1')):
        ports = []
        for pin in cuts.values():
            binding = ("1'b0" if i == 0 and pin in varying else pin) if all_feedback else (("1'b"+value) if pin == target else pin)
            ports.append('.'+pin+'('+binding+')')
        ports.append('.y('+('a' if i == 0 else 'b')+')')
        text += 'cone c'+str(i)+' ('+','.join(ports)+');\n'
    text += 'assign diff=a^b;endmodule\n'
    return text, dict(root=root, cells=len(nodes), cut_inputs=len(cuts), target=target,
                     cofactor='all_feedback' if all_feedback else 'own_feedback', varying_ports=sorted(varying),
                     cuts={str(bit): dict(port=port, reason=reasons[bit]) for bit, port in cuts.items()})


def prepare(timing, out):
    timing, out = Path(timing).resolve(), Path(out).resolve()
    plan = json.loads((timing/'plan.json').read_text())
    validate(plan)
    paths = [Path(p) for p in plan['input_sha256']]
    snapshot = next(p for p in paths if p.name == 'configuration-state.json')
    native = next(p for p in paths if p.name == 'LUT4x8_ha.nl.v')
    liberty = next(p for p in paths if p.suffix == '.lib')
    if sha(snapshot) != SNAPSHOT_SHA:
        raise ValueError('Changed authenticated primary configuration')
    out.mkdir(parents=True, exist_ok=False)
    bound = [Path(__file__).resolve(), timing/'plan.json', snapshot, native, liberty]
    if any(any(c in str(p) for c in '{}\n\r"') for p in bound+[out]):
        raise ValueError('Unsafe tool path')
    export = f'read_liberty -lib "{liberty}"\nread_verilog "{native}"\nwrite_json "{out}/native.json"\n'
    (out/'export.ys').write_text(export)
    data = dict(input_sha256={str(p): sha(p) for p in bound}, snapshot=str(snapshot), liberty=str(liberty),
                export_sha256=sha(out/'export.ys'), depth=64, limit=2048)
    (out/'plan.json').write_text(json.dumps(data, indent=2)+'\n')


def render(out):
    out = Path(out).resolve()
    plan = json.loads((out/'plan.json').read_text())
    validate(plan)
    if sha(out/'export.ys') != plan['export_sha256']:
        raise ValueError('Changed native conversion')
    module = json.loads((out/'native.json').read_text())['modules']['LUT4x8_ha']
    state = json.loads(Path(plan['snapshot']).read_text())['tiles'][TILE]
    if state['tile_type'] != 'LUT4x8_ha' or len(state['q']) != 438:
        raise ValueError('Changed tile configuration census')
    cases = {}
    for root in ROOTS:
        try:
            text, row = cone(module, state['q'], root, plan['depth'], plan['limit'])
        except ValueError as exc:
            if str(exc).startswith('Root feedback was not exposed'):
                cases[root] = dict(no_feedback_cut=True)
                continue
            raise
        (out/(root+'.v')).write_text(text)
        cases[root] = row
        text, row = cone(module, state['q'], root, plan['depth'], plan['limit'], all_feedback=True)
        name = root+'_all_feedback'
        (out/(name+'.v')).write_text(text)
        cases[name] = row
    # The negative control must produce a counterexample; identical copies must not.
    for name, expression in [('control_positive', 'f^f'), ('control_negative', 'f^!f')]:
        (out/(name+'.v')).write_text('module miter(input f, output diff);assign diff='+expression+';endmodule\n')
        cases[name] = dict(control=True)
    for name, row in cases.items():
        if row.get('no_feedback_cut'):
            continue
        script = f'read_liberty -ignore_miss_func "{plan["liberty"]}"\nread_verilog "{out/name}.v"\nhierarchy -check -top miter\nflatten\nopt\nsat -timeout 30 -prove diff 0 -show-inputs -show-outputs\n'
        (out/(name+'.ys')).write_text(script)
        row.update(verilog_sha256=sha(out/(name+'.v')), script_sha256=sha(out/(name+'.ys')))
    (out/'cases.json').write_text(json.dumps(dict(native_sha256=sha(out/'native.json'), cases=cases), indent=2)+'\n')


def audit(out):
    out = Path(out).resolve()
    before = (out/'cases.json').read_bytes()
    # Re-render source-bound cones and demand byte-identical recorded plans.
    # Check the existing artifacts before render can replace them.
    data = json.loads(before)
    for name, row in data['cases'].items():
        if not row.get('no_feedback_cut'):
            if sha(out/(name+'.v')) != row['verilog_sha256'] or sha(out/(name+'.ys')) != row['script_sha256']:
                raise ValueError('Changed cone or SAT policy')
    render(out)
    if before != (out/'cases.json').read_bytes():
        raise ValueError('Native JSON or generated cones changed')
    rows = {}
    for name, row in data['cases'].items():
        if row.get('no_feedback_cut'):
            rows[name] = row
            continue
        text = (out/(name+'.log')).read_text()
        matches = re.findall(r'^SAT proof finished - (no model found: SUCCESS!|model found: FAIL!)$', text, re.M)
        if len(matches) != 1 or re.search(r'ERROR:|TIMEOUT|timeout.*reached', text, re.I):
            raise ValueError('Incomplete SAT diagnostic: '+name)
        rows[name] = dict(independent=matches[0].startswith('no model'))
    if not rows['control_positive']['independent'] or rows['control_negative']['independent']:
        raise ValueError('SAT polarity controls failed')
    result = dict(diagnostic_complete=True, tile=TILE, cases=rows, timing_acceptance=False,
                  scope='Binary stable-behavior cone support only; arbitrary shared boundaries. No timing arc is disabled. No glitch, settling, extracted timing or physical acceptance.')
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--timing', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    for name in ('render', 'audit'):
        sub.add_parser(name).add_argument('--out', type=Path, required=True)
    args = vars(parser.parse_args())
    mode = args.pop('mode')
    dict(prepare=prepare, render=render, audit=audit)[mode](**args)
