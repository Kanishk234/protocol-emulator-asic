"""One-buffer relocation from exact timing-passing strength route; no DRT."""
import json
import os
import re
import argparse
from pathlib import Path
from event_nor2_screen import logical_cells, validate_overflow, validate_antenna_only_changes
from sram_buffer_plan import plan
from native_route_gl import validate
from native_stock_route import run_step, qualified, fingerprints
from postgrt_timing import screen


def validate_history(log, target='dout0'):
    receipt = {'dout0': 'TRIPWIRE SRAM relocation: wire9447 ',
               'ren': 'TRIPWIRE SRAM REN relocation: _29426_ ',
               'antenna-branch': 'TRIPWIRE antenna branch: _03831_ '}[target]
    legal = ('TRIPWIRE antenna branch: legalization completed' if target == 'antenna-branch'
             else 'exact site/master/nets retained after legalization')
    other_move = any(prefix in log for prefix in
                     {'TRIPWIRE SRAM relocation: wire9447 ',
                      'TRIPWIRE SRAM REN relocation: _29426_ ',
                      'TRIPWIRE antenna branch: _03831_ '} - {receipt})
    if (log.count(receipt) != 1
            or log.count(legal) != 1
            or other_move
            or 'TRIPWIRE native hold100 setup:' in log
            or (target == 'ren' and 'TRIPWIRE SRAM relocation: wire9447 ' in log)
            or (target == 'dout0' and 'TRIPWIRE SRAM REN relocation: _29426_ ' in log)):
        raise ValueError('Missing/repeated SRAM relocation or unexpected sizing')
    resets = re.findall(r'TRIPWIRE native route reset: cleared ([0-9]+) ordinary routed wires', log)
    if len(resets) != 1 or int(resets[0]) == 0:
        raise ValueError('Missing or ambiguous native detailed-wire reset')
    validate_overflow(log)


def promote(state_path, baseline, target='dout0'):
    state = json.loads(state_path.read_text())
    odb = Path(state['odb'])
    before = odb.with_suffix('.baseline.nl.v')
    nl, pnl = odb.with_suffix('.eco.nl.v'), odb.with_suffix('.eco.pnl.v')
    if not all(p.is_file() for p in (before, nl, pnl)):
        raise ValueError('Fresh native physical netlists missing')
    if logical_cells(before.read_text()) != logical_cells(baseline.read_text()):
        raise ValueError('Native ODB differs from measured extracted netlist')
    if target == 'antenna-branch':
        from antenna_branch import validate_change
        validate_change(baseline.read_text(), nl.read_text())
    elif logical_cells(before.read_text()) != logical_cells(nl.read_text()):
        raise ValueError('SRAM relocation changed logical cells or connections')
    state.update(nl=str(nl.resolve()), pnl=str(pnl.resolve()), spef=None, sdf=None, lib=None)
    promoted = state_path.with_name('eco_state.json')
    promoted.write_text(json.dumps(state, indent=2) + '\n')
    return promoted


def promote_antenna(state_path, baseline):
    state = json.loads(state_path.read_text())
    odb = Path(state['odb'])
    nl, pnl = odb.with_suffix('.eco.nl.v'), odb.with_suffix('.eco.pnl.v')
    if not all(p.is_file() for p in (nl, pnl)):
        raise ValueError('Fresh native antenna netlists missing')
    validate_antenna_only_changes(baseline.read_text(), nl.read_text())
    state.update(nl=str(nl.resolve()), pnl=str(pnl.resolve()), spef=None, sdf=None, lib=None)
    promoted = state_path.with_name('eco_state.json')
    promoted.write_text(json.dumps(state, indent=2) + '\n')
    return promoted


