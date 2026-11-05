"""Three sizes plus one diode on a frozen copy; never official-flow qualification."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from native_stock_route import run_step
from postgrt_timing import screen
from event_nor2_screen import logical_cells


def one(root, pattern):
    paths = list(root.glob(pattern))
    if len(paths) != 1:
        raise ValueError('Missing unique evidence: ' + pattern)
    return paths[0]


def main(edit):
    manifest = json.loads(Path(os.environ['SOURCE_MANIFEST']).read_text())
    source = Path(manifest['source_state'])
    state = json.loads(source.read_text())
    frozen = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in manifest['files']}
    assert frozen == manifest['files']
    config = json.loads(Path('src/config_merged.json').read_text())
    original = logical_cells(Path(state['nl']).read_text())
    plan = json.loads(Path('spikes/phase2_stock_flow/antenna_targeted_sizing_feasibility.json').read_text())
    for item in plan['cases']:
        assert original[item['instance']][0] == item['original_master']
    output = Path('runs/targeted-diagnostic')
    output.mkdir()
    hook = Path('scripts/ci/targeted_antenna_size.tcl').resolve()
    if not edit:
        hook = (output / 'control_snapshot.tcl').resolve()
        hook.write_text('set base [file join $::env(STEP_DIR) targeted_sizing]\nwrite_db ${base}.odb\nwrite_def ${base}.def\nwrite_verilog ${base}.nl.v\nwrite_verilog -include_pwr_gnd ${base}.pnl.v\n')
    sizing = dict(config, STA_EXTRA_CORNER_TCL_FILE=str(hook))
    run_step(sizing, source, output / 'sizing', ['OpenROAD.STAMidPNR'])
    snapshot = one(output / 'sizing', '*-openroad-stamidpnr/targeted_sizing.odb').with_suffix('')
    changed = dict(state)
    for key, suffix in [('odb', '.odb'), ('def', '.def'), ('nl', '.nl.v'), ('pnl', '.pnl.v')]:
        path = Path(str(snapshot) + suffix)
        assert path.is_file()
        changed[key] = str(path.resolve())
    changed['metrics'] = {}
    handoff = output / 'sized_state.json'
    handoff.write_text(json.dumps(changed, indent=2) + '\n')
    expected = dict(original)
    if edit:
        for item in plan['cases']:
            name = item['instance']
            expected[name] = (item['candidate_master'], original[name][1])
    assert logical_cells(Path(changed['nl']).read_text()) == expected, 'Unexpected sizing connectivity change'
    interface = json.loads(Path('runs/native-endpoint-interface.json').read_text())
    diode_config = dict(config, **interface['diode_config'])
    diode_config['INSERT_ECO_DIODES'] = [dict(target='hold7969/A', placement=None)] if edit else []
    run_step(diode_config, handoff, output / 'diode', ['Odb.InsertECODiodes'])
    diode_state = one(output / 'diode', '*/state_out.json')
    run_step(config, diode_state, output / 'routing', ['OpenROAD.GlobalRouting'])
    final = one(output / 'routing', '*-openroad-globalrouting/state_out.json')
    final_state = json.loads(final.read_text())
    actual = logical_cells(Path(final_state['nl']).read_text())
    assert all(actual.get(n) == c for n, c in expected.items()), 'Original logical cell/connection changed'
    added = set(actual) - set(expected)
    assert len(added) == (1 if edit else 0)
    if edit:
        cell = actual[next(iter(added))]
        assert cell[0] == 'sg13cmos5l_antennanp' and dict(cell[1]).get('A') == '_10511_'
    run_step(config, final, output / 'antenna', ['OpenROAD.CheckAntennas'])
    shutil.copytree('src', 'target-audit-src')
    screen(Path('target-audit-src/config_merged.json'), final, output / 'timing', os.environ['PDK_ROOT'], repaired=final,
           sdc=Path(state['sdc']), sta_grt_adjustment=config['GRT_ADJUSTMENT'])
    log = one(output / 'routing', '*-openroad-globalrouting/openroad-globalrouting.log').read_text()
    overflow = re.findall(r'(?m)^Total\s+\d+\s+\d+\s+[0-9.]+%\s+\d+\s*/\s*\d+\s*/\s*(\d+)\s*$', log)
    assert overflow
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in frozen.items())
    antenna = json.loads(one(output / 'antenna', '*/or_metrics_out.json').read_text())
    result = dict(edited=edit, exact_original_connections_preserved=True, added_diodes=len(added),
                  final_overflow=int(overflow[-1]), fresh_antenna={k: antenna[k] for k in ('antenna__violating__nets', 'antenna__violating__pins')},
                  timing=json.loads((output / 'timing/comparison.json').read_text()),
                  source_unchanged=True, qualification_performed=False, promotable_stock_recipe=False,
                  detailed_routing_performed=False, scope='Experimental snapshot edits and reroute; no official-flow authority')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--insert', choices=['true', 'false'], required=True)
    main(parser.parse_args().insert == 'true')
