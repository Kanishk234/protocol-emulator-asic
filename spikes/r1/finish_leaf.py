"""Finish authenticated detailed-routed R1 contexts; never chip/timing acceptance."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from detailed_leaf import OBSERVER, sha

SOURCE_RUN = 44394572610
SOURCE_SHA = '5db0b642a9ea3c5d1c7b9a76f1ed74edf1a52716'
ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT/'docs/reports/r1_detailed_contexts_44394572610.json'
CAMPAIGN_SHA = '865c170a300db97f2116360bd25ad7af809ed7803376d6d78762560b4a20a11a'
GATES = ('route__drc_errors', 'design__critical_disconnected_pin__count',
         'antenna__violating__nets', 'antenna__violating__pins',
         'magic__drc_error__count', 'klayout__drc_error__count', 'design__lvs_error__count')
SCOPE = ('Frozen leaf finishing diagnostic; no assembled macro, shell, '
         'configured timing, replacement or submission acceptance.')


def identity(data):
    expected = dict(id=SOURCE_RUN, head_sha=SOURCE_SHA, run_attempt=1,
                    status='completed', conclusion='success', head_branch='efpga',
                    path='.github/workflows/r1_detailed_contexts.yaml')
    if any(data.get(k) != v for k, v in expected.items()):
        raise ValueError('Wrong detailed-route producer')


def gates_pass(metrics):
    return all(type(metrics.get(k)) in (int, float) and metrics[k] == 0 for k in GATES)


def campaign_case(case):
    if sha(CAMPAIGN) != CAMPAIGN_SHA:
        raise ValueError('Frozen routing evidence changed')
    data = json.loads(CAMPAIGN.read_text())
    rows = [r for r in data['reviewed_contexts'] if r['case'] == case]
    artifacts = [a for a in data['artifact_metadata']
                 if a['name'] == f'r1-detailed-context-{SOURCE_RUN}-{case}']
    if len(rows) != 1 or len(artifacts) != 1 or not rows[0]['passed']:
        raise ValueError('Unknown or unqualified finishing context')
    return rows[0], artifacts[0]


def finishing_steps(classes):
    ids = [s.id for s in classes]
    steps = classes[ids.index('Odb.RemoveRoutingObstructions'):ids.index('Checker.LVS')+1]
    required = {'OpenROAD.CheckAntennas', 'Checker.TrDRC', 'Checker.DisconnectedPins',
                'OpenROAD.FillInsertion', 'OpenROAD.RCX', 'OpenROAD.STAPostPNR',
                'KLayout.StreamOut', 'Magic.DRC', 'KLayout.DRC', 'Checker.MagicDRC',
                'Checker.KLayoutDRC', 'Magic.SpiceExtraction', 'Netgen.LVS', 'Checker.LVS'}
    # SequentialFlow suffixes repeated stages (the post-DRT antenna stage is -1).
    actual = {re.sub(r'-[0-9]+$', '', s.id) for s in steps}
    if not required <= actual:
        raise ValueError('Missing required finishing stages: '+str(sorted(required-actual)))
    return steps


def check_finished_inventory(before, after, expected=None):
    if expected is None:
        expected = dict(cells=1243, required_signal_nets_with_wires=1347)
    def rows(text):
        return [line.split('\t') for line in text.splitlines()]
    original, final = rows(before), rows(after)
    oldcells = {r[1]: r for r in original if r[0] == 'CELL'}
    newcells = {r[1]: r for r in final if r[0] == 'CELL'}
    if len(oldcells) != expected['cells'] or not oldcells.keys() <= newcells.keys():
        raise ValueError('Original leaf cells missing')
    additions = set(newcells) - set(oldcells)
    if any(not re.fullmatch(r'sg13cmos5l_(?:fill|decap)_[0-9]+', newcells[n][2]) for n in additions):
        raise ValueError('Finishing added a functional cell')
    if any(oldcells[n] != newcells[n] for n in oldcells):
        raise ValueError('Finishing changed original cells or placement')
    def frozen(data):
        return sorted(r for r in data if r[0] in ('PORT', 'PBOX') or
                      (r[0] == 'ITERM' and r[1] in oldcells))
    if frozen(original) != frozen(final):
        raise ValueError('Finishing changed original connectivity or interface')
    a = {r[1]: r[2] for r in original if r[0] == 'REQUIRED_NET'}
    b = {r[1]: r[2] for r in final if r[0] == 'REQUIRED_NET'}
    if len(a) != expected['required_signal_nets_with_wires'] or a != b or any(v != '1' for v in b.values()):
        raise ValueError('Finishing changed or lost required signal wires')
    return dict(original_cells=len(oldcells), added_fill_or_decap_cells=len(additions),
                required_signal_nets_with_wires=len(b))


def prepare(capsule, routed, producer, out, case='lut0'):
    capsule, routed, producer, out = (Path(p).resolve() for p in (capsule, routed, producer, out))
    identity(json.loads(producer.read_text()))
    expected, _ = campaign_case(case)
    result = json.loads((routed/'result.json').read_text())
    if (result != expected or result['tool_exit_code'] != 0 or result['router_violations'] != 0
            or sha(routed/'routed.odb') != expected['routed_odb_sha256']):
        raise ValueError('Require exact passed context route')
    route_plan = json.loads((routed/'plan.json').read_text())
    if route_plan['case'] != case:
        raise ValueError('Route plan context differs')
    for name, digest in route_plan['input_sha256'].items():
        if '/build/r1_timing/' in name:
            path = capsule/name.split('/build/r1_timing/', 1)[1]
        else:
            suffix = name.split('/protocol-emulator-asic/protocol-emulator-asic/', 1)[-1]
            if suffix not in ('spikes/r1/detailed_context.py', 'spikes/r1/detailed_leaf.py'):
                raise ValueError('Unknown route input')
            path = Path(__file__).resolve().parents[2]/suffix
        if sha(path) != digest:
            raise ValueError('Frozen source input differs')
    if sha(routed/'route.tcl') != route_plan['script_sha256']:
        raise ValueError('Route script differs')
    records = []
    for record in (capsule/'leaves').glob('*/native/result.json'):
        data = json.loads(record.read_text())
        if data.get('balanced_case', {}).get('name') == case:
            records.append((record, data))
    if len(records) != 1:
        raise ValueError('Missing unique original global context')
    record, data = records[0]; native = record.parent
    if len(data['cases']) != 1:
        raise ValueError('Unexpected original case sweep')
    folder = native/next(iter(data['cases']))
    stages = list(folder.glob('*-openroad-globalrouting'))
    if len(stages) != 1:
        raise ValueError('Missing unique original global stage')
    stage = stages[0]
    state = json.loads((stage/'state_out.json').read_text())
    def relocate(value):
        if isinstance(value, dict):
            return {k: relocate(v) for k, v in value.items()}
        if isinstance(value, list):
            return [relocate(v) for v in value]
        if isinstance(value, str) and value.startswith('/home/runner/work/'):
            for prefix in ('/build/r1_balanced_remaining/native/', '/build/r1_balanced_leaf/native/'):
                if prefix in value:
                    return str(native/value.split(prefix, 1)[1])
            if '/build/r1_balanced_source/input/' in value:
                return str(capsule/'mapped/input'/value.split('/build/r1_balanced_source/input/', 1)[1])
            raise ValueError('Unrecognized source path')
        return value
    state = relocate(state)
    state['odb'] = str(routed/'routed.odb');state['def'] = str(routed/'routed.def')
    # This value comes from the authenticated detailed router, not the GRT state.
    state['metrics']['route__drc_errors'] = result['router_violations']
    config = relocate(json.loads((folder/'policy.json').read_text())['config'])
    config.update(PRIMARY_GDSII_STREAMOUT_TOOL='klayout', MAGIC_EXT_USE_GDS=True)
    out.mkdir(parents=True, exist_ok=False)
    (out/'initial.json').write_text(json.dumps(state)+'\n')
    (out/'config.json').write_text(json.dumps(config, indent=2)+'\n')
    inputs = [Path(__file__), CAMPAIGN, record, producer, routed/'result.json', routed/'plan.json',
              routed/'routed.odb', routed/'routed.def', routed/'routed.txt',
              out/'initial.json', out/'config.json']
    for key, value in state.items():
        if key != 'metrics' and isinstance(value, str):
            inputs.append(Path(value))
    (out/'plan.json').write_text(json.dumps(dict(scope=SCOPE, source_run=SOURCE_RUN, case=case,
        expected=dict(cells=expected['cells'], required_signal_nets_with_wires=expected['required_signal_nets_with_wires']),
        input_sha256={str(p):sha(p) for p in inputs}), indent=2)+'\n')


def inside(out):
    from librelane.flows.classic import Classic
    from librelane.state import State, DesignFormat
    from cloud_tile_harden import metric_json
    out = Path(out).resolve()
    plan = json.loads((out/'plan.json').read_text())
    if any(sha(p) != digest for p, digest in plan['input_sha256'].items()):
        raise ValueError('Finishing input changed')
    (out/'available-stages.json').write_text(json.dumps([s.id for s in Classic.Steps], indent=2)+'\n')
    steps = finishing_steps(Classic.Steps)
    class Finish(Classic):
        Steps = steps
    result = dict(passed=False, case=plan['case'], scope=SCOPE, physical_acceptance=False, timing_acceptance=False)
    try:
        flow = Finish(json.loads((out/'config.json').read_text()), design_dir=str(out),
                      pdk='ihp-sg13cmos5l', pdk_root=os.environ['PDK_ROOT'])
        (out/'stages.json').write_text(json.dumps([s.id for s in flow.Steps], indent=2)+'\n')
        final = flow.start(with_initial_state=State.load(json.loads((out/'initial.json').read_text())),
                           _force_run_dir=str(out/'run'))
        metrics = json.loads(json.dumps(final.metrics.to_raw_dict(), default=metric_json))
        result['metrics'] = metrics
        result['physical_gate_metrics'] = {k: metrics.get(k) for k in GATES}
        observer = out/'observe.tcl'
        observer.write_text(OBSERVER+f'\nread_db {{{final[DesignFormat.ODB]}}}\ninventory {{{out/"final.txt"}}}\n')
        with (out/'observe.log').open('w') as stream:
            subprocess.run(['openroad', '-exit', str(observer)], stdout=stream,
                           stderr=subprocess.STDOUT, check=True, timeout=120)
        source = Path(json.loads((out/'initial.json').read_text())['odb']).parent/'routed.txt'
        result.update(check_finished_inventory(source.read_text(), (out/'final.txt').read_text(), plan['expected']))
        for key in (DesignFormat.ODB, DesignFormat.GDS, DesignFormat.NETLIST):
            path = Path(str(final[key]))
            result[key.id+'_sha256'] = sha(path)
        if not gates_pass(metrics):
            raise ValueError('Physical gates missing or nonzero')
        result['passed'] = True
    except Exception as exc:
        result['error'] = str(exc)
    if 'physical_gate_metrics' not in result:
        # Retain completed-stage evidence on a failed flow without promoting it.
        partial = {}
        for path in sorted((out/'run').glob('*/state_out.json')):
            partial.update(json.loads(path.read_text()).get('metrics', {}))
        result['physical_gate_metrics'] = {k: partial.get(k) for k in GATES}
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    if not result['passed']:
        raise ValueError(result['error'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('prepare')
    for name in ('capsule', 'routed', 'producer', 'out'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--case', default='lut0')
    sub.add_parser('inside').add_argument('--out', type=Path, required=True)
    args = vars(parser.parse_args());mode = args.pop('mode')
    if mode == 'inside':
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'test_internal'))
    (prepare if mode == 'prepare' else inside)(**args)