def main(target='dout0'):
    if target not in ('dout0', 'ren', 'antenna-branch'):
        raise ValueError('Unreviewed SRAM relocation target')
    name = {'dout0': 'sram-relocate', 'ren': 'sram-ren-relocate',
            'antenna-branch': 'antenna-branch'}[target]
    root = Path.cwd()
    run = json.loads(Path('/tmp/native-eco-source-run.json').read_text())
    validate(root, run)
    if run['id'] != 37954320974:
        raise ValueError('Only timing-passing strength source allowed')
    expected = json.loads(Path('/tmp/native-trusted-files.json').read_text())
    actual = fingerprints(root)
    def hardware(values):
        return {k: v for k, v in values.items()
                if not (k.startswith('src/config') and k.endswith('.json'))}
    if hardware(expected) != hardware(actual):
        raise ValueError('Native strength hardware/constraint fingerprint mismatch')
    if json.loads(Path('src/config_native_stock.json').read_text()) != json.loads(
            Path('/tmp/native-trusted-config.json').read_text()):
        raise ValueError('Native strength source recipe mismatch')
    route = Path('runs/native-strength-route/drt')
    states = list(route.glob('*-openroad-detailedrouting/state_out.json'))
    if len(states) != 1:
        raise ValueError('One strength DRT source required')
    source = states[0]
    baseline = source.parent / 'tt_um_tripwire.nl.v'
    if target == 'antenna-branch':
        from antenna_branch import validate_source, SINKS
        validate_source(baseline.read_text())
        placement_plan = dict(target=target, source_run=run['id'], added_buffers=1,
                              moved_pins=sorted(SINKS), legal_site_verified=False,
                              initial_location_dbu=[1250400, 291060])
    else:
        placement_plan = plan(baseline, source.parent / 'tt_um_tripwire.def', target=target)
    # Step configs omit synthesis/resizer variables; use the audited full recipe.
    config = json.loads(Path('src/config_native_stock.json').read_text())
    if config.get('GRT_RESIZER_HOLD_SLACK_MARGIN') != 0.10:
        raise ValueError('Native hold target mismatch')
    config['GRT_ALLOW_CONGESTION'] = False
    output = Path('runs/native-' + name)
    output.mkdir(exist_ok=False)
    (output / 'source_plan.json').write_text(json.dumps(placement_plan, indent=2) + '\n')
    # Build only after source/hash checks, keeping the pinned flow image base.
    import subprocess
    subprocess.run(['docker', 'build', '-t', 'tripwire-' + name + ':local',
                    '-f', 'workflow-src/scripts/ci/Dockerfile.openroad-' + name,
                    'workflow-src/scripts/ci'], check=True)
    os.environ['LIBRELANE_IMAGE_OVERRIDE'] = 'tripwire-' + name + ':local'
    grt = output / 'grt'
    run_step(config, source, grt, ['OpenROAD.GlobalRouting'])
    paths = list(grt.glob('*-openroad-globalrouting/state_out.json'))
    if len(paths) != 1:
        raise ValueError('Fresh native GRT missing')
    log = (paths[0].parent / 'openroad-globalrouting.log').read_text()
    validate_history(log, target)
    changed = promote(paths[0], baseline, target)
    # Same pinned image; wrapper only exports fresh antenna views in cleanup.
    # Preserve repaired guides; never run full GRT after antenna repair.
    antenna = output / 'antenna'
    run_step(config, changed, antenna, ['OpenROAD.CheckAntennas'])
    paths = list(antenna.glob('*-openroad-checkantennas/state_out.json'))
    if len(paths) != 1:
        raise ValueError('Fresh antenna state missing')
    checked = paths[0]
    metrics = json.loads((checked.parent / 'or_metrics_out.json').read_text())
    if metrics.get('antenna__violating__nets') or metrics.get('antenna__violating__pins'):
        cleanup = output / 'antenna-cleanup'
        run_step(config, changed, cleanup, ['OpenROAD.RepairAntennas', 'OpenROAD.CheckAntennas'])
        paths = list(cleanup.glob('*-openroad-checkantennas/state_out.json'))
        if len(paths) != 1:
            raise ValueError('Fresh antenna cleanup state missing')
        checked = paths[0]
        metrics = json.loads((checked.parent / 'or_metrics_out.json').read_text())
        resolved = json.loads((cleanup / 'resolved.json').read_text())
        logs = list(cleanup.glob('*-openroad-repairantennas/*-openroad-diodeinsertion/openroad-diodeinsertion.log'))
        if (resolved.get('GRT_ALLOW_CONGESTION') is not False or len(logs) != 1
                or 'repair_antennas' not in logs[0].read_text()
                or '-allow_congestion' in logs[0].read_text()):
            raise ValueError('Native cleanup congestion policy not enforced')
        checked = promote_antenna(checked, Path(json.loads(changed.read_text())['nl']))
    path = Path('src/config_native_' + name.replace('-', '_') + '.json')
    path.write_text(json.dumps(config, indent=2) + '\n')
    screen(path, checked, output / 'timing', os.environ['PDK_ROOT'],
           repaired=checked, sdc=Path('src/signoff.sdc'))
    timing = json.loads((output / 'timing/comparison.json').read_text())
    ready = qualified(timing, metrics)
    (output / 'gates.json').write_text(json.dumps(dict(source_run=run['id'],
        changes=1 if target == 'antenna-branch' else 0,
        relocated_instances=0 if target == 'antenna-branch' else 1,
        qualified=ready, minimum_fast_hold_ns=0.05,
        target=target, physical_screen_only=True, official_signoff=False), indent=2) + '\n')
    if not ready:
        raise ValueError('SRAM relocation screen fails timing/hold/antenna gates')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=['dout0', 'ren', 'antenna-branch'], default='dout0')
    main(parser.parse_args().target)
