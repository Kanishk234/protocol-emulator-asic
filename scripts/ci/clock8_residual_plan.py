"""Exact routed-source repair proposals; topology checks are not physical closure."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from event_nor2_screen import logical_cells

NL_SHA = 'f9e558c27c0876d9a2f280130a618090732a36d2a272bc3b1989a7794b059b24'
DEF_SHA = 'a09a3856f46b2f7684b84e82fc0554174213d26318f70a75ea1b37e65973f218'
HOLD = (('_46984_', '_01546_', '_42227_', 'sg13cmos5l_nor2b_1'),
        ('_46597_', '_01159_', '_40391_', 'sg13cmos5l_nor2_1'))


def source(before, layout):
    if hashlib.sha256(before.encode()).hexdigest() != NL_SHA or hashlib.sha256(layout.encode()).hexdigest() != DEF_SHA:
        raise ValueError('Wrong reviewed clock8 routed source')
    cells = logical_cells(before)
    positions = {}
    for hit in re.finditer(r'^\s*- (\S+) (\S+)[^;]*\+ PLACED \( (\d+) (\d+) \) (?:N|FS)\b', layout, re.M):
        name, master = hit[1], hit[2]
        if name in cells and cells[name][0] == master:
            positions[name] = (int(hit[3]), int(hit[4]))
    return cells, positions


def attached(cells, net):
    return sorted((n, p) for n, (_, pins) in cells.items() for p, v in pins if v == net)


def plan(before, layout, kind):
    cells, positions = source(before, layout)
    groups = []
    if kind == 'antenna':
        driver, net = '_29457_', '_04467_'
        if cells.get(driver, (None,))[0] != 'sg13cmos5l_nand2_1' or dict(cells[driver][1]).get('Y') != net:
            raise ValueError('Wrong branch driver')
        sinks = [s for s in attached(cells, net) if s != (driver, 'Y')]
        if len(sinks) != 20 or sum(cells[n][0] == 'sg13cmos5l_antennanp' for n, p in sinks) != 12:
            raise ValueError('Wrong branch functional/antenna loads')
        if any(n not in positions for n, p in sinks) or driver not in positions:
            raise ValueError('Missing branch placements')
        origin = positions[driver]
        # Retain nearest six loads: six plus two new buffer inputs equals eight.
        ordered = sorted(sinks, key=lambda s: (sum(abs(positions[s[0]][j] - origin[j]) for j in range(2)), s))
        distal = ordered[6:]
        axis = max(range(2), key=lambda j: max(positions[n][j] for n, p in distal)-min(positions[n][j] for n, p in distal))
        distal.sort(key=lambda s: (positions[s[0]][axis], s))
        for i in range(2):
            selected = distal[i*7:(i+1)*7]
            groups.append(dict(buffer=f'tripwire_clock8_branch_{i}', net=f'tripwire_clock8_branch_net_{i}',
                source_net=net, rail_source=driver, sinks=selected,
                location=[sum(positions[n][j] for n, p in selected)//7 for j in range(2)]))
        upstream = 8
    elif kind == 'hold':
        for endpoint, net, driver, master in HOLD:
            if cells.get(endpoint, (None,))[0] != 'sg13cmos5l_dfrbpq_1' or dict(cells[endpoint][1]).get('D') != net:
                raise ValueError('Wrong hold endpoint')
            if cells.get(driver, (None,))[0] != master or dict(cells[driver][1]).get('Y') != net:
                raise ValueError('Wrong hold driver')
            if attached(cells, net) != sorted([(driver, 'Y'), (endpoint, 'D')]) or endpoint not in positions:
                raise ValueError('Hold source must have only the reviewed data sink')
            groups.append(dict(buffer=f'tripwire_clock8_hold_{endpoint}', net=f'tripwire_clock8_hold_net_{endpoint}',
                source_net=net, rail_source=endpoint, sinks=[(endpoint, 'D')], location=list(positions[endpoint])))
        upstream = 1
    else:
        raise ValueError('Unreviewed repair kind')
    master = 'sg13cmos5l_buf_4' if kind == 'antenna' else 'sg13cmos5l_buf_1'
    old_nets = {v for _, pins in cells.values() for _, v in pins}
    if any(g['buffer'] in cells or g['net'] in old_nets for g in groups):
        raise ValueError('Repeated repair names')
    return dict(source_run=38019338907, netlist_sha256=NL_SHA, def_sha256=DEF_SHA,
                kind=kind, buffer_master=master, groups=groups, added_buffers=2,
                upstream_sink_pins=upstream, downstream_sink_pins=[len(g['sinks']) for g in groups],
                retained_antenna_cells=True, legal_site_verified=False,
                physical_timing_measured=False, official_signoff=False)


def validate_change(before, layout, after, proposal):
    canonical = plan(before, layout, proposal['kind'])
    if json.loads(json.dumps(proposal)) != json.loads(json.dumps(canonical)):
        raise ValueError('Proposal differs from reviewed source partition')
    old, new = logical_cells(before), logical_cells(after)
    groups = canonical['groups']
    added = {g['buffer'] for g in groups}
    rewires = {(n, p): g['net'] for g in groups for n, p in g['sinks']}
    if set(new) != set(old) | added:
        raise ValueError('Expected exactly two identity buffers; preserve existing cells')
    for n, (master, pins) in old.items():
        if new[n] != (master, tuple(sorted((p, rewires.get((n, p), v)) for p, v in pins))):
            raise ValueError('Unexpected existing logic or wiring change')
    for g in groups:
        if new[g['buffer']] != (canonical['buffer_master'], tuple(sorted([('A', g['source_net']), ('X', g['net'])]))):
            raise ValueError('Wrong identity buffer function or wiring')
    return canonical


def target_call(before, layout, kind):
    proposal = plan(before, layout, kind)
    cells = logical_cells(before)
    def word(value):
        if not re.fullmatch(r'[A-Za-z0-9_./]+', value):
            raise ValueError('Unsafe residual Tcl identity')
        return '{' + value + '}'
    expectations = []
    for net in sorted({g['source_net'] for g in proposal['groups']}):
        terms = attached(cells, net)
        pins = ' '.join(word(n+'/'+p) for n, p in terms)
        masters = ' '.join('{' + word(n)+' '+word(cells[n][0])+'}' for n in sorted({n for n, p in terms}))
        expectations.append('{' + word(net)+' {'+pins+'} {'+masters+'}}')
    groups = []
    for g in proposal['groups']:
        sinks = ' '.join('{' + word(n)+' '+word(p)+'}' for n, p in g['sinks'])
        values = ' '.join(word(g[k]) for k in ('buffer','net','source_net','rail_source'))
        groups.append('{' + values+' {'+' '.join(map(str,g['location']))+'} {'+sinks+'}}')
    return 'tripwire_clock8_residual '+word(proposal['buffer_master'])+' {\n'+'\n'.join(expectations)+'\n} {\n'+'\n'.join(groups)+'\n}\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('netlist', type=Path)
    parser.add_argument('layout', type=Path)
    parser.add_argument('--kind', choices=['antenna', 'hold'], required=True)
    args = parser.parse_args()
    print(json.dumps(plan(args.netlist.read_text(), args.layout.read_text(), args.kind), indent=2))
