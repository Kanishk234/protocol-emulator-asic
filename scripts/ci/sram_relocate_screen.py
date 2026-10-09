"""One-buffer relocation from exact timing-passing strength route; no DRT."""
import json
import os
import re
from pathlib import Path
from event_nor2_screen import logical_cells, validate_overflow, validate_antenna_only_changes
from sram_buffer_plan import plan
from native_route_gl import validate
from native_stock_route import run_step, qualified, fingerprints
from postgrt_timing import screen


def validate_history(log):
    if (log.count('TRIPWIRE SRAM relocation: wire9447 ') != 1
            or log.count('exact site/master/nets retained after legalization') != 1
            or 'TRIPWIRE native hold100 setup:' in log):
        raise ValueError('Missing/repeated SRAM relocation or unexpected sizing')
    resets = re.findall(r'TRIPWIRE native route reset: cleared ([0-9]+) ordinary routed wires', log)
    if len(resets) != 1 or int(resets[0]) == 0:
        raise ValueError('Missing or ambiguous native detailed-wire reset')
    validate_overflow(log)


def promote(state_path, baseline):
    state = json.loads(state_path.read_text())
    odb = Path(state['odb'])
    before = odb.with_suffix('.baseline.nl.v')
    nl, pnl = odb.with_suffix('.eco.nl.v'), odb.with_suffix('.eco.pnl.v')
    if not all(p.is_file() for p in (before, nl, pnl)):
        raise ValueError('Fresh native physical netlists missing')
    if logical_cells(before.read_text()) != logical_cells(baseline.read_text()):
        raise ValueError('Native ODB differs from measured extracted netlist')
    if logical_cells(before.read_text()) != logical_cells(nl.read_text()):
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


def main():
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
    placement_plan = plan(baseline, source.parent / 'tt_um_tripwire.def')
    # Step configs omit synthesis/resizer variables; use the audited full recipe.
    config = json.loads(Path('src/config_native_stock.json').read_text())
    if config.get('GRT_RESIZER_HOLD_SLACK_MARGIN') != 0.10:
        raise ValueError('Native hold target mismatch')
    config['GRT_ALLOW_CONGESTION'] = False
    output = Path('runs/native-sram-relocate')
    output.mkdir(exist_ok=False)
    (output / 'source_plan.json').write_text(json.dumps(placement_plan, indent=2) + '\n')
    # Build only after source/hash checks, keeping the pinned flow image base.
    import subprocess
    subprocess.run(['docker', 'build', '-t', 'tripwire-sram-relocate:local',
                    '-f', 'workflow-src/scripts/ci/Dockerfile.openroad-sram-relocate',
                    'workflow-src/scripts/ci'], check=True)
    os.environ['LIBRELANE_IMAGE_OVERRIDE'] = 'tripwire-sram-relocate:local'
    grt = output / 'grt'
    run_step(config, source, grt, ['OpenROAD.GlobalRouting'])
    paths = list(grt.glob('*-openroad-globalrouting/state_out.json'))
    if len(paths) != 1:
        raise ValueError('Fresh native GRT missing')
    log = (paths[0].parent / 'openroad-globalrouting.log').read_text()
    validate_history(log)
    changed = promote(paths[0], baseline)
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
    path = Path('src/config_native_sram_relocate.json')
    path.write_text(json.dumps(config, indent=2) + '\n')
    screen(path, checked, output / 'timing', os.environ['PDK_ROOT'],
           repaired=checked, sdc=Path('src/signoff.sdc'))
    timing = json.loads((output / 'timing/comparison.json').read_text())
    ready = qualified(timing, metrics)
    (output / 'gates.json').write_text(json.dumps(dict(source_run=run['id'],
        changes=0, relocated_instances=1, qualified=ready, minimum_fast_hold_ns=0.05,
        physical_screen_only=True, official_signoff=False), indent=2) + '\n')
    if not ready:
        raise ValueError('SRAM relocation screen fails timing/hold/antenna gates')


if __name__ == '__main__':
    main()
