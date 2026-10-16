"""D099 custom-tool identity gate then bounded, same-process pair repair.

Hosted EDA only. Collection success is never physical acceptance.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import cloud_route_trace as trace
from cloud_route_121_grid import PATCH, EXPECTED_SEGMENTS, observed_trace
from cloud_route_isolation import capacities
from cloud_boundary_audit import SCRIPT as BOUNDARY_SCRIPT
from audit_native_grid import audit, guide_coverage, number

EXPECTED_GRID = '278fdd4a3e55eea60f586571bae98191e3a07623b2790aeb642e3a83d6c163ae'
MARKER = 'WARP_FORCE_REPAIR_BEGIN'
# Observer must reproduce the rejected capacity-corrected run38948702750.
REFERENCE_REPAIR = {
    'segments': '805a3f9af53c39e0ff179433ee9bfd98d8f91d179f3bb303d71248e259e8c90d',
    'interior': '6a648ef741a2bb9071f5bcd33c4eccd9dd0be8fe813770ba903f611ecc7b1c03',
    'boundary': '24a84793cd7507483da418601a676c21bb497c3c8ee8e321cf2f8ebbe16efc53',
}
SEEDS = {'cell_pad[31]', 'cell_val[30]'}
# IHP CMOS5L tech LEF at 2bbec755dc67ca3db0261c3d6163e15735d66710:
# sg13cmos5l_tech.lef SHA256 3edd5a1ad31e8307be537d0d1b85c3258fefeb21aac04aaa476e4f72de4cffd5.
BOUNDARY_DIRECTIONS = {'Metal1': 'H', 'Metal2': 'V', 'Metal3': 'H', 'Metal4': 'V'}


def grid_body(name):
    text = observed_trace(trace.TRACE, PATCH.read_text())
    start = text.index('set warp_grid [[ord::get_db_block] getGCellGrid]')
    stop = text.index('close $warp_grid_file', start) + len('close $warp_grid_file')
    return text[start:stop].replace('native-grid.tsv', name) + '\n'


def boundary_grid_body(name):
    """Real preferred edges omitted by the historical interior-grid format.

    Native OpenDB export duplicates H last-column/V last-row for display;
    export only actual H last-row and V last-column edges here.
    """
    return r'''
set warp_boundary_file [open $::env(STEP_DIR)/@NAME@ w]
puts $warp_boundary_file "META\t[llength $warp_x]\t[llength $warp_y]"
foreach warp_layer [[[ord::get_db] getTech] getLayers] {
    set warp_name [$warp_layer getName]
    if {$warp_name ni {Metal1 Metal2 Metal3 Metal4}} {continue}
    set warp_direction [$warp_layer getDirection]
    set warp_expected [dict get {Metal1 HORIZONTAL Metal2 VERTICAL Metal3 HORIZONTAL Metal4 VERTICAL} $warp_name]
    if {$warp_direction ne $warp_expected} {error "Boundary layer direction differs from pinned CMOS5L tech LEF"}
    if {$warp_direction eq "HORIZONTAL"} {
        set warp_yi [expr {[llength $warp_y]-1}]
        for {set warp_xi 0} {$warp_xi < [llength $warp_x]-1} {incr warp_xi} {
            puts $warp_boundary_file "EDGE\t$warp_name\tH\t$warp_xi\t$warp_yi\t[$warp_grid getCapacity $warp_layer $warp_xi $warp_yi]\t[$warp_grid getUsage $warp_layer $warp_xi $warp_yi]"
        }
    } else {
        set warp_xi [expr {[llength $warp_x]-1}]
        for {set warp_yi 0} {$warp_yi < [llength $warp_y]-1} {incr warp_yi} {
            puts $warp_boundary_file "EDGE\t$warp_name\tV\t$warp_xi\t$warp_yi\t[$warp_grid getCapacity $warp_layer $warp_xi $warp_yi]\t[$warp_grid getUsage $warp_layer $warp_xi $warp_yi]"
        }
    }
}
close $warp_boundary_file
'''.replace('@NAME@', name)


def audit_boundary_grid(path):
    rows = Path(path).read_text().splitlines()
    if not rows or not re.fullmatch(r'META\t[0-9]+\t[0-9]+', rows[0]):
        raise ValueError('Missing boundary grid dimensions')
    nx, ny = map(int, rows[0].split('\t')[1:])
    if min(nx, ny) < 2:
        raise ValueError('Degenerate boundary grid')
    expected = {(layer, direction, x, ny-1) for layer, direction in BOUNDARY_DIRECTIONS.items()
                if direction == 'H' for x in range(nx-1)}
    expected |= {(layer, direction, nx-1, y) for layer, direction in BOUNDARY_DIRECTIONS.items()
                 if direction == 'V' for y in range(ny-1)}
    seen, caps = set(), {}
    overflow = {layer: 0 for layer in BOUNDARY_DIRECTIONS}
    for line in rows[1:]:
        fields = line.split('\t')
        if len(fields) != 7 or fields[0] != 'EDGE' or not all(re.fullmatch(r'[0-9]+', v) for v in fields[3:5]):
            raise ValueError('Malformed or negative boundary edge')
        _, layer, direction, x, y, cap, usage = fields
        x, y = map(int, (x, y))
        cap, usage = number(cap), number(usage)
        if any(value != value.to_integral_value() for value in (cap, usage)):
            raise ValueError('Fractional boundary edge resource count')
        cap, usage = int(cap), int(usage)
        key = (layer, direction, x, y)
        if key not in expected or key in seen:
            raise ValueError('Duplicate or invalid real boundary edge')
        seen.add(key)
        caps[key] = cap
        overflow[layer] += max(0, usage-cap)
    if seen != expected:
        raise ValueError('Incomplete real boundary edge census')
    return {'dimensions': [nx, ny], 'observed_edges': len(seen), 'capacities': caps,
            'overflow_by_layer': overflow, 'total_overflow': sum(overflow.values()),
            'sha256': trace.cfg.sha(Path(path)),
            'scope': 'Native OpenDB real preferred boundary edges; excludes display sentinel duplicates'}


def geometry_body(name):
    start = BOUNDARY_SCRIPT.index('set block [ord::get_db_block]')
    stop = BOUNDARY_SCRIPT.index('close $out', start) + len('close $out')
    return (BOUNDARY_SCRIPT[start:stop].replace('$::env(WARP_GEOMETRY)',
            '$::env(STEP_DIR)/' + name) + '\n')


RESOLVE = r'''
set warp_handles {}
foreach warp_name {cell_pad[31] cell_val[30]} {
    set warp_matches {}
    foreach warp_net [[ord::get_db_block] getNets] {
        set warp_normal [string map [list [format %c 92] {}] [$warp_net getName]]
        if {$warp_normal eq $warp_name} {lappend warp_matches $warp_net}
    }
    if {[llength $warp_matches] != 1} {error "Missing or ambiguous force net"}
    lappend warp_handles [lindex $warp_matches 0]
}
'''
GUIDES = r'''
set warp_guides_file [open $::env(STEP_DIR)/native-guides.tsv w]
foreach warp_net [[ord::get_db_block] getNets] {
    puts $warp_guides_file "NET\t[$warp_net getName]\t[$warp_net getTermCount]\t[llength [$warp_net getGuides]]\t[$warp_net isConnectedByAbutment]"
}
close $warp_guides_file
'''


def force_trace(repair):
    if not isinstance(repair, bool):
        raise ValueError('Repair selection must be boolean')
    text = trace.cfg.CENSUS + r'''
set warp_route_code [catch {log_cmd global_route {*}$arg_list} warp_route_error warp_route_options]
if {$warp_route_code == 0 || ![string match {*GRT-0116*} $warp_route_error]} {
    error "Custom tool initial route did not reproduce failed control"
}
write_global_route_segments $::env(STEP_DIR)/initial-segments.txt
'''
    text += grid_body('initial-grid.tsv') + boundary_grid_body('initial-boundary-grid.tsv')
    # Hash gates execute inside the SAME process before any force call.
    for filename, expected in [('initial-segments.txt', EXPECTED_SEGMENTS), ('initial-grid.tsv', EXPECTED_GRID)]:
        text += ('if {[lindex [exec sha256sum $::env(STEP_DIR)/' + filename + '] 0] ne "' + expected +
                 '"} {error "Custom tool initial checkpoint hash mismatch"}\n')
    text += 'census $::env(STEP_DIR)/before-census.tsv\n' + geometry_body('before-geometry.tsv')
    text += r'''
set warp_initial [open $::env(STEP_DIR)/initial-return.txt w]
puts $warp_initial $warp_route_code
puts $warp_initial $warp_route_error
close $warp_initial
'''
    if repair:
        text += RESOLVE + 'puts "' + MARKER + '"\n'
        text += r'''
file mkdir $::env(STEP_DIR)/force-observer
if {[info exists ::env(WARP_FORCE_OBSERVER_DIR)]} {error "Unexpected inherited observer directory"}
set ::env(WARP_FORCE_OBSERVER_DIR) $::env(STEP_DIR)/force-observer
set warp_route_code [catch {log_cmd grt::force_reroute_pair {*}$warp_handles} warp_route_error warp_route_options]
unset ::env(WARP_FORCE_OBSERVER_DIR)
'''
    text += r'''
set warp_observer [open $::env(STEP_DIR)/native-return.txt w]
puts $warp_observer $warp_route_code
puts $warp_observer $warp_route_error
close $warp_observer
# Export diagnostic state even when repair exhausted; never waive native failure.
write_global_route_segments $::env(STEP_DIR)/native-segments.txt
'''
    text += grid_body('native-grid.tsv') + boundary_grid_body('native-boundary-grid.tsv') + GUIDES
    text += 'census $::env(STEP_DIR)/after-census.tsv\n' + geometry_body('after-geometry.tsv')
    text += 'if {$warp_route_code != 0} {return -options $warp_route_options $warp_route_error}\n'
    return text


def net_names(path):
    text = Path(path).read_text()
    trace.parse_segments(text)  # Validate every native segment first.
    lines = text.splitlines()
    return sorted(lines[i].replace('\\', '') for i in range(len(lines)-1) if lines[i+1] == '(')


def validate_stage(stage, repair):
    stage = Path(stage)
    if trace.cfg.sha(stage/'initial-segments.txt') != EXPECTED_SEGMENTS or trace.cfg.sha(stage/'initial-grid.tsv') != EXPECTED_GRID:
        raise ValueError('Initial exact121 checkpoint differs')
    before = audit(stage/'initial-grid.tsv')
    after = audit(stage/'native-grid.tsv')
    before_boundary = audit_boundary_grid(stage/'initial-boundary-grid.tsv')
    after_boundary = audit_boundary_grid(stage/'native-boundary-grid.tsv')
    if (before_boundary['dimensions'] != before['dimensions'] or
            after_boundary['dimensions'] != after['dimensions']):
        raise ValueError('Boundary/interior grid dimensions differ')
    if before_boundary['capacities'] != after_boundary['capacities']:
        raise ValueError('Force repair changes real boundary capacity arrays')
    if before['total_overflow'] != 121:
        raise ValueError('Initial grid is not121')
    if capacities(stage/'initial-grid.tsv') != capacities(stage/'native-grid.tsv'):
        raise ValueError('Force repair changes native capacity arrays')
    for kind in ('census', 'geometry'):
        if (stage/f'before-{kind}.tsv').read_bytes() != (stage/f'after-{kind}.tsv').read_bytes():
            raise ValueError('Force repair changes physical ' + kind)
    initial_names, final_names = net_names(stage/'initial-segments.txt'), net_names(stage/'native-segments.txt')
    if len(initial_names) != 3659 or initial_names != final_names:
        raise ValueError('Complete native net census changed')
    returned = (stage/'native-return.txt').read_text().splitlines()
    if len(returned) < 1 or returned[0] not in ('0', '1'):
        raise ValueError('Malformed native return')
    code = int(returned[0])
    if code and not any(error in '\n'.join(returned[1:]) for error in ('GRT-0116', 'GRT-0232')):
        raise ValueError('Unexpected native repair error')
    full_overflow = after['total_overflow'] + after_boundary['total_overflow']
    if not code and full_overflow != 0:
        raise ValueError('Native success contradicts grid overflow')
    coverage = guide_coverage(stage/'native-guides.tsv', (stage/'after-census.tsv').read_text())
    raw = (stage/'openroad-globalrouting.log').read_text()
    if repair:
        if raw.count(MARKER) != 1:
            raise ValueError('Missing or repeated repair marker')
        tail = raw.split(MARKER, 1)[1]
        try:
            table = trace.routing.parse_congestion(tail)
        except (ValueError, IndexError):
            table = None
        if table and table[-1]['total_overflow'] != full_overflow:
            raise ValueError('Final native table contradicts final grid')
        if table:
            for row in table[:-1]:
                if (after['layers'][row['layer']]['overflow'] +
                        after_boundary['overflow_by_layer'][row['layer']] != row['total_overflow']):
                    raise ValueError('Final native layer table contradicts final grid')
        if code == 0 and (not table or coverage['missing_guides']):
            raise ValueError('Passing route lacks final table or complete guides')
    else:
        table = trace.routing.parse_congestion(raw)
        if trace.cfg.sha(stage/'native-segments.txt') != EXPECTED_SEGMENTS or after['sha256'] != EXPECTED_GRID:
            raise ValueError('Custom default tool does not reproduce exact121')
        if before_boundary['sha256'] != after_boundary['sha256']:
            raise ValueError('Custom default changes boundary grid')
        if table[-1]['total_overflow'] != full_overflow:
            raise ValueError('Default native table contradicts interior plus boundary grid')
        for row in table[:-1]:
            if (after['layers'][row['layer']]['overflow'] +
                    after_boundary['overflow_by_layer'][row['layer']] != row['total_overflow']):
                raise ValueError('Default native layer table contradicts final grid')
    # Internal tuple-key capacity maps are compared above, not serialized.
    before_boundary.pop('capacities')
    after_boundary.pop('capacities')
    return {'initial_grid': before, 'final_grid': after,
            'initial_boundary_grid': before_boundary, 'final_boundary_grid': after_boundary,
            'final_observed_full_grid_overflow': full_overflow,
            'initial_segments_sha256': trace.cfg.sha(stage/'initial-segments.txt'),
            'final_segments_sha256': trace.cfg.sha(stage/'native-segments.txt'),
            'full_native_net_count': len(final_names),
            'physical_census_and_geometry_unchanged': True, 'capacities_unchanged': True,
            'capacity_identity_scope': 'OpenDB reporting capacities on canonical interior and real preferred boundary edges; native final table independently scans all raw H/V edges',
            'native_tcl_returncode': code, 'native_error': '\n'.join(returned[1:]),
            'final_table_available': bool(table), 'final_native_table': table,
            'guide_coverage': coverage, 'native_repair_passed': repair and code == 0 and full_overflow == 0,
            'physical_acceptance': False}


def grid_resources(path):
    """Strict semantic grid identity; numeric17 and17.0 are equivalent."""
    audit(path)
    rows = Path(path).read_text().splitlines()
    axes = tuple(tuple(map(int, row.split('\t')[1].split())) for row in rows[1:3])
    cells = {}
    for row in rows[3:]:
        _, layer, x, y, cap, usage = row.split('\t')
        cells[layer, int(x), int(y)] = (number(cap), number(usage))
    return axes, cells


def boundary_resources(path):
    audit_boundary_grid(path)
    cells = {}
    for row in Path(path).read_text().splitlines()[1:]:
        _, layer, direction, x, y, cap, usage = row.split('\t')
        cells[layer, direction, int(x), int(y)] = (number(cap), number(usage))
    return cells


def segment_map(path):
    text = Path(path).read_text()
    trace.parse_segments(text)
    lines, index, result = text.splitlines(), 0, {}
    while index < len(lines):
        name = lines[index].replace('\\', '')
        index += 2
        route = []
        while lines[index] != ')':
            x, y, layer, xx, yy, other = lines[index].split()
            route.append(tuple(sorted(((int(x), int(y), layer), (int(xx), int(yy), other)))))
            index += 1
        result[name] = tuple(sorted(route))
        index += 1
    return result


def parse_observer_names(path, pass_index, previous, complete_names):
    rows = Path(path).read_text().splitlines()
    if not rows or not re.fullmatch(r'META\t[0-9]+\t[0-9]+\t[0-9]+', rows[0]):
        raise ValueError('Malformed observer identity header')
    actual_pass, count, added = map(int, rows[0].split('\t')[1:])
    names, new_names, raw_names = set(), set(), []
    for line in rows[1:]:
        fields = line.split('\t')
        if len(fields) != 3 or fields[0] != 'NET' or fields[2] not in ('0', '1') or not fields[1]:
            raise ValueError('Malformed observer identity row')
        raw, new = fields[1], fields[2] == '1'
        name = raw.replace('\\', '')
        if name in names or name not in complete_names or new != (name not in previous):
            raise ValueError('Observer duplicate/unknown identity or new-name contradiction')
        names.add(name); raw_names.append(raw)
        if new:
            new_names.add(name)
    if (actual_pass != pass_index or count != len(names) or added != len(new_names) or
            raw_names != sorted(raw_names) or not previous <= names or not SEEDS <= names):
        raise ValueError('Observer identity count/order/pass/expansion contradiction')
    if pass_index == 0 and names != SEEDS:
        raise ValueError('Observer first pass is not the selected pair')
    return names, new_names


def validate_observer(stage, validated_stage):
    """Interpret per-pass evidence only after exact failed132 route equivalence."""
    stage = Path(stage)
    expected_files = {'segments': 'native-segments.txt', 'interior': 'native-grid.tsv',
                      'boundary': 'native-boundary-grid.tsv'}
    if any(trace.cfg.sha(stage/name) != REFERENCE_REPAIR[key] for key, name in expected_files.items()):
        raise ValueError('Observer changes measured132 final route/grid hashes')
    normal_missing = {name.replace('\\', '') for name in validated_stage['guide_coverage']['missing_guides']}
    if (validated_stage['native_tcl_returncode'] != 1 or 'GRT-0232' not in validated_stage['native_error'] or
            validated_stage['final_observed_full_grid_overflow'] != 132 or
            validated_stage['final_boundary_grid']['total_overflow'] != 0 or
            validated_stage['guide_coverage']['required_net_count'] != 3691 or normal_missing != SEEDS):
        raise ValueError('Observer no longer reproduces failed132 outcome/coverage')
    expected_layers = {'Metal1': 15, 'Metal2': 52, 'Metal3': 24, 'Metal4': 41}
    if {name: row['overflow'] for name, row in validated_stage['final_grid']['layers'].items()} != expected_layers:
        raise ValueError('Observer final132 layer accounting differs')
    directory = stage/'force-observer'
    expected = {f'pass_{i}.{suffix}' for i in range(5)
                for suffix in ('nets.tsv', 'native-grid.tsv', 'boundary-native-grid.tsv', 'segments.txt')}
    if (not directory.is_dir() or any(p.is_symlink() or not p.is_file() for p in directory.iterdir()) or
            {p.name for p in directory.iterdir()} != expected):
        raise ValueError('Observer snapshot files are incomplete/extra/linked')
    raw = (stage/'openroad-globalrouting.log').read_text()
    witnesses = re.findall(r'^WARP_FORCE_OBSERVER pass=(\d+) nets=(\d+) added=(\d+) segment_bytes=(\d+) interior_grid=true boundary_preferred=true prefix=(.+)$', raw, re.M)
    if [int(row[0]) for row in witnesses] != list(range(5)):
        raise ValueError('Missing/repeated/out-of-order native observer witnesses')
    complete = set(net_names(stage/'initial-segments.txt'))
    before_axes, before_cells = grid_resources(stage/'initial-grid.tsv')
    before_caps = {edge: value[0] for edge, value in before_cells.items()}
    before_boundary = audit_boundary_grid(stage/'initial-boundary-grid.tsv')
    previous, observations = set(), []
    for index, witness in enumerate(witnesses):
        paths = {kind: directory/f'pass_{index}.{suffix}' for kind, suffix in
                 [('names', 'nets.tsv'), ('interior', 'native-grid.tsv'),
                  ('boundary', 'boundary-native-grid.tsv'), ('segments', 'segments.txt')]}
        names, added = parse_observer_names(paths['names'], index, previous, complete)
        if (len(names) != int(witness[1]) or len(added) != int(witness[2]) or
                paths['segments'].stat().st_size != int(witness[3]) or
                not witness[4].endswith('/force-observer/pass_'+str(index))):
            raise ValueError('Native observer witness contradicts retained snapshot bytes/identity')
        # Parse all retained bytes, not merely native write/open success or names header count.
        if set(net_names(paths['segments'])) != complete or len(complete) != 3659:
            raise ValueError('Observer pass loses complete3659-net census')
        interior = audit(paths['interior'])
        boundary = audit_boundary_grid(paths['boundary'])
        axes, cells = grid_resources(paths['interior'])
        if (axes != before_axes or {edge: value[0] for edge, value in cells.items()} != before_caps or
                boundary['capacities'] != before_boundary['capacities'] or
                interior['dimensions'] != before_boundary['dimensions'] or
                boundary['dimensions'] != before_boundary['dimensions']):
            raise ValueError('Observer pass changes actual capacity arrays/grid geometry')
        boundary.pop('capacities')
        observations.append({'pass': index, 'actual_native_pass_net_count': len(names),
            'newly_added_net_count': len(added), 'net_names': sorted(names), 'new_net_names': sorted(added),
            'interior_grid': interior, 'preferred_boundary_grid': boundary,
            'observed_full_grid_overflow': interior['total_overflow']+boundary['total_overflow'],
            'files_sha256': {kind: trace.cfg.sha(path) for kind, path in paths.items()}})
        previous = names
    for kind, filename in expected_files.items():
        snapshot = directory/('pass_4.'+{'segments': 'segments.txt', 'interior': 'native-grid.tsv',
                                      'boundary': 'boundary-native-grid.tsv'}[kind])
        parser = {'segments': segment_map, 'interior': grid_resources, 'boundary': boundary_resources}[kind]
        if parser(snapshot) != parser(stage/filename):
            raise ValueError('Last observer snapshot differs from final native export')
    return {'reference_run': 38948702750, 'observer_equivalence_verified': True,
            'final_observed_full_grid_overflow': 132, 'passes': observations,
            'physical_acceptance': False, 'routing_improvement': False,
            'scope': 'Identical rejected132 route; per-pass complete reporting-grid and merged-segment observation'}


def docker_options(binary):
    path = Path(binary)
    if not re.fullmatch(r'/nix/store/[a-z0-9]{32}-[^/]+/bin/openroad', str(path)) or not path.is_file():
        raise ValueError('Expected existing exact Nix-store OpenROAD executable')
    root = str(path.parent.parent)
    closure = subprocess.run(['nix-store', '--query', '--requisites', root],
                             check=True, capture_output=True, text=True, timeout=30).stdout.splitlines()
    if not closure or root not in closure or len(set(closure)) != len(closure):
        raise ValueError('Incomplete or duplicated custom tool runtime closure')
    options = []
    for member in sorted(closure):
        if not re.fullmatch(r'/nix/store/[a-z0-9]{32}-[A-Za-z0-9+._=-]+', member) or not Path(member).exists():
            raise ValueError('Invalid or missing runtime store path')
        options.extend(('-v', member + ':' + member + ':ro'))
    # Mount individual outputs; mounting the store root hides container Python.
    options.extend(('-e', '_LLN_OVERRIDE_OPENROAD=' + str(path)))
    return tuple(options)


def main():
    binary = os.environ['WARP_FORCE_OPENROAD']
    options = docker_options(binary)
    output = trace.ROOT/'build/route_force_repair'
    output.mkdir(exist_ok=False)
    result = {'diagnostic_completed': False, 'physical_acceptance': False, 'cases': {},
              'custom_binary': binary, 'custom_binary_sha256': trace.cfg.sha(Path(binary)),
              'patch_sha256': trace.cfg.sha(trace.ROOT/'patches/openroad_force_reroute.patch'),
              'source_revision': os.environ.get('GITHUB_SHA'), 'workflow_run': os.environ.get('GITHUB_RUN_ID'),
              'workflow_attempt': os.environ.get('GITHUB_RUN_ATTEMPT')}
    try:
        command = ['docker', 'run', '--rm', *options, '--entrypoint', 'python3', trace.cfg.IMAGE,
                   '-c', 'import librelane,os,subprocess,sys; print(sys.version); subprocess.run([os.environ["_LLN_OVERRIDE_OPENROAD"],"-version"],check=True)']
        with (output/'runtime-smoke.log').open('w') as log:
            subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=60)
        for name, repair in [('default_identity', False), ('forced_pair', True)]:
            trace.OUT = output/name
            trace.main(15, worker=__file__, docker_args=options,
                       native_error_codes=('GRT-0116', 'GRT-0232') if repair else ('GRT-0116',),
                       repair_observation=repair)
            stage, = (trace.OUT/'replay').glob('*-openroad-globalrouting')
            result['cases'][name] = validate_stage(stage, repair)
            if repair:
                result['cases'][name]['observer'] = validate_observer(stage, result['cases'][name])
            # The next case starts only after full custom-default identity passed.
        result['diagnostic_completed'] = True
    except Exception as exc:
        result['error'] = str(exc)
        # A rejected invariant must not hide the actual native failure evidence.
        # These observations remain explicitly unqualified, never a passed case.
        observations = {}
        for name in ('default_identity', 'forced_pair'):
            stages = list((output/name/'replay').glob('*-openroad-globalrouting'))
            if len(stages) != 1:
                continue
            stage = stages[0]
            observed = {'physical_acceptance': False, 'validated': False}
            try:
                observed['native_grid'] = audit(stage/'native-grid.tsv', allow_negative_usage=True)
                observed['native_return'] = (stage/'native-return.txt').read_text()
            except (OSError, ValueError) as evidence_error:
                observed['evidence_error'] = str(evidence_error)
            observations[name] = observed
        result['unvalidated_observations'] = observations
        raise
    finally:
        (output/'result.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == '--inside':
        case = Path(sys.argv[2]).parent.name
        if case not in ('default_identity', 'forced_pair'):
            raise ValueError('Unknown force repair stage')
        trace.TRACE = force_trace(case == 'forced_pair')
        trace.reports.instrument = trace.instrument
        trace.reports.inside(*(Path(p) for p in sys.argv[2:]))
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit('Unsupported force repair invocation')
