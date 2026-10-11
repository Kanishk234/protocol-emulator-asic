"""Read-only dominant-net partitions; repin extracted geometry before physical use."""
import hashlib
import re
from event_nor2_screen import logical_cells

NL_SHA = '1da984a3d76325e06e39de478f8d8cf4c24d812970df97dff72f5ee9f1244cfe'
DEF_SHA = '7a6172759a31a18f20c1ae2b3fd17cce4bd699c3ae18d06ece0f0b887e8fab87'
TARGETS = {
    '_28807_': ('sg13cmos5l_nand3_1', '_03831_', 16, 8),
    '_28820_': ('sg13cmos5l_nor2_1', '_03844_', 13, 6),
}


def plan(before, layout, driver):
    if (hashlib.sha256(before.encode()).hexdigest() != NL_SHA
            or hashlib.sha256(layout.encode()).hexdigest() != DEF_SHA):
        raise ValueError('Wrong reviewed extracted geometry')
    if driver not in TARGETS:
        raise ValueError('Unreviewed dominant slew target')
    cells = logical_cells(before)
    master, net, count, diodes = TARGETS[driver]
    if cells.get(driver, (None,))[0] != master or dict(cells[driver][1]).get('Y') != net:
        raise ValueError('Wrong dominant driver')
    sinks = sorted((n, p) for n, (_, pins) in cells.items()
                   for p, v in pins if v == net and (n, p) != (driver, 'Y'))
    if (len(sinks) != count
            or sum(cells[n][0] == 'sg13cmos5l_antennanp' for n, p in sinks) != diodes
            or any(p in ('CLK', 'GCLK', 'GATE', 'RESET_B', 'Y', 'X', 'Q') for n, p in sinks)):
        raise ValueError('Wrong data/diode load set')
    positions = {}
    for n, p in sinks:
        hit = re.search(r'^\s*- ' + re.escape(n) + r' ' + re.escape(cells[n][0])
                        + r'[^;]*\+ PLACED \( (\d+) (\d+) \) (N|FS)\b', layout, re.M)
        if not hit:
            raise ValueError('Missing reviewed sink placement')
        positions[n] = (int(hit[1]), int(hit[2]))
    axis = max(range(2), key=lambda j: max(v[j] for v in positions.values())
               - min(v[j] for v in positions.values()))
    ordered = sorted(sinks, key=lambda s: (positions[s[0]][axis], s))
    groups = []
    for i in range(0, len(ordered), 4):
        selected = ordered[i:i+4]
        name = f'tripwire_dominant_{driver}_{i//4}'
        groups.append(dict(buffer=name, net=name+'_net', sinks=selected,
                           source_net=net, centroid_dbu=[sum(positions[n][j] for n, p in selected)
                                                        // len(selected) for j in range(2)]))
    if len(groups) > 4:
        raise ValueError('Upstream load reserve exceeded')
    if any(g['buffer'] in cells or g['net'] in {v for _, pins in cells.values() for p, v in pins}
           for g in groups):
        raise ValueError('Proposed buffer or net name collision')
    return dict(source_run=38112320460, netlist_sha256=NL_SHA, def_sha256=DEF_SHA,
                driver=driver, groups=groups, added_buffers=len(groups),
                legal_site_verified=False, physical_timing_measured=False,
                physical_screen_only=True, official_signoff=False)


def validate_change(before, layout, after, proposal):
    canonical = plan(before, layout, proposal['driver'])
    if canonical != proposal:
        raise ValueError('Unreviewed partition proposal')
    expected = logical_cells(before)
    rewires = {(n, p):g['net'] for g in canonical['groups'] for n, p in g['sinks']}
    for n, (master, pins) in list(expected.items()):
        expected[n] = (master, tuple(sorted((p, rewires.get((n, p), v)) for p, v in pins)))
    for g in canonical['groups']:
        expected[g['buffer']] = ('sg13cmos5l_buf_4', tuple(sorted([('A', g['source_net']), ('X', g['net'])])))
    if logical_cells(after) != expected:
        raise ValueError('Partition must preserve all original cells and every sink/diode')
    return canonical


def target_call(before, layout, driver):
    """Use existing guarded residual binding; caller must legalize and qualify."""
    proposal = plan(before, layout, driver)
    cells = logical_cells(before)
    groups = proposal['groups']
    net = groups[0]['source_net']
    sinks = sorted(s for g in groups for s in g['sinks'])
    tokens = [driver, net] + [v for n, p in sinks for v in (n, p, cells[n][0])]
    tokens += [v for g in groups for v in (g['buffer'], g['net'])]
    if any(not re.fullmatch(r'[A-Za-z0-9_]+', value) for value in tokens):
        raise ValueError('Unsupported Tcl target token')
    pins = ' '.join([driver+'/Y'] + [n+'/'+p for n, p in sinks])
    masters = ' '.join('{'+n+' '+cells[n][0]+'}' for n in sorted({driver} | {n for n, p in sinks}))
    expectation = '{'+net+' {'+pins+'} {'+masters+'}}'
    entries = []
    for g in groups:
        entries.append('{'+g['buffer']+' '+g['net']+' '+net+' '+driver
                       +' {'+' '.join(str(v) for v in g['centroid_dbu'])+'} {'
                       +' '.join('{'+n+' '+p+'}' for n, p in g['sinks'])+'}}')
    return ('tripwire_clock8_residual sg13cmos5l_buf_4 {'+expectation+'} {'
            +' '.join(entries)+'}\n')
