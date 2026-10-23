"""Independent, read-only audit of D112/D114 global-route leaf evidence.

Does not import the generator, physical policy or their acceptance checkers.
"""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

BASELINE = ('40013513454', '8d42ac1202864ac92c6488b75f34c0a63fcbaebf')
CRITICAL = ('40030916359', '00216eac8dcd14c03503afd17d303118a4d3440f')
REMAINING = ('40033384495', 'c6eba0161edf611270b563a434a06a8731da2cb9')
LEF_SHA = 'c47c436758ae87288324aa1f5a84fcc8faf813bf19df1a400b32258fff4e1219'
WIDTHS = (47520, 154080, 164640, 154080, 154080, 164640, 154080, 68640)
HEIGHTS = (56700, 185220, 185220, 185220, 56700)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(data, expected):
    require(str(data['id']) == expected[0] and data['head_sha'] == expected[1]
            and data['run_attempt'] == 1 and data['conclusion'] == 'success',
            'Incomplete or mismatched authenticated producer')


def guide_blocks(text):
    result = {}
    for name, body in re.findall(r'^([^\n]+)\n\(\n(.*?)\n\)', text, re.M | re.S):
        require(name not in result and body.strip(), 'Duplicate or empty guide net')
        rows = [line.split() for line in body.splitlines()]
        require(all(len(r) == 5 and r[4] in ('Metal2', 'Metal3', 'Metal4')
                    and int(r[0]) < int(r[2]) and int(r[1]) < int(r[3]) for r in rows),
                'Malformed or unsupported guide rectangles')
        result[name] = rows
    require(result, 'No route guides')
    return result


def wire_coverage(header, port_nets, guides):
    require(not header['cells'], 'Wire tile contains cells')
    inputs = {}
    for name, port in header['ports'].items():
        if port['direction'] == 'input':
            for i, bit in enumerate(port['bits']):
                inputs[bit] = name if len(port['bits']) == 1 else f'{name}[{i + port.get("offset", 0)}]'
    nets = []
    for name, port in header['ports'].items():
        if port['direction'] != 'output':
            continue
        for i, bit in enumerate(port['bits']):
            output = name if len(port['bits']) == 1 else f'{name}[{i + port.get("offset", 0)}]'
            require(bit in inputs, 'Nonidentity wire output')
            net = port_nets.get(output)
            require(net and port_nets.get(inputs[bit]) == net and net in guides,
                    'Wire pair lacks native connectivity or route guide')
            nets.append(net)
    require(len(nets) == len(set(nets)) == 52, 'Incomplete frozen wire coverage')
    return len(nets)


def power_geometry(boxes, x, height):
    groups = defaultdict(list)
    for box in boxes:
        if box['layer'] != 'Metal4':
            continue
        a, b, c, d = box['rect']
        require(0 <= a < c <= WIDTHS[x] and 0 <= b < d <= height and c - a == 2100,
                'Power rectangle bounds or width changed')
        require(box['net'] in ('VPWR', 'VGND'), 'Unexpected power net')
        offset = 0 if box['net'] == 'VPWR' else 4100
        center = Decimal(a + c) / 2 + sum(WIDTHS[:x])
        require((center - 12000 - offset) % 109920 == 0, 'Incorrect absolute column power phase')
        groups[box['net'], a, c].append((b, d))
    require({k[0] for k in groups} == {'VPWR', 'VGND'}
            and all((0, height) in spans for spans in groups.values()), 'Incomplete full-height power pins')


def areas(text):
    headers = list(re.finditer(r'^MACRO (\S+)$', text, re.M))
    result = {}
    for i, match in enumerate(headers):
        body = text[match.end():headers[i + 1].start() if i + 1 < len(headers) else len(text)]
        size = re.findall(r'^  SIZE ([0-9.]+) BY ([0-9.]+) ;', body, re.M)
        require(len(size) == 1, 'Ambiguous master geometry')
        result[match[1]] = Decimal(size[0][0]) * Decimal(size[0][1]) * 1000000
    return result


