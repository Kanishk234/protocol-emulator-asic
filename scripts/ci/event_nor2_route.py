#!/usr/bin/env python3
"""Prepared continuation for a qualified NOR2 screen; never repeat sizing."""
import json
import os
from pathlib import Path
import subprocess
import sys

from event_nor2_screen import SOURCE_RUN, VARIANT, ROUTE_RUN, validate_overflow, validate_antenna_overflow, validate_netlist, validate_physical_baseline, validate_antenna_only_changes
from placement_route import timing_pass
from postgrt_timing import CORNERS, screen
from route_source import validate_identity

SCREEN_RUN = 37736921949


def validate_run(run, selected):
    if (int(selected) != SCREEN_RUN or run['id'] != SCREEN_RUN
            or run['conclusion'] != 'success' or run['head_branch'] != 'main'
            or run['path'] != '.github/workflows/gds-event-nor2-screen.yaml'):
        raise ValueError('Unqualified NOR2 screen provenance')


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


def main():
    if (os.environ['SOURCE_VARIANT'] != VARIANT
            or int(os.environ['SOURCE_RUN_ID']) != SOURCE_RUN
            or os.environ.get('PRE_ROUTE_HOLD_TARGET', 'source') != 'source'
            or os.environ.get('REPAIR_POSTANTENNA_HOLD', '0') != '0'):
        raise ValueError('NOR2 continuation cannot change source or repeat repair')
    validate_run(json.loads(Path('/tmp/placement-repaired-run.json').read_text()),
                 os.environ['REPAIRED_SOURCE_RUN_ID'])
    root = Path('runs/event-nor2')
    source = root / 'antenna/3-openroad-checkantennas-1/eco_state.json'
    antenna = json.loads(source.with_name('or_metrics_out.json').read_text())
    timing = json.loads((root / 'timing/comparison.json').read_text())
    gates = json.loads((root / 'gates.json').read_text())
    if gates['antenna_repair_requested'] is not True:
        raise ValueError('Missing reviewed antenna cleanup')
    validate_gate(gates, timing, antenna, source)
    validate_overflow((root / 'grt/1-openroad-globalrouting/openroad-globalrouting.log').read_text())
    validate_antenna_overflow((root / 'antenna/2-openroad-repairantennas/1-openroad-diodeinsertion/openroad-diodeinsertion.log').read_text())
    state = json.loads(source.read_text())
    for key in ('odb', 'def', 'nl', 'pnl', 'sdc'):
        if not Path(state[key]).is_file():
            raise ValueError(f'Missing NOR2 checkpoint {key}')
    original = Path(json.loads(Path('runs/placement-route/antenna/3-openroad-checkantennas-1/state_out.json').read_text())['nl'])
    baseline = root / 'grt/1-openroad-globalrouting/tt_um_tripwire.baseline.nl.v'
    validate_physical_baseline(original.read_text(), baseline.read_text())
    grt_nl = root / 'grt/1-openroad-globalrouting/tt_um_tripwire.eco.nl.v'
    validate_netlist(baseline.read_text(), grt_nl.read_text())
    validate_antenna_only_changes(grt_nl.read_text(), Path(state['nl']).read_text())
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
    # Ordinary image: the one-cell repair is already present and must not repeat.
    os.environ['LIBRELANE_IMAGE_OVERRIDE'] = 'tripwire-hotspot:local'
    screen(config_path, source, out / 'event-nor2-sta', os.environ['PDK_ROOT'],
           repaired=source, sdc=Path('src/signoff.sdc'))
    fresh = json.loads((out / 'event-nor2-sta/comparison.json').read_text())
    ready = qualified(fresh, antenna)
    (out / 'gates.json').write_text(json.dumps({'state': str(source),
        'timing_and_antenna_pass': ready, 'nor2_screen_run': SCREEN_RUN}, indent=2) + '\n')
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
