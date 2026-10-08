#!/usr/bin/env python3
"""Continue qualified NOR2 or leaf-hold checkpoints without repeating repairs."""
import json
import os
from pathlib import Path
import subprocess
import sys

from event_nor2_screen import SOURCE_RUN, VARIANT, ROUTE_RUN, validate_overflow, validate_antenna_overflow, validate_netlist, validate_physical_baseline, validate_antenna_only_changes, validate_drop_netlist, logical_cells
from placement_route import timing_pass
from postgrt_timing import CORNERS, screen
from route_source import validate_identity

SCREEN_RUN = 37736921949
HOLD_SCREEN_RUN = 37806209914
DRIVER_SCREEN_RUN = 37818177484
RESIDUAL_SCREEN_RUN = 37834700367


def validate_run(run, selected):
    sources = {SCREEN_RUN: ('nor2', 'gds-event-nor2-screen'),
               HOLD_SCREEN_RUN: ('hold', 'gds-drop-leaf-hold-screen'),
               DRIVER_SCREEN_RUN: ('driver', 'gds-drop-driver-screen'),
               RESIDUAL_SCREEN_RUN: ('residual', 'gds-residual-setup-screen')}
    if int(selected) not in sources:
        raise ValueError('Unqualified NOR2 screen provenance')
    profile, workflow = sources[int(selected)]
    if (run['id'] != int(selected)
            or run['conclusion'] != 'success' or run['head_branch'] != 'main'
            or run['path'] != f'.github/workflows/{workflow}.yaml'):
        raise ValueError('Unqualified NOR2 screen provenance')
    return profile


def qualified(timing, antenna):
    return (timing_pass(timing)
            and timing['corners'][CORNERS[0]]['after'][f'timing__hold__ws__corner:{CORNERS[0]}'] >= 0.05
            and antenna['antenna__violating__nets'] == 0
            and antenna['antenna__violating__pins'] == 0)


def validate_gate(gates, timing, antenna, source):
    if (gates['source_route'] != ROUTE_RUN or gates['ready_for_route_review'] is not True
            or gates['drt_launched'] is not False
            or Path(gates['state']).resolve() != source.resolve()
            or Path(timing['after_state']).resolve() != source.resolve()
            or not qualified(timing, antenna)):
        raise ValueError('NOR2 timing/50ps/antenna/checkpoint gate fails')


def validate_hold_history(gates):
    if (gates.get('eco_profile') != 'drop-hold'
            or gates.get('source_screen') != 37803300460
            or gates.get('minimum_fast_hold_ns') != 0.05
            or gates.get('fast_hold_margin_pass') is not True):
        raise ValueError('Unreviewed hold checkpoint history or margin policy')


def validate_driver_history(gates):
    if (gates.get('eco_profile') != 'drop-driver'
            or gates.get('source_screen') != HOLD_SCREEN_RUN
            or gates.get('minimum_fast_hold_ns') != 0.05
            or gates.get('fast_hold_margin_pass') is not True):
        raise ValueError('Unreviewed driver checkpoint history or margin policy')


def validate_residual_history(gates):
    if (gates.get('eco_profile') != 'residual-setup'
            or gates.get('source_screen') != DRIVER_SCREEN_RUN
            or gates.get('minimum_fast_hold_ns') != 0.05
            or gates.get('fast_hold_margin_pass') is not True):
        raise ValueError('Unreviewed residual checkpoint history or margin policy')


