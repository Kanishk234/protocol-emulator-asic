"""One setup-buffer strength screen on the selected fanout route; no DRT."""
import json
import os
import re
from pathlib import Path
from event_nor2_screen import logical_cells, validate_overflow, validate_antenna_only_changes
from fanout_setup_plan import plan, target_call, validate_change, NL_SHA
import argparse
from native_stock_route import validate_source
import hashlib
from native_stock_route import run_step, qualified, fingerprints
from postgrt_timing import screen


def promote(state_path, baseline, layout, proposal):
    state = json.loads(state_path.read_text())
    odb = Path(state['odb'])
    before = odb.with_suffix('.baseline.nl.v')
    nl, pnl = odb.with_suffix('.eco.nl.v'), odb.with_suffix('.eco.pnl.v')
    if not all(p.is_file() for p in (before, nl, pnl)):
        raise ValueError('Fresh native physical netlists missing')
    if logical_cells(before.read_text()) != logical_cells(baseline.read_text()):
        raise ValueError('Native ODB differs from measured extracted netlist')
    validate_change(before.read_text(), layout.read_text(), nl.read_text(), proposal)
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


SOURCE_RUN = 38103189246
SOURCE_SHA = 'ad189c03a2d9f46826365bb7e452721fc3be0f95'


def validate_inputs(root, run, expected, trusted_config):
    if (run.get('id') != SOURCE_RUN or run.get('head_sha') != SOURCE_SHA
            or run.get('head_branch') != 'main' or run.get('conclusion') != 'success'
            or run.get('path') != '.github/workflows/gds-clock8-fanout-route.yaml'):
        raise ValueError('Wrong extracted clock8 source provenance')
    config = json.loads((root / 'src/config_native_stock.json').read_text())
    if config != trusted_config:
        raise ValueError('Clock8 recipe differs from trusted generated config')
    # Validate the inherited clean-build recipe without accepting route success as timing closure.
    screen_run = dict(id=37990280838, head_sha='dfe1a9f46d9b97d20550d1326fb7755cbe2829cf',
        head_branch='main', conclusion='success', path='.github/workflows/gds-native-clock8-screen.yaml')
    validate_source(screen_run,
        json.loads((root / 'runs/native-stock-screen/recipe.json').read_text()),
        config, expected, fingerprints(root), profile='clock8')


def main(kind):
    root = Path.cwd()
    run = json.loads(Path('/tmp/native-eco-source-run.json').read_text())
    validate_inputs(root, run,
        json.loads(Path('/tmp/native-trusted-files.json').read_text()),
        json.loads(Path('/tmp/native-trusted-config.json').read_text()))
    route = Path('runs/clock8-fanout-route/drt')
    states = list(route.glob('*-openroad-detailedrouting/state_out.json'))
    if len(states) != 1:
        raise ValueError("Ambiguous clock8 DRT source")
    source = states[0]
    state = json.loads(source.read_text())
    for key in ("odb", "def", "nl", "pnl", "sdc"):
        if not Path(state[key]).is_file():
            raise ValueError("Missing clock8 checkpoint " + key)
    baseline, layout = Path(state['nl']), Path(state['def'])
    proposal = plan(baseline.read_text(), layout.read_text(), kind)
    extracted = Path('runs/extracted-timing/final/nl/tt_um_tripwire.nl.v')
    if logical_cells(baseline.read_text()) != logical_cells(extracted.read_text()):
        raise ValueError('Residual DRT/exported topology mismatch')
    targets = Path('workflow-src/scripts/ci/clock8_residual_targets.tcl')
    if targets.exists():
        raise ValueError('Refusing repeated residual targets')
    targets.write_text(target_call(baseline.read_text(), layout.read_text(), kind))
    # Step configs omit synthesis/resizer variables; use the audited full recipe.
    config = json.loads(Path('src/config_native_stock.json').read_text())
    if config.get('GRT_RESIZER_HOLD_SLACK_MARGIN') != 0.10:
        raise ValueError('Native hold target mismatch')
    config['GRT_ALLOW_CONGESTION'] = False
    output = Path('runs/fanout-setup-screen')
    output.mkdir(exist_ok=False)
    (output / 'proposal.json').write_text(json.dumps(proposal, indent=2) + '\n')
    # Build only after source/hash checks, keeping the pinned flow image base.
    import subprocess
    subprocess.run(['docker', 'build', '-t', 'tripwire-clock8-residual:local',
                    '-f', 'workflow-src/scripts/ci/Dockerfile.openroad-clock8-residual',
                    'workflow-src/scripts/ci'], check=True)
    os.environ['LIBRELANE_IMAGE_OVERRIDE'] = 'tripwire-clock8-residual:local'
    grt = output / 'grt'
    run_step(config, source, grt, ['OpenROAD.GlobalRouting'])
    paths = list(grt.glob('*-openroad-globalrouting/state_out.json'))
    if len(paths) != 1:
        raise ValueError('Fresh native GRT missing')
    log = (paths[0].parent / 'openroad-globalrouting.log').read_text()
    if log.count('TRIPWIRE native hold100 setup:') != proposal['repair_receipts']:
        raise ValueError('Missing or repeated native sizing receipt')
    resets = re.findall(r'TRIPWIRE native route reset: cleared ([0-9]+) ordinary routed wires', log)
    if len(resets) != 1 or int(resets[0]) == 0:
        raise ValueError('Missing or ambiguous native detailed-wire reset')
    validate_overflow(log)
    changed = promote(paths[0], baseline, layout, proposal)
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
    path = Path('src/config_clock8_residual_' + kind + '.json')
    path.write_text(json.dumps(config, indent=2) + '\n')
    screen(path, checked, output / 'timing', os.environ['PDK_ROOT'],
           repaired=checked, sdc=Path('src/signoff.sdc'))
    timing = json.loads((output / 'timing/comparison.json').read_text())
    ready = qualified(timing, metrics)
    (output / 'gates.json').write_text(json.dumps(dict(source_run=run['id'],
        kind=kind, changed_cells=proposal['changed_cells'], added_buffers=0, qualified=ready, minimum_fast_hold_ns=0.05,
        physical_screen_only=True, official_signoff=False), indent=2) + '\n')
    if not ready:
        raise ValueError('Native strength screen fails timing/hold/antenna gates')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=['setup'], required=True)
    main(parser.parse_args().kind)
