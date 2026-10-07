#!/usr/bin/env python3
"""One exact SRAM-branch repair with fresh timing/antenna gates, never DRT."""
import json
import os
from pathlib import Path
import subprocess
import sys

from placement_route import timing_pass
from postgrt_timing import CORNERS, screen
from route_source import validate_identity

SOURCE_RUN = 37669663762
VARIANT = 'bs-event-pin-banked'


def validate_source(data, run_id):
    if int(run_id) != SOURCE_RUN:
        raise ValueError('Unreviewed SRAM branch checkpoint')
    for corner in CORNERS:
        row = data['corners'][corner]['after']
        if (row[f'timing__setup__ws__corner:{corner}'] < 0
                or row[f'timing__setup_vio__count__corner:{corner}'] != 0):
            raise ValueError('Source setup failure')
        slack = row[f'timing__hold__ws__corner:{corner}']
        count = row[f'timing__hold_vio__count__corner:{corner}']
        if corner == CORNERS[0]:
            if not (-0.025 <= slack < 0 and count == 1):
                raise ValueError('Unexpected fast hold residual')
        elif slack < 0 or count != 0:
            raise ValueError('Unexpected secondary hold failure')


def qualified(data, antenna):
    return (timing_pass(data)
            and data['corners'][CORNERS[0]]['after'][f'timing__hold__ws__corner:{CORNERS[0]}'] >= 0.05
            and antenna['antenna__violating__nets'] == 0
            and antenna['antenna__violating__pins'] == 0)


def main():
    if os.environ['SOURCE_VARIANT'] != VARIANT:
        raise ValueError('Unexpected SRAM branch source variant')
    root = Path('runs/rtl-grt-screen/timing')
    data = json.loads((root / 'comparison.json').read_text())
    validate_source(data, os.environ['SOURCE_RUN_ID'])
    source = Path(data['after_state'])
    states = list((root / 'repair').glob('*-openroad-resizertimingpostgrt/state_out.json'))
    if len(states) != 1 or source.resolve() != states[0].resolve():
        raise ValueError('Unexpected repaired source checkpoint')
    cfg = json.loads(source.with_name('config.json').read_text())
    for key, value in {'CLOCK_PERIOD': 20, 'GRT_ADJUSTMENT': 0.16,
                       'PL_TARGET_DENSITY_PCT': 56, 'PL_OPTIMIZE_MIRRORING': False}.items():
        if cfg[key] != value:
            raise ValueError(f'Unexpected source {key}')
    if Path(cfg['PNR_SDC_FILE']).resolve() != Path('src/signoff.sdc').resolve():
        raise ValueError('Source constraints changed')
    identity = validate_identity(json.loads(Path('/tmp/placement-source-identity.json').read_text()),
                                 Path.cwd(), VARIANT)
    if identity['source_run_id'] != SOURCE_RUN:
        raise ValueError('Source fingerprint run changed')
    out = Path('runs/banked-sram-hold')
    out.mkdir(exist_ok=False)
    (out / 'source_identity.json').write_text(json.dumps(identity, indent=2) + '\n')
    os.environ['LIBRELANE_IMAGE_OVERRIDE'] = 'tripwire-banked-hold:local'
    config_path = Path('src/config_rx_screen.json')
    screen(config_path, source, out / 'timing', os.environ['PDK_ROOT'],
           sdc=Path('src/signoff.sdc'), setup_margin=0.0,
           repair_corners=CORNERS, hold_margin=0.125)
    repaired = Path(json.loads((out / 'timing/comparison.json').read_text())['after_state'])
    log = repaired.with_name('openroad-resizertimingpostgrt.log').read_text()
    if ('TRIPWIRE address hold: net9161' not in log
            or 'TRIPWIRE hotspot screen:' not in log):
        raise ValueError('Missing physical insertion or region reservation evidence')
    config = json.loads(config_path.read_text())
    config.update(PNR_CORNERS=list(CORNERS), RSZ_CORNERS=list(CORNERS),
                  PNR_SDC_FILE=str(Path('src/signoff.sdc').resolve()),
                  GRT_ADJUSTMENT=0.16, OPENROAD_THREADS=4)
    config['meta'] = {'version': config.get('meta', {}).get('version', 1),
                      'flow': ['OpenROAD.CheckAntennas', 'OpenROAD.RepairAntennas', 'OpenROAD.CheckAntennas']}
    path = Path('src/config_banked_hold_antenna.json')
    path.write_text(json.dumps(config, indent=2) + '\n')
    antenna_root = out / 'antenna'
    antenna_root.mkdir()
    subprocess.run([sys.executable, '-m', 'librelane', '--pdk-root', os.environ['PDK_ROOT'],
                    '--docker-no-tty', '--dockerized', '--pdk', 'ihp-sg13cmos5l', '--manual-pdk',
                    '--run-tag', 'antenna', '--force-run-dir', str(antenna_root), '--hide-progress-bar',
                    '--with-initial-state', str(repaired), str(path)], check=True)
    final = antenna_root / '3-openroad-checkantennas-1/state_out.json'
    antenna = json.loads(final.with_name('or_metrics_out.json').read_text())
    screen(config_path, repaired, out / 'postantenna-sta', os.environ['PDK_ROOT'],
           repaired=final, sdc=Path('src/signoff.sdc'))
    timing = json.loads((out / 'postantenna-sta/comparison.json').read_text())
    ready = qualified(timing, antenna)
    (out / 'gates.json').write_text(json.dumps({'state': str(final), 'ready_for_route_review': ready,
        'drt_launched': False, 'source_run_id': SOURCE_RUN, 'variant': VARIANT}, indent=2) + '\n')
    if list(out.glob('**/*-openroad-detailedrouting')):
        raise ValueError('Unexpected detailed routing')
    if not ready:
        raise ValueError('Repair fails timing/headroom or antennas; routing remains blocked')
    print('Repair-only all-corner/50ps/antenna gates pass; detailed routing not launched')


if __name__ == '__main__':
    main()
