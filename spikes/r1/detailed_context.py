"""Detailed-route a frozen R1 context from the authenticated original capsule."""
import argparse
import json
from pathlib import Path
import re

from detailed_leaf import OBSERVER, check_inventories, sha

PRODUCERS = {'40030916359', '40033384495'}
SCOPE = ('Frozen leaf routing only; no placement/netlist change, foundry signoff, '
         'LVS, extracted timing or assembled macro acceptance.')


def prepare(capsule, case, out):
    capsule, out = Path(capsule).resolve(), Path(out).resolve()
    if not re.fullmatch(r'[a-z][a-z0-9_]*', case):
        raise ValueError('Invalid context name')
    matches = []
    for record in (capsule / 'leaves').glob('*/native/result.json'):
        data = json.loads(record.read_text())
        if data.get('balanced_case', {}).get('name') == case:
            matches.append((record, data))
    if len(matches) != 1:
        raise ValueError('Require one frozen context')
    record, data = matches[0]
    if (not data['passed'] or data['run'] not in PRODUCERS or data['attempt'] != '1'
            or data['detailed_routing'] or data['timing_acceptance'] or len(data['cases']) != 1):
        raise ValueError('Unqualified global-route source')
    key, row = next(iter(data['cases'].items()))
    if (not row['passed'] or not row['congestion'] or
            any(any(c[k] for k in ('total_overflow', 'max_h_overflow', 'max_v_overflow'))
                for c in row['congestion']) or any(row['final_power_grid_violations'].values())):
        raise ValueError('Source overflow or power failure')
    folder = record.parent / key
    odbs = list(folder.glob('*-openroad-globalrouting/*.odb'))
    guides = list(folder.glob('*-openroad-globalrouting/after_grt.guide'))
    if len(odbs) != 1 or len(guides) != 1 or sha(odbs[0]) != row['odb_sha256']:
        raise ValueError('Missing or changed frozen routing input')
    cells = sum(row['native_cells'].values())
    expected = dict(cells=cells, configuration_latches=row['native_cells'].get('sg13cmos5l_dlhq_1', 0),
                    power_terminals=row['power_terminals_checked'])
    if expected['power_terminals'] != 2*cells:
        raise ValueError('Incomplete power census')
    if any(c in str(p) for p in (out, odbs[0], guides[0]) for c in '{}\n\r'):
        raise ValueError('Unsafe tool path')
    out.mkdir(parents=True, exist_ok=False)
    script = OBSERVER + f'''
read_db {{{odbs[0]}}}
read_guides {{{guides[0]}}}
inventory {{{out/'source.txt'}}}
set_thread_count 4
set_routing_layers -signal Metal2-Metal4
detailed_route -droute_end_iter 32 -drc_report_iter_step 1 -output_drc {{{out/'drc.rpt'}}}
puts "R1_DRT_VIOLATIONS [drt::detailed_route_num_drvs]"
inventory {{{out/'routed.txt'}}}
write_db {{{out/'routed.odb'}}}
write_def {{{out/'routed.def'}}}
puts "R1_DRT_END"
'''
    (out/'route.tcl').write_text(script)
    inputs = (Path(__file__), Path(__file__).with_name('detailed_leaf.py'), record, odbs[0], guides[0])
    plan = dict(case=case, expected=expected, source_run=data['run'], scope=SCOPE,
                script_sha256=sha(out/'route.tcl'), input_sha256={str(p):sha(p) for p in inputs})
    (out/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')


def audit(out):
    out = Path(out).resolve()
    plan = json.loads((out/'plan.json').read_text())
    result = dict(passed=False, case=plan['case'], scope=SCOPE,
                  physical_acceptance=False, timing_acceptance=False)
    try:
        code = int((out/'exit-code.txt').read_text())
        result['tool_exit_code'] = code
        if code != 0:
            raise ValueError('Router timeout' if code == 124 else 'Router process failed')
        if any(sha(p) != digest for p, digest in plan['input_sha256'].items()):
            raise ValueError('Frozen input changed')
        if sha(out/'route.tcl') != plan['script_sha256']:
            raise ValueError('Routing policy changed')
        text = (out/'route.log').read_text()
        counts = re.findall(r'^R1_DRT_VIOLATIONS (\d+)$', text, re.M)
        if len(counts) != 1 or len(re.findall(r'^R1_DRT_END$', text, re.M)) != 1:
            raise ValueError('Incomplete or duplicate router completion')
        result['router_violations'] = int(counts[0])
        result.update(check_inventories((out/'source.txt').read_text(),
                                       (out/'routed.txt').read_text(), plan['expected']))
        result['routed_odb_sha256'] = sha(out/'routed.odb')
        if result['router_violations']:
            raise ValueError('Router DRC violations remain')
        result['passed'] = True
    except Exception as exc:
        result['error'] = str(exc)
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    if not result['passed']:
        raise ValueError(result['error'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--capsule', type=Path, required=True)
    p.add_argument('--case', required=True)
    p.add_argument('--out', type=Path, required=True)
    sub.add_parser('audit').add_argument('--out', type=Path, required=True)
    args = vars(parser.parse_args()); mode = args.pop('mode')
    (prepare if mode == 'prepare' else audit)(**args)
