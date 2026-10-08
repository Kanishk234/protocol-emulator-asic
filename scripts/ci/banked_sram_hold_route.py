#!/usr/bin/env python3
"""Resume only the audited repaired banked checkpoint through guarded DRT."""
import json
import os
from pathlib import Path
import subprocess
import sys

from banked_sram_hold_screen import SOURCE_RUN, VARIANT, qualified, validate_configs
from postgrt_timing import CORNERS, screen
from route_source import validate_identity

REPAIR_RUN = 37690561695


def validate_repair_run(run, run_id):
    if (int(run_id) != REPAIR_RUN or run['id'] != REPAIR_RUN
            or run['conclusion'] != 'success' or run['head_branch'] != 'main'
            or run['path'] != '.github/workflows/gds-banked-sram-hold-screen.yaml'):
        raise ValueError('Unreviewed or unsuccessful repaired source run')


def validate_gate(gates, timing, antenna, expected_state):
    if (gates['source_run_id'] != SOURCE_RUN or gates['variant'] != VARIANT
            or gates['ready_for_route_review'] is not True or gates['drt_launched'] is not False
            or Path(gates['state']).resolve() != expected_state.resolve()
            or Path(timing['after_state']).resolve() != expected_state.resolve()
            or not qualified(timing, antenna)):
        raise ValueError('Repaired source timing/antenna/state gate fails')


def main():
    if (os.environ['SOURCE_VARIANT'] != VARIANT
            or int(os.environ['SOURCE_RUN_ID']) != SOURCE_RUN
            or os.environ.get('PRE_ROUTE_HOLD_TARGET', 'source') != 'source'
            or os.environ.get('REPAIR_POSTANTENNA_HOLD', '0') != '0'):
        raise ValueError('Repaired continuation cannot change source or repeat repair')
    validate_repair_run(json.loads(Path('/tmp/placement-repaired-run.json').read_text()),
                        os.environ['REPAIRED_SOURCE_RUN_ID'])
    root = Path('runs/banked-sram-hold')
    source = root / 'antenna/3-openroad-checkantennas-1/state_out.json'
    timing = json.loads((root / 'postantenna-sta/comparison.json').read_text())
    antenna = json.loads(source.with_name('or_metrics_out.json').read_text())
    validate_gate(json.loads((root / 'gates.json').read_text()), timing, antenna, source)
    state = json.loads(source.read_text())
    for key in ('odb', 'def', 'nl', 'pnl', 'sdc'):
        if not Path(state[key]).is_file():
            raise ValueError(f'Missing repaired checkpoint {key}')
    identity = validate_identity(json.loads((root / 'source_identity.json').read_text()), Path.cwd(), VARIANT)
    expected = validate_identity(json.loads(Path('/tmp/placement-source-identity.json').read_text()), Path.cwd(), VARIANT)
    if identity != expected or identity['source_run_id'] != SOURCE_RUN:
        raise ValueError('Repaired source fingerprints changed')
    placements = list(Path('runs/rtl-grt-screen/flow').glob('*-openroad-globalplacement/config.json'))
    if len(placements) != 1:
        raise ValueError('Missing unique actual placement')
    original = Path('runs/rtl-grt-screen/timing/repair/1-openroad-resizertimingpostgrt/config.json')
    base = json.loads(Path('src/config_rx_screen.json').read_text())
    validate_configs(json.loads(original.read_text()), base, json.loads(placements[0].read_text()))
    out = Path('runs/placement-route')
    out.mkdir(exist_ok=False)
    (out / 'source_identity.json').write_text(json.dumps(identity, indent=2) + '\n')
    os.environ['LIBRELANE_IMAGE_OVERRIDE'] = 'tripwire-hotspot:local'
    screen(Path('src/config_rx_screen.json'), source, out / 'postantenna-sta', os.environ['PDK_ROOT'],
           repaired=source, sdc=Path('src/signoff.sdc'))
    fresh = json.loads((out / 'postantenna-sta/comparison.json').read_text())
    ready = qualified(fresh, antenna)
    (out / 'gates.json').write_text(json.dumps({'state': str(source),
        'timing_and_antenna_pass': ready, 'repair_run_id': REPAIR_RUN,
        'source_run_id': SOURCE_RUN, 'variant': VARIANT}, indent=2) + '\n')
    if not ready:
        raise ValueError('Fresh repaired timing fails; routing refused')
    base.update(PNR_CORNERS=list(CORNERS), RSZ_CORNERS=list(CORNERS),
                PNR_SDC_FILE=str(Path('src/signoff.sdc').resolve()),
                GRT_ADJUSTMENT=0.16, OPENROAD_THREADS=4, DRT_SAVE_DRC_REPORT_ITERS=5)
    base['meta'] = {'version': base.get('meta', {}).get('version', 1), 'flow': ['OpenROAD.DetailedRouting']}
    path = Path('src/config_banked_repaired_drt.json')
    path.write_text(json.dumps(base, indent=2) + '\n')
    dest = out / 'drt'
    dest.mkdir()
    subprocess.run([sys.executable, '-m', 'librelane', '--pdk-root', os.environ['PDK_ROOT'],
                    '--docker-no-tty', '--dockerized', '--pdk', 'ihp-sg13cmos5l', '--manual-pdk',
                    '--run-tag', 'drt', '--force-run-dir', str(dest), '--hide-progress-bar',
                    '--with-initial-state', str(source), str(path)], check=True)


if __name__ == '__main__':
    main()
