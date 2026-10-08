#!/usr/bin/env python3
"""Qualify the exact native AREA1 checkpoint, route, then extract timing."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from event_nor2_screen import validate_overflow
from native_stock_screen import checkpoint, configure
from postgrt_timing import CORNERS, screen

SOURCE_RUN = 37853023857
SOURCE_SHA = 'a53dd57b44438d2a10f3363e1418d489a175397e'


def fingerprints(root):
    files = [root / 'info.yaml']
    for folder in ('src', 'macro'):
        files.extend(p for p in (root / folder).rglob('*') if p.is_file())
    if not (root / 'src/trw_defs.vh').is_file():
        raise ValueError('Missing candidate hardware')
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files)}


def validate_source(run, recipe, config, expected, actual):
    if (run['id'] != SOURCE_RUN or run['conclusion'] != 'success'
            or run['head_branch'] != 'main' or run['head_sha'] != SOURCE_SHA
            or run['path'] != '.github/workflows/gds-native-stock-screen.yaml'):
        raise ValueError('Wrong native source provenance')
    if (recipe.get('synthesis_strategy') != 'AREA 1'
            or recipe.get('source_variant') != 'bs-event-late'
            or recipe.get('stock_sequence') is not True
            or recipe.get('checkpoint_ecos') is not False
            or recipe.get('repair_corners') != list(CORNERS)
            or recipe.get('hold_target_ns') != 0.125):
        raise ValueError('Wrong native recipe')
    if (config['CLOCK_PERIOD'] != 20 or config['PL_TARGET_DENSITY_PCT'] != 56
            or config['SYNTH_STRATEGY'] != 'AREA 1' or config['GRT_ADJUSTMENT'] != 0.16
            or config['RSZ_CORNERS'] != list(CORNERS)
            or config.get('RUN_POST_GRT_RESIZER_TIMING') is not True
            or config['GRT_RESIZER_HOLD_SLACK_MARGIN'] != 0.125
            or Path(config['PNR_SDC_FILE']).resolve() != Path('src/signoff.sdc').resolve()
            or Path(config['SIGNOFF_SDC_FILE']).resolve() != Path('src/signoff.sdc').resolve()):
        raise ValueError('Wrong native physical config')
    # Generated configs vary; trusted comparison covers RTL, macro views and SDCs.
    def hardware(values):
        return {k: v for k, v in values.items()
                if not (k.startswith('src/config') and k.endswith('.json'))}
    if hardware(expected) != hardware(actual):
        raise ValueError('Native hardware/constraints fingerprint mismatch')


def qualified(timing, antenna):
    for corner in CORNERS:
        row = timing['corners'][corner]['after']
        for kind in ('setup', 'hold'):
            value = row[f'timing__{kind}__ws__corner:{corner}']
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                return False
        if corner == CORNERS[0] and row[f'timing__hold__ws__corner:{corner}'] < 0.05:
            return False
    return (antenna.get('antenna__violating__nets') == 0
            and antenna.get('antenna__violating__pins') == 0)


def run_step(config, source, output, steps):
    cfg = dict(config)
    cfg['meta'] = {'version': 1, 'flow': steps}
    path = Path('src/config_native_' + output.name + '.json')
    path.write_text(json.dumps(cfg, indent=2) + '\n')
    output.mkdir(parents=True, exist_ok=False)
    subprocess.run([sys.executable, '-m', 'librelane', '--pdk-root', os.environ['PDK_ROOT'],
                    '--docker-no-tty', '--dockerized', '--pdk', 'ihp-sg13cmos5l',
                    '--manual-pdk', '--run-tag', output.name, '--force-run-dir', str(output),
                    '--hide-progress-bar', '--with-initial-state', str(source), str(path)], check=True)


def main():
    root = Path('runs/native-stock-screen')
    config_path = Path('src/config_native_stock.json')
    config = json.loads(config_path.read_text())
    if config != json.loads(Path('/tmp/native-trusted-config.json').read_text()):
        raise ValueError('Downloaded recipe differs from trusted generated config')
    validate_source(json.loads(Path('/tmp/native-source-run.json').read_text()),
                    json.loads((root / 'recipe.json').read_text()), config,
                    json.loads(Path('/tmp/native-trusted-files.json').read_text()),
                    fingerprints(Path.cwd()))
    source = checkpoint(root / 'flow')
    log = source.parent / 'openroad-resizertimingpostgrt.log'
    validate_overflow(log.read_text())
    out = Path('runs/native-stock-route')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.pop('LIBRELANE_IMAGE_OVERRIDE', None)
    run_step(config, source, out / 'antenna', ['OpenROAD.CheckAntennas'])
    metrics = list((out / 'antenna').glob('*-openroad-checkantennas/or_metrics_out.json'))
    if len(metrics) != 1:
        raise ValueError('Fresh antenna evidence missing')
    antenna = json.loads(metrics[0].read_text())
    screen(config_path, source, out / 'timing', os.environ['PDK_ROOT'],
           repaired=source, sdc=Path('src/signoff.sdc'))
    timing = json.loads((out / 'timing/comparison.json').read_text())
    ready = qualified(timing, antenna)
    (out / 'gates.json').write_text(json.dumps({'source_run': SOURCE_RUN,
        'strategy': 'AREA 1', 'state': str(source), 'qualified': ready,
        'minimum_fast_hold_ns': 0.05, 'official_signoff': False}, indent=2) + '\n')
    if not ready:
        raise ValueError('Fresh timing/50ps hold/antenna gate fails; routing refused')
    run_step(config, source, out / 'drt', ['OpenROAD.DetailedRouting'])
    # Extraction reads config_merged.json; preserve the exact native recipe.
    Path('src/config_merged.json').write_text(json.dumps(config, indent=2) + '\n')
    from extracted_timing import main as extract
    extract(out / 'drt')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        Path('/tmp/native-trusted-files.json').write_text(json.dumps(fingerprints(Path.cwd())))
        expected = configure(json.loads(Path('src/config_merged.json').read_text()),
                             'AREA 1', Path('src/signoff.sdc'))
        Path('/tmp/native-trusted-config.json').write_text(json.dumps(expected))
    else:
        main()
