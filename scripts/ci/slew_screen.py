#!/usr/bin/env python3
"""Independent branch split screen; never detailed-route or modify RTL."""
import json
import os
from pathlib import Path
from postgrt_timing import CORNERS, screen
from placement_route import timing_pass


def main():
    if os.environ['VARIANT'] not in {'none', 'lane', 'sram'}:
        raise ValueError('Unknown isolated slew variant')
    root = Path('runs/rtl-grt-screen')
    data = json.loads((root / 'timing/comparison.json').read_text())
    if not timing_pass(data):
        raise ValueError('Failing original placement timing')
    states = list((root / 'timing/repair').glob('*-openroad-resizertimingpostgrt/state_out.json'))
    if len(states) != 1 or states[0].resolve() != Path(data['after_state']).resolve():
        raise ValueError('Wrong measured source state')
    config = Path('src/config_rx_screen.json')
    cfg = json.loads(config.read_text())
    if cfg['PL_TIMING_DRIVEN'] is not True or cfg['PL_OPTIMIZE_MIRRORING'] is not False:
        raise ValueError('Wrong placement source')
    if cfg['CLOCK_PERIOD'] != 20 or cfg['PL_TARGET_DENSITY_PCT'] != 56:
        raise ValueError('Wrong clock/density')
    for key in ('odb', 'def', 'nl', 'pnl', 'sdc'):
        if not Path(json.loads(states[0].read_text())[key]).is_file():
            raise ValueError(f'Missing saved {key}')
    os.environ['LIBRELANE_IMAGE_OVERRIDE'] = 'tripwire-hotspot:local'
    screen(config, states[0], Path('runs/slew-screen'), os.environ['PDK_ROOT'],
           sdc=Path('src/signoff.sdc'), setup_margin=0, repair_corners=CORNERS)


if __name__ == '__main__':
    main()
