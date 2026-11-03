"""Diagnostic-only edits to frozen physical copies; never a stock GDS candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import os
from native_stock_route import run_step
from postgrt_timing import screen

TARGETS = {'hold7969/A': '_10511_', 'wire13568/A': '_19518_',
           '_38673_/A': 'net11878', 'wire12579/A': 'net12579'}


def violating_sinks(report):
    result = set()
    for net in re.split(r'(?=^Net:)', report, flags=re.M):
        for pin in re.split(r'(?=^  Pin:)', net, flags=re.M)[1:]:
            if '(VIOLATED)' in pin:
                result.add(re.match(r'  Pin:\s+(\S+)', pin).group(1))
    return result


def components(text):
    block = text.split('\nCOMPONENTS ', 1)[1].split('END COMPONENTS', 1)[0]
    result = {}
    for name, master, body in re.findall(r'(?m)^\s*-\s+(\S+)\s+(\S+)\s+(.*?);', block, re.S):
        pos = re.search(r'\+ (?:PLACED|FIXED|COVER) \( (\d+) (\d+) \) (\w+)', body)
        if pos is None:
            raise ValueError('Unplaced original or added cell: ' + name)
        result[name] = (master, *pos.groups())
    return result


def verify_edit(before, after, insert):
    old, new = components(before), components(after)
    if any(new.get(name) != value for name, value in old.items()):
        raise ValueError('Diagnostic moved, resized or removed an original cell')
    added = set(new) - set(old)
    if len(added) != (4 if insert else 0):
        raise ValueError('Unexpected added-cell count')
    if any(new[n][0] != 'sg13cmos5l_antennanp' for n in added):
        raise ValueError('Unexpected added cell master')
    def logical_connections(text):
        block = text.split('\nNETS ', 1)[1].split('END NETS', 1)[0]
        result = {}
        for net, body in re.findall(r'(?m)^\s*- (\S+)\s+(.*?);', block, re.S):
            result[net] = {pair for pair in re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)', body)
                           if pair[0] in old or pair[0] == 'PIN'}
        return result
    if logical_connections(before) != logical_connections(after):
        raise ValueError('An original signal connection changed')
    nets = after.split('\nNETS ', 1)[1].split('END NETS', 1)[0]
    for index, (target, net) in enumerate(TARGETS.items()):
        block = re.search(r'(?m)^\s*- ' + re.escape(net) + r'\s+(.*?);', nets, re.S)
        if block is None:
            raise ValueError('Missing target net')
        connections = set(re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)', block.group(1)))
        if tuple(target.split('/')) not in connections:
            raise ValueError('Target sink moved to another net')
        if insert and (f'eco_diode_{index}', 'A') not in connections:
            raise ValueError('Diode not directly attached to reviewed sink net')
    return len(added)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--insert', choices=['true', 'false'], required=True)
    args = parser.parse_args()
    insert = args.insert == 'true'
    manifest = json.loads(Path(os.environ['SOURCE_MANIFEST']).read_text())
    source = Path(manifest['source_state'])
    state = json.loads(source.read_text())
    verify_edit(Path(state['def']).read_text(), Path(state['def']).read_text(), False)
    before_hashes = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
                     for name in manifest['files']}
    if before_hashes != manifest['files']:
        raise ValueError('Frozen inputs changed since recovery')
    config = json.loads(Path('src/config_merged.json').read_text())
    run_step(config, source, Path('runs/endpoint-before-antenna'), ['OpenROAD.CheckAntennas'])
    fresh = list(Path('runs/endpoint-before-antenna').glob('*/or_metrics_out.json'))
    if len(fresh) != 1:
        raise ValueError('Missing source antenna evidence')
    metrics = json.loads(fresh[0].read_text())
    if metrics['antenna__violating__nets'] != 4 or metrics['antenna__violating__pins'] != 4:
        raise ValueError('Wrong frozen failure baseline')
    reports = list(Path('runs/endpoint-before-antenna').glob('*/reports/antenna.rpt'))
    if len(reports) != 1 or violating_sinks(reports[0].read_text()) != set(TARGETS):
        raise ValueError('Fresh source violations differ from reviewed endpoints')
    interface = json.loads(Path('runs/native-endpoint-interface.json').read_text())
    cfg = dict(config, **interface['diode_config'])
    cfg['INSERT_ECO_DIODES'] = [dict(target=t, placement=None) for t in TARGETS] if insert else []
    output = Path('runs/endpoint-diagnostic')
    run_step(cfg, source, output, ['Odb.InsertECODiodes'])
    resolved = json.loads((output / 'resolved.json').read_text())
    if [item['target'] for item in resolved['INSERT_ECO_DIODES']] != (list(TARGETS) if insert else []):
        raise ValueError('Native insertion targets differ from the reviewed control')
    states = list(output.glob('*/state_out.json'))
    if len(states) != 1:
        raise ValueError('Missing unique native diagnostic output')
    edited = json.loads(states[0].read_text())
    def_path = Path(edited['def'])
    if not def_path.resolve().is_relative_to(output.resolve()):
        raise ValueError('Native step skipped; no edited/control DEF produced')
    added = verify_edit(Path(state['def']).read_text(), def_path.read_text(), insert)
    run_step(config, states[0], Path('runs/endpoint-after-antenna'), ['OpenROAD.CheckAntennas'])
    reports = list(Path('runs/endpoint-after-antenna').glob('*/reports/antenna.rpt'))
    metric_paths = list(Path('runs/endpoint-after-antenna').glob('*/or_metrics_out.json'))
    if len(reports) != 1 or len(metric_paths) != 1:
        raise ValueError('Missing fresh endpoint response')
    after_sinks = violating_sinks(reports[0].read_text())
    after_metrics = json.loads(metric_paths[0].read_text())
    # STA reads the modified ODB, with the original frozen SDC explicitly bound.
    # The inherited NL is not an updated gate-level netlist and is not used for GL.
    shutil.copytree('src', 'audit-src')
    screen(Path('audit-src/config_merged.json'), source, Path('runs/endpoint-timing'),
           os.environ['PDK_ROOT'], repaired=states[0], sdc=Path(state['sdc']))
    if any(hashlib.sha256(Path(n).read_bytes()).hexdigest() != h for n, h in before_hashes.items()):
        raise ValueError('Frozen source mutated')
    result = dict(source_run=manifest['run']['id'], insert=insert, added_diodes=added,
                  after_violating_sinks=sorted(after_sinks),
                  target_still_violates={t: t in after_sinks for t in TARGETS},
                  fresh_after_antenna={k: after_metrics[k] for k in ('antenna__violating__nets', 'antenna__violating__pins')},
                  original_cells_unchanged=True, source_files_unchanged=True,
                  post_edit_gate_level_netlist_exported=False,
                  qualification_performed=False, promotable_stock_recipe=False,
                  detailed_routing_performed=False,
                  scope='Native experimental endpoint diagnosis; compare with empty-insertion control')
    (output / 'diagnostic_result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