def validate_repair_chain(root, state, held=False, driver=False, residual=False):
    """Audit every netlist transition; never trust a final netlist in isolation."""
    if residual:
        prior_root = Path('runs/drop-driver')
        prior = json.loads((prior_root / 'antenna/3-openroad-checkantennas-1/eco_state.json').read_text())
        validate_repair_chain(prior_root, prior, driver=True)
        baseline = root / 'grt/1-openroad-globalrouting/tt_um_tripwire.baseline.nl.v'
        if logical_cells(Path(prior['nl']).read_text()) != logical_cells(baseline.read_text()):
            raise ValueError('Residual source snapshot mismatch')
        from event_nor2_screen import validate_residual_netlist
        changed = root / 'grt/1-openroad-globalrouting/tt_um_tripwire.eco.nl.v'
        validate_residual_netlist(baseline.read_text(), changed.read_text())
        validate_antenna_only_changes(changed.read_text(), Path(state['nl']).read_text())
    elif driver:
        prior_root = Path('runs/drop-hold')
        prior = json.loads((prior_root / 'antenna/3-openroad-checkantennas-1/eco_state.json').read_text())
        validate_repair_chain(prior_root, prior, held=True)
        baseline = root / 'grt/1-openroad-globalrouting/tt_um_tripwire.baseline.nl.v'
        if logical_cells(Path(prior['nl']).read_text()) != logical_cells(baseline.read_text()):
            raise ValueError('Driver source snapshot mismatch')
        from event_nor2_screen import validate_driver_netlist
        changed = root / 'grt/1-openroad-globalrouting/tt_um_tripwire.eco.nl.v'
        validate_driver_netlist(baseline.read_text(), changed.read_text())
        validate_antenna_only_changes(changed.read_text(), Path(state['nl']).read_text())
    elif held:
        prior_root = Path('runs/event-nor2')
        prior = json.loads((prior_root / 'antenna/3-openroad-checkantennas-1/eco_state.json').read_text())
        validate_repair_chain(prior_root, prior)
        drop_root = Path('runs/drop-event')
        drop_base = drop_root / 'grt/1-openroad-globalrouting/tt_um_tripwire.baseline.nl.v'
        if logical_cells(Path(prior['nl']).read_text()) != logical_cells(drop_base.read_text()):
            raise ValueError('Dropped-event source snapshot mismatch')
        drop_nl = drop_root / 'grt/1-openroad-globalrouting/tt_um_tripwire.eco.nl.v'
        validate_drop_netlist(drop_base.read_text(), drop_nl.read_text())
        drop_state = json.loads((drop_root / 'antenna/3-openroad-checkantennas-1/eco_state.json').read_text())
        validate_antenna_only_changes(drop_nl.read_text(), Path(drop_state['nl']).read_text())
        hold_base = root / 'grt/1-openroad-globalrouting/tt_um_tripwire.baseline.nl.v'
        if logical_cells(Path(drop_state['nl']).read_text()) != logical_cells(hold_base.read_text()):
            raise ValueError('Hold source snapshot mismatch')
        hold_nl = root / 'grt/1-openroad-globalrouting/tt_um_tripwire.eco.nl.v'
        from drop_leaf_hold import validate_drop_leaf_hold
        validate_drop_leaf_hold(hold_base.read_text(), hold_nl.read_text())
        validate_antenna_only_changes(hold_nl.read_text(), Path(state['nl']).read_text())
    else:
        original = Path(json.loads(Path('runs/placement-route/antenna/3-openroad-checkantennas-1/state_out.json').read_text())['nl'])
        baseline = root / 'grt/1-openroad-globalrouting/tt_um_tripwire.baseline.nl.v'
        validate_physical_baseline(original.read_text(), baseline.read_text())
        grt_nl = root / 'grt/1-openroad-globalrouting/tt_um_tripwire.eco.nl.v'
        validate_netlist(baseline.read_text(), grt_nl.read_text())
        validate_antenna_only_changes(grt_nl.read_text(), Path(state['nl']).read_text())


