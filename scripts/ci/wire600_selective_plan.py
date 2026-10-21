"""Exact post-antenna wire600 identity-buffer proposal; no signoff authority."""
import hashlib
import json
from pathlib import Path
import re

from combined_physical_plan import connections, macro_pin, source_rows
from incremental_repair_audit import placements
from sram_bank_plan import MACRO_LEF_SHA

BINDING = json.loads((Path(__file__).parent / 'fixtures/wire600_selective/source.json').read_text())
PROTECTED = {'CLK', 'GCLK', 'GATE', 'RESET_B'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_files(root):
    root = Path(root)
    for item in BINDING['files'].values():
        if digest(root / item['path']) != item['sha256']:
            raise ValueError('Wrong selective electrical source: ' + item['path'])


def partition(terms, locations):
    drivers = [(n, p) for n, p in terms if p in {'X', 'Y', 'Q'} or p.startswith('A_DOUT[')]
    if len(drivers) != 1:
        raise ValueError('Expected one reviewed data driver')
    driver = drivers[0]
    sinks = [p for p in terms if p != driver]
    if not sinks or len(sinks) > 24 or any(p in PROTECTED for n, p in terms):
        raise ValueError('Protected or excessive electrical load set')
    if any(n == 'PIN' for n, p in terms):
        raise ValueError('Exposed net cannot be rewired')
    if driver[0] != 'u_chip.u_sram.sram' and not locations[driver[0]][0].startswith('sg13cmos5l_'):
        raise ValueError('Unreviewed driver master')
    sinks.sort(key=lambda p: (locations[p[0]][1], locations[p[0]][2], p))
    return driver, [sinks[i:i+4] for i in range(0, len(sinks), 4)]


def nearest_row(rows, target):
    candidates = []
    for x, y, orient, count, pitch in rows:
        index = max(0, min(count - 1, round((target[0] - x) / pitch)))
        px = x + index * pitch
        candidates.append((abs(px-target[0]) + abs(y-target[1]), px, y, orient))
    if not candidates:
        raise ValueError('No placement rows')
    _, x, y, orient = min(candidates)
    return [x, y, orient]


def power_anchor(terms, locations, driver):
    if driver[0] != 'u_chip.u_sram.sram':
        return driver[0]
    # Antenna cells need not have both ordinary VDD/VSS terminals. Use an
    # active standard-cell load, never a diode or the macro's VDD!/VSS! pins.
    candidates = sorted(n for n, p in terms if locations[n][0].startswith('sg13cmos5l_')
                        and locations[n][0] != 'sg13cmos5l_antennanp')
    if not candidates:
        raise ValueError('Missing active standard-cell power anchor')
    return candidates[0]


def plan(root, macro_lef):
    root = Path(root)
    validate_files(root)
    if digest(macro_lef) != MACRO_LEF_SHA:
        raise ValueError('Wrong SRAM geometry')
    files = BINDING['files']
    layout = (root / files['def']['path']).read_text()
    gates = json.loads((root / files['gates']['path']).read_text())
    if gates['qualified'] is not False or gates['estimated_setup_reserve_pass'] is not True:
        raise ValueError('Wrong failed electrical-only source')
    nets, attached = connections(layout, True)
    locations = placements(layout)
    rows = source_rows(layout)
    targets = {}
    for corner, data in gates['electrical'].items():
        for line in data['violations']['fanout']:
            pin = tuple(line.split()[0].rsplit('/', 1))
            net = attached[pin]
            if len(nets[net])-1 != int(line.split()[2]):
                raise ValueError('Final DEF disagrees with measured fanout')
            targets.setdefault(net, set()).add('fanout')
    for corner, data in gates['estimated_margin_offenders'].items():
        for kind in ('slew', 'capacitance'):
            for row in data[kind]:
                pin = tuple(row['pin'].rsplit('/', 1))
                if attached.get(pin) != row['net'] or not row['utilization'] > .45:
                    raise ValueError('Wrong electrical reserve target')
                targets.setdefault(row['net'], set()).add(kind)
    if not 1 <= len(targets) <= 48:
        raise ValueError('Unreviewed electrical source count')
    groups = []
    for net, reasons in sorted(targets.items()):
        driver, batches = partition(nets[net], locations)
        anchor = power_anchor(nets[net], locations, driver)
        target = (macro_pin(layout, Path(macro_lef), driver[1]) if driver[0] == 'u_chip.u_sram.sram'
                  else list(locations[driver[0]][1:3]))
        location = nearest_row(rows, target)
        for sinks in batches:
            name = f'tripwire_wire600_{len(groups)}'
            if name in locations or name+'_net' in nets:
                raise ValueError('Repeated electrical repair')
            groups.append(dict(buffer=name, net=name+'_net', source_net=net, rail_source=anchor,
                               master='sg13cmos5l_buf_4', sinks=sinks, location=location,
                               reasons=sorted(reasons)))
    if len(groups) > 96:
        raise ValueError('Electrical buffer budget exceeded')
    result = dict(source_run=BINDING['source_run'], def_sha256=files['def']['sha256'],
                groups=groups, target_count=len(targets), buffers=len(groups),
                source_targets={k: sorted(v) for k, v in sorted(targets.items())},
                legal_sites_verified=False, physical_timing_proven=False,
                qualified=False, route_authorized=False, clean_reproduction_required=True)
    validate_proposal(result)
    return result


def validate_proposal(proposal):
    if hashlib.sha256(json.dumps(proposal, sort_keys=True).encode()).hexdigest() != BINDING['proposal_sha256']:
        raise ValueError('Selective plan differs from reviewed canonical identity edits')


def target_call(layout, proposal):
    validate_proposal(proposal)
    if (hashlib.sha256(layout.encode()).hexdigest() != BINDING['files']['def']['sha256']
            or proposal['source_run'] != BINDING['source_run']
            or proposal['def_sha256'] != BINDING['files']['def']['sha256']):
        raise ValueError('Wrong selective Tcl source')
    nets, _ = connections(layout, True)
    loc = placements(layout)
    def word(value):
        if not re.fullmatch(r'[A-Za-z0-9_./\[\]-]+', value):
            raise ValueError('Unsafe Tcl identity')
        return '{' + value + '}'
    lines = []
    for net in dict.fromkeys(g['source_net'] for g in proposal['groups']):
        groups = [g for g in proposal['groups'] if g['source_net'] == net]
        terms = nets[net]
        expected = '{' + word(net) + ' {' + ' '.join(word(n+'/'+p) for n, p in terms) + '} {'
        expected += ' '.join('{'+word(n)+' '+word(loc[n][0])+'}' for n in sorted({n for n, p in terms})) + '}}'
        serialized = []
        for g in groups:
            values = ' '.join(word(g[k]) for k in ('buffer', 'net', 'source_net', 'rail_source'))
            sinks = ' '.join('{'+word(n)+' '+word(p)+'}' for n, p in g['sinks'])
            serialized.append('{'+values+' {'+' '.join(map(str, g['location']))+'} {'+sinks+'}}')
        lines.append('tripwire_electrical_repair {sg13cmos5l_buf_4} {'+expected+'} {'+' '.join(serialized)+'}')
    return '\n'.join(lines)+'\n'
