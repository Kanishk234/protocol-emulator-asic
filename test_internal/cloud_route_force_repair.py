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
from audit_native_grid import audit, guide_coverage

EXPECTED_GRID = '278fdd4a3e55eea60f586571bae98191e3a07623b2790aeb642e3a83d6c163ae'
MARKER = 'WARP_FORCE_REPAIR_BEGIN'


def grid_body(name):
    text = observed_trace(trace.TRACE, PATCH.read_text())
    start = text.index('set warp_grid [[ord::get_db_block] getGCellGrid]')
    stop = text.index('close $warp_grid_file', start) + len('close $warp_grid_file')
    return text[start:stop].replace('native-grid.tsv', name) + '\n'


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
    text += grid_body('initial-grid.tsv')
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
set warp_route_code [catch {log_cmd grt::force_reroute_pair {*}$warp_handles} warp_route_error warp_route_options]
'''
    text += r'''
set warp_observer [open $::env(STEP_DIR)/native-return.txt w]
puts $warp_observer $warp_route_code
puts $warp_observer $warp_route_error
close $warp_observer
# Export diagnostic state even when repair exhausted; never waive native failure.
write_global_route_segments $::env(STEP_DIR)/native-segments.txt
'''
    text += grid_body('native-grid.tsv') + GUIDES
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
    if not code and after['total_overflow'] != 0:
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
        if table and table[-1]['total_overflow'] != after['total_overflow']:
            raise ValueError('Final native table contradicts final grid')
        if table:
            for row in table[:-1]:
                if after['layers'][row['layer']]['overflow'] != row['total_overflow']:
                    raise ValueError('Final native layer table contradicts final grid')
        if code == 0 and (not table or coverage['missing_guides']):
            raise ValueError('Passing route lacks final table or complete guides')
    else:
        table = trace.routing.parse_congestion(raw)
        if trace.cfg.sha(stage/'native-segments.txt') != EXPECTED_SEGMENTS or after['sha256'] != EXPECTED_GRID:
            raise ValueError('Custom default tool does not reproduce exact121')
    return {'initial_grid': before, 'final_grid': after,
            'initial_segments_sha256': trace.cfg.sha(stage/'initial-segments.txt'),
            'final_segments_sha256': trace.cfg.sha(stage/'native-segments.txt'),
            'full_native_net_count': len(final_names),
            'physical_census_and_geometry_unchanged': True, 'capacities_unchanged': True,
            'native_tcl_returncode': code, 'native_error': '\n'.join(returned[1:]),
            'final_table_available': bool(table), 'final_native_table': table,
            'guide_coverage': coverage, 'native_repair_passed': repair and code == 0 and after['total_overflow'] == 0,
            'physical_acceptance': False}


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
            # The next case starts only after full custom-default identity passed.
        result['diagnostic_completed'] = True
    except Exception as exc:
        result['error'] = str(exc)
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