def main():
    if (os.environ['SOURCE_VARIANT'] != VARIANT
            or int(os.environ['SOURCE_RUN_ID']) != SOURCE_RUN
            or os.environ.get('PRE_ROUTE_HOLD_TARGET', 'source') != 'source'
            or os.environ.get('REPAIR_POSTANTENNA_HOLD', '0') != '0'):
        raise ValueError('NOR2 continuation cannot change source or repeat repair')
    profile = validate_run(json.loads(Path('/tmp/placement-repaired-run.json').read_text()),
                           os.environ['REPAIRED_SOURCE_RUN_ID'])
    held = profile == 'hold'
    residual = profile == 'residual'
    driver = profile in {'driver', 'residual'}
    root = Path('runs/residual-setup' if residual else 'runs/drop-driver' if driver else 'runs/drop-hold' if held else 'runs/event-nor2')
    source = root / 'antenna/3-openroad-checkantennas-1/eco_state.json'
    antenna = json.loads(source.with_name('or_metrics_out.json').read_text())
    timing = json.loads((root / 'timing/comparison.json').read_text())
    gates = json.loads((root / 'gates.json').read_text())
    if gates['antenna_repair_requested'] is not True:
        raise ValueError('Missing reviewed antenna cleanup')
    validate_gate(gates, timing, antenna, source)
    if held:
        validate_hold_history(gates)
    if driver:
        (validate_residual_history if residual else validate_driver_history)(gates)
    validate_overflow((root / 'grt/1-openroad-globalrouting/openroad-globalrouting.log').read_text())
    validate_antenna_overflow((root / 'antenna/2-openroad-repairantennas/1-openroad-diodeinsertion/openroad-diodeinsertion.log').read_text())
    state = json.loads(source.read_text())
    for key in ('odb', 'def', 'nl', 'pnl', 'sdc'):
        if not Path(state[key]).is_file():
            raise ValueError(f'Missing NOR2 checkpoint {key}')
    if any(state.get(k) is not None for k in ('spef', 'sdf', 'lib')):
        raise ValueError('Stale repaired checkpoint views')
    validate_repair_chain(root, state, held=held, driver=driver, residual=residual)
    identity = validate_identity(json.loads((root / 'source_identity.json').read_text()), Path.cwd(), VARIANT)
    expected = validate_identity(json.loads(Path('/tmp/placement-source-identity.json').read_text()), Path.cwd(), VARIANT)
    if identity != expected or identity['source_run_id'] != SOURCE_RUN:
        raise ValueError('NOR2 hardware fingerprint mismatch')
    out = Path('runs/placement-route')
    if (out / 'drt').exists():
        raise ValueError('Existing detailed route; overwrite refused')
    config_path = Path('src/config_rx_screen.json')
    base = json.loads(config_path.read_text())
    if (base['CLOCK_PERIOD'] != 20 or base['GRT_ADJUSTMENT'] != 0.16
            or Path(base['PNR_SDC_FILE']).resolve() != Path('src/signoff.sdc').resolve()):
        raise ValueError('NOR2 routing clock/constraints/config changed')
    # Ordinary image: all reviewed repairs are already present and must not repeat.
    os.environ['LIBRELANE_IMAGE_OVERRIDE'] = 'tripwire-hotspot:local'
    sta_root = out / ('residual-setup-sta' if residual else 'drop-driver-sta' if driver else 'hold-leaves-sta' if held else 'event-nor2-sta')
    screen(config_path, source, sta_root, os.environ['PDK_ROOT'],
           repaired=source, sdc=Path('src/signoff.sdc'))
    fresh = json.loads((sta_root / 'comparison.json').read_text())
    ready = qualified(fresh, antenna)
    (out / 'gates.json').write_text(json.dumps({'state': str(source),
        'timing_and_antenna_pass': ready,
        'nor2_screen_run': SCREEN_RUN,
        **({'hold_screen_run': HOLD_SCREEN_RUN} if held or driver else {}),
        **({'driver_screen_run': DRIVER_SCREEN_RUN} if driver else {}),
        **({'residual_screen_run': RESIDUAL_SCREEN_RUN} if residual else {})}, indent=2) + '\n')
    if not ready:
        raise ValueError('Fresh NOR2 timing fails; DRT refused')
    base.update(PNR_CORNERS=list(CORNERS), RSZ_CORNERS=list(CORNERS), OPENROAD_THREADS=4,
                DRT_SAVE_DRC_REPORT_ITERS=5,
                meta={'version': base.get('meta', {}).get('version', 1), 'flow': ['OpenROAD.DetailedRouting']})
    path = Path('src/config_event_nor2_drt.json')
    path.write_text(json.dumps(base, indent=2) + '\n')
    dest = out / 'drt'
    dest.mkdir()
    subprocess.run([sys.executable, '-m', 'librelane', '--pdk-root', os.environ['PDK_ROOT'],
                    '--docker-no-tty', '--dockerized', '--pdk', 'ihp-sg13cmos5l', '--manual-pdk',
                    '--run-tag', 'drt', '--force-run-dir', str(dest), '--hide-progress-bar',
                    '--with-initial-state', str(source), str(path)], check=True)


if __name__ == '__main__':
    main()
