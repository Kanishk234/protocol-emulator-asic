"""D098: distinguish southern pin-access failure from full-chip competition."""
import json
import os
from pathlib import Path
import sys

import cloud_route_trace as trace
from cloud_route_121_grid import EXPECTED_SEGMENTS, observed_trace, PATCH
from audit_native_grid import audit

CASES = {'control': None, 'pad31': ['cell_pad[31]'],
         'val30': ['cell_val[30]'], 'south_pair': ['cell_pad[31]', 'cell_val[30]']}


def isolation_trace(original, names):
    observed = observed_trace(original, PATCH.read_text())
    if names is None:
        return observed
    if names not in list(CASES.values()):
        raise ValueError('Unapproved reduced connection set')
    # Braced Tcl literals prevent [] substitution; all names are fixed above.
    selection = 'set warp_selected_nets {' + ' '.join(names) + '}\n'
    selection += ('foreach warp_name $warp_selected_nets {\n'
                  '    set warp_matches {}\n'
                  '    foreach warp_net [[ord::get_db_block] getNets] {\n'
                  '        set warp_normal [string map [list [format %c 92] {}] [$warp_net getName]]\n'
                  '        if {$warp_normal eq $warp_name} {lappend warp_matches $warp_net}\n'
                  '    }\n'
                  '    if {[llength $warp_matches] != 1} {error "Missing or ambiguous selected net"}\n'
                  '    log_cmd grt::add_net_to_route [lindex $warp_matches 0]\n'
                  '}\n')
    return selection + observed


def capacities(path):
    audit(path)
    rows = Path(path).read_text().splitlines()
    return rows[:3], {tuple(row.split('\t')[:4]): row.split('\t')[4] for row in rows[3:]}


def main():
    output = trace.ROOT / 'build/route_isolation'
    output.mkdir(exist_ok=False)
    results = {'diagnostic_completed': False, 'physical_acceptance': False, 'cases': {},
               'source_revision': os.environ.get('GITHUB_SHA'),
               'workflow_run': os.environ.get('GITHUB_RUN_ID'),
               'workflow_attempt': os.environ.get('GITHUB_RUN_ATTEMPT')}
    reference = None
    try:
        for name, names in CASES.items():
            trace.OUT = output / name
            trace.TARGETS = set(names) if names else {'cell_val[30]', 'cell_pad[27]', 'cell_pad[31]', 'cell_val[27]'}
            trace.main(15, worker=__file__, reduced_nets=names)
            result = json.loads((trace.OUT/'result.json').read_text())
            stage, = (trace.OUT/'replay').glob('*-openroad-globalrouting')
            grid = capacities(stage/'native-grid.tsv')
            if names is None:
                if result['segments_sha256'] != EXPECTED_SEGMENTS or result['native_congestion'][-1]['total_overflow'] != 121:
                    raise ValueError('Full control does not reproduce exact121')
                reference = grid
            result['capacity_arrays_identical_to_control'] = grid == reference
            result['selected_nets'] = names
            result['native_grid'] = audit(stage/'native-grid.tsv')
            for row in result['native_congestion'][:-1]:
                if result['native_grid']['layers'][row['layer']]['overflow'] != row['total_overflow']:
                    raise ValueError('Native grid and routing table overflow disagree')
            result['reduced_case_only'] = names is not None
            if names and result['native_net_count'] != len(names):
                raise ValueError('Reduced native route census differs')
            results['cases'][name] = result
            # Preserve changed pin-dependent capacity as a confound, never a controlled win.
        results['diagnostic_completed'] = True
    except Exception as exc:
        results['error'] = str(exc)
        raise
    finally:
        (output/'result.json').write_text(json.dumps(results, indent=2)+'\n')


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == '--inside':
        name = Path(sys.argv[2]).parent.name
        if name not in CASES:
            raise ValueError('Unknown isolation case')
        trace.TRACE = isolation_trace(trace.TRACE, CASES[name])
        trace.reports.instrument = trace.instrument
        trace.reports.inside(*(Path(p) for p in sys.argv[2:]))
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit('Unsupported isolation invocation')
