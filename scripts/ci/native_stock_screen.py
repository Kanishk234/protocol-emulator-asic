#!/usr/bin/env python3
"""Clean synthesis through stock post-antenna repair; no checkpoint ECOs."""
import json
import os
from pathlib import Path
import subprocess
import sys

from postgrt_timing import CORNERS, screen
from rtl_grt_screen import native_mapping_strategy


def configure(original, strategy, sdc, design_repair=False, hold_target=0.125):
    if type(design_repair) is not bool:
        raise ValueError('Design repair selection must be boolean')
    if type(hold_target) not in (int, float) or hold_target not in (0.10, 0.125):
        raise ValueError('Unreviewed native hold target')
    native_mapping_strategy('bs-event-late', strategy)
    if strategy is None:
        raise ValueError('Explicit native mapping strategy required')
    if float(original['CLOCK_PERIOD']) != 20 or float(original['PL_TARGET_DENSITY_PCT']) != 56:
        raise ValueError('Unexpected full-candidate clock/density')
    config = dict(original)
    config.update(SYNTH_STRATEGY=strategy, GRT_ADJUSTMENT=0.16,
                  OPENROAD_THREADS=4, PL_OPTIMIZE_MIRRORING=False,
                  PL_TIMING_DRIVEN=True, PL_RESIZER_SETUP_SLACK_MARGIN=0,
                  GRT_RESIZER_SETUP_SLACK_MARGIN=0,
                  GRT_RESIZER_HOLD_SLACK_MARGIN=hold_target,
                  PNR_SDC_FILE=str(sdc.resolve()), SIGNOFF_SDC_FILE=str(sdc.resolve()),
                  PNR_CORNERS=list(CORNERS), RSZ_CORNERS=list(CORNERS),
                  RUN_POST_GRT_RESIZER_TIMING=True)
    # A saved/custom step list would bypass the stock Classic ordering.
    config['meta'] = {'version': original.get('meta', {}).get('version', 1), 'flow': 'Classic'}
    if design_repair:
        config['RUN_POST_GRT_DESIGN_REPAIR'] = True
    return config


def checkpoint(root):
    if list(root.glob('*-openroad-detailedrouting')):
        raise ValueError('Unexpected detailed routing')
    stages = list(root.glob('*-openroad-resizertimingpostgrt/state_out.json'))
    if len(stages) != 1:
        raise ValueError('Exactly one stock post-GRT repair checkpoint required')
    state = json.loads(stages[0].read_text())
    for key in ('odb', 'def', 'nl', 'pnl', 'sdc'):
        if not Path(state[key]).is_file():
            raise ValueError(f'Missing repaired {key}')
    return stages[0]


def main():
    if os.environ['VARIANT'] != 'bs-event-late':
        raise ValueError('Unreviewed source variant')
    original = json.loads(Path('src/config_merged.json').read_text())
    sdc = Path('src/signoff.sdc')
    repair = os.environ.get('NATIVE_DESIGN_REPAIR', '0')
    if repair not in {'0', '1'}:
        raise ValueError('Unknown native design repair selection')
    config = configure(original, os.environ['NATIVE_MAPPING_STRATEGY'], sdc,
                       design_repair=repair == '1',
                       hold_target=float(os.environ.get('NATIVE_HOLD_TARGET', '0.125')))
    path = Path('src/config_native_stock.json')
    path.write_text(json.dumps(config, indent=2) + '\n')
    root = Path('runs/native-stock-screen')
    flow = root / 'flow'
    flow.mkdir(parents=True, exist_ok=False)
    os.environ.pop('LIBRELANE_IMAGE_OVERRIDE', None)
    subprocess.run([sys.executable, '-m', 'librelane', '--pdk-root', os.environ['PDK_ROOT'],
                    '--docker-no-tty', '--dockerized', '--pdk', 'ihp-sg13cmos5l',
                    '--manual-pdk', '--run-tag', 'native-stock', '--force-run-dir', str(flow),
                    '--hide-progress-bar', '--to', 'OpenROAD.ResizerTimingPostGRT', str(path)], check=True)
    source = checkpoint(flow)
    # STA-only rereads of this exact checkpoint; do not invoke another repair.
    screen(path, source, root / 'timing', os.environ['PDK_ROOT'], repaired=source, sdc=sdc)
    (root / 'recipe.json').write_text(json.dumps({
        'source_variant': 'bs-event-late', 'synthesis_strategy': config['SYNTH_STRATEGY'],
        'repair_corners': list(CORNERS),
        'hold_target_ns': config['GRT_RESIZER_HOLD_SLACK_MARGIN'],
        'stock_sequence': True, 'checkpoint_ecos': False,
        'post_grt_design_repair': repair == '1',
        'extracted': False, 'official_signoff': False,
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