def audit(baseline, baseline_identity, critical, critical_identity, remaining, remaining_identity, lef):
    identity(json.loads(baseline_identity.read_text()), BASELINE)
    require(digest(lef) == LEF_SHA, 'Changed pinned LEF')
    master_area = areas(lef.read_text())
    manifest = json.loads((baseline / 'manifest.json').read_text())
    for name, expected in manifest['files'].items():
        require(digest(baseline / name) == expected, 'Changed prepared input: ' + name)
    fabric = json.loads((baseline / 'connections.json').read_text())['modules']['eFPGA']
    expected_contexts = set()
    for name, cell in fabric['cells'].items():
        x, y = map(int, re.fullmatch(r'Tile_X(\d+)Y(\d+)_.+', name).groups())
        expected_contexts.add((cell['type'], x, HEIGHTS[y]))
    require(len(fabric['cells']) == 40 and len(expected_contexts) == 26, 'Frozen context census changed')
    contexts = {}; wire_pairs = 0; exports = {}
    for root, api, expected, count in ((critical, critical_identity, CRITICAL, 5),
                                      (remaining, remaining_identity, REMAINING, 21)):
        identity(json.loads(api.read_text()), expected)
        prefix = 'r1-balanced-leaf-' if expected == CRITICAL else 'r1-balanced-remaining-'
        records = list(root.glob(prefix + expected[0] + '-*/native/result.json'))
        require(len(records) == count, 'Missing or duplicate campaign artifacts')
        for record in records:
            data = json.loads(record.read_text()); spec = data['balanced_case']
            require(data['passed'] and data['run'] == expected[0] and data['attempt'] == '1'
                    and not data['detailed_routing'] and not data['timing_acceptance'], 'Unqualified leaf outcome')
            require(data['input_manifest_sha256'] == digest(baseline / 'manifest.json'), 'Wrong input capsule')
            require(len(data['cases']) == 1, 'Unexpected case sweep')
            key, row = next(iter(data['cases'].items())); tile = data['tile']; x, y = spec['x'], spec['y']
            width, height = WIDTHS[x], HEIGHTS[y]; context = (tile, x, height)
            require(context in expected_contexts and context not in contexts, 'Wrong or repeated leaf context')
            require(row['passed'] and row['signal_pins'] == sum(len(p['bits']) for p in manifest['tiles'][tile]['ports'].values()), 'Missing routed signals')
            require(data['mapped_nl_sha256'] == manifest['files'][tile + '/tile.nl.v'], 'Changed original mapping')
            inventory = json.loads((record.parent / key / 'pins.json').read_text())
            bare_key = tile + '-width' + str(width / 1000).replace('.', '_')
            bare = critical / ('r1-balanced-interfaces-' + CRITICAL[0]) / 'native' / bare_key / 'pins.json'
            require(inventory == json.loads(bare.read_text()), 'Signal pin geometry or direction changed after placement')
            policy = row['policy']
            require(policy['DIE_AREA'] == [0, 0, width / 1000, height / 1000]
                    and policy['CLOCK_PERIOD'] == 20 and policy['CLOCK_PORT'] is None
                    and policy['PL_TARGET_DENSITY_PCT'] == 96 and policy['GRT_OVERFLOW_ITERS'] == 50
                    and policy['GRT_ADJUSTMENT'] == 0.3 and policy['RT_MIN_LAYER'] == 'Metal2'
                    and policy['RT_MAX_LAYER'] == 'Metal4' and policy['PL_ROUTABILITY_DRIVEN']
                    and not policy['PL_TIMING_DRIVEN'], 'Physical policy drift')
            original = Counter(manifest['tiles'][tile]['expected_cells']); actual = Counter(row['native_cells'])
            require(not (original - actual), 'Original mapped cells lost')
            for cell, n in (actual - original).items():
                require(cell == 'sg13cmos5l_buf_1' or (cell in ('sg13cmos5l_tiehi', 'sg13cmos5l_tielo') and n == 1), 'Unexpected physical cell')
            require(actual['sg13cmos5l_dlhq_1'] == original['sg13cmos5l_dlhq_1'], 'Configuration storage changed')
            require(sum(master_area[c] * n for c, n in actual.items()) == row['cell_area_dbu2'], 'Native area mismatch')
            require(row['power_terminals_checked'] == 2 * sum(actual.values()), 'Incomplete all-cell power binding census')
            require(not any(row['final_power_grid_violations'].values()) and row['congestion']
                    and all(c['total_overflow'] == c['max_h_overflow'] == c['max_v_overflow'] == 0 for c in row['congestion']), 'Native PG or overflow failure')
            power_geometry(row['power_pins'], x, height)
            folder = record.parent / key
            odb = list(folder.glob('*-openroad-globalrouting/*.odb'))
            require(len(odb) == 1 and digest(odb[0]) == row['odb_sha256'], 'Changed retained ODB')
            state_file = list(folder.glob('*-openroad-globalrouting/state_out.json'))
            require(len(state_file) == 1, 'Missing unique final native state')
            native_state = json.loads(state_file[0].read_text()); native_path = native_state['nl']
            if '/native/' in native_path:
                native_nl = record.parent / native_path.split('/native/', 1)[1]
                require(native_nl.resolve().is_relative_to(record.parent.resolve()), 'Native netlist escaped artifact')
            else:
                require(tile == 'NE_term' and native_path.endswith('/input/NE_term/tile.nl.v'), 'Unrecognized external native source')
                native_nl = baseline / tile / 'tile.nl.v'
            export = dict(path=str(native_nl.resolve()), sha256=digest(native_nl))
            require(tile not in exports or exports[tile]['sha256'] == export['sha256'],
                    'Native graph bytes differ between contexts; one shared module is unqualified')
            exports.setdefault(tile, export)
            if data.get('wire_only'):
                require(tile == 'NE_term' and not original and not actual and not data['placement_required'], 'Improper empty-tile exception')
                log = (folder / 'native-census.log').read_text()
                nets = {l.split('\t')[1]: l.split('\t')[2] for l in log.splitlines() if l.startswith('R1_PORT_NET\t')}
                guide = list(folder.glob('*-openroad-globalrouting/after_grt.guide'))
                require(len(guide) == 1 and row['metrics'].get('global_route__wirelength', 0) > 0, 'Missing actual wire route')
                header = json.loads((baseline / tile / 'header.json').read_text())['modules'][tile]
                wire_pairs += wire_coverage(header, nets, guide_blocks(guide[0].read_text()))
            else:
                require(actual and data.get('placement_required', True), 'Nonempty tile bypassed placement')
            contexts[context] = dict(case=spec['name'],utilization=row['metrics'].get('design__instance__utilization'),configuration_latches=actual['sg13cmos5l_dlhq_1'])
    require(set(contexts) == expected_contexts and wire_pairs == 52, 'Incomplete complete-layout leaf coverage')
    return dict(passed=True,leaf_contexts=len(contexts),grid_instances=40,prepared_hashes=len(manifest['files']),
                source_runs=dict(baseline=BASELINE[0],critical=CRITICAL[0],remaining=REMAINING[0]),
                wire_feedthroughs_with_guides=wire_pairs,scope='Global-route leaf evidence only; no whole-chip, detailed routing, management shell or timing acceptance.',
                native_exports=exports,cases=[contexts[k] for k in sorted(contexts)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','baseline-identity','critical','critical-identity','remaining','remaining-identity','lef','out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(); kwargs = vars(args); out = kwargs.pop('out')
    result = audit(**kwargs); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','native_exports')}))


if __name__ == '__main__':
    main()
