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
PROFILES = {
    'stock125': (SOURCE_RUN, SOURCE_SHA, 'gds-native-stock-screen', 0.125),
    'hold100': (37866086829, '7b87718f0b28be7c5815cded40db05eb52c27be8',
                'gds-native-hold100-screen', 0.10),
    'clock8': (37990280838, 'dfe1a9f46d9b97d20550d1326fb7755cbe2829cf',
               'gds-native-clock8-screen', 0.10),
}


def profile_values(profile):
    if profile not in PROFILES:
        raise ValueError('Unqualified native route profile')
    return PROFILES[profile]


def fingerprints(root):
    files = [root / 'info.yaml']
    for folder in ('src', 'macro'):
        files.extend(p for p in (root / folder).rglob('*') if p.is_file())
    if not (root / 'src/trw_defs.vh').is_file():
        raise ValueError('Missing candidate hardware')
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files)}


def validate_source(run, recipe, config, expected, actual, profile='stock125'):
    run_id, sha, workflow, hold_target = profile_values(profile)
    if profile == 'clock8' and (recipe.get('clock_sink_clustering_size') != 8
                               or recipe.get('post_grt_design_repair') is not False
                               or config.get('CTS_SINK_CLUSTERING_SIZE') != 8
                               or config.get('CTS_SINK_CLUSTERING_ENABLE', True) is not True):
        raise ValueError('Wrong native clock clustering recipe')
    if (run['id'] != run_id or run['conclusion'] != 'success'
            or run['head_branch'] != 'main' or run['head_sha'] != sha
            or run['path'] != f'.github/workflows/{workflow}.yaml'):
        raise ValueError('Wrong native source provenance')
    if (recipe.get('synthesis_strategy') != 'AREA 1'
            or recipe.get('source_variant') != 'bs-event-late'
            or recipe.get('stock_sequence') is not True
            or recipe.get('checkpoint_ecos') is not False
            or recipe.get('repair_corners') != list(CORNERS)
            or recipe.get('hold_target_ns') != hold_target):
        raise ValueError('Wrong native recipe')
    if (config['CLOCK_PERIOD'] != 20 or config['PL_TARGET_DENSITY_PCT'] != 56
            or config['SYNTH_STRATEGY'] != 'AREA 1' or config['GRT_ADJUSTMENT'] != 0.16
            or config['RSZ_CORNERS'] != list(CORNERS)
            or config.get('RUN_POST_GRT_RESIZER_TIMING') is not True
            or config['GRT_RESIZER_HOLD_SLACK_MARGIN'] != hold_target
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
    profile = os.environ.get('NATIVE_ROUTE_PROFILE', 'stock125')
    run_id, _, _, _ = profile_values(profile)
    root = Path('runs/native-stock-screen')
    config_path = Path('src/config_native_stock.json')
    config = json.loads(config_path.read_text())
    if config != json.loads(Path('/tmp/native-trusted-config.json').read_text()):
        raise ValueError('Downloaded recipe differs from trusted generated config')
    validate_source(json.loads(Path('/tmp/native-source-run.json').read_text()),
                    json.loads((root / 'recipe.json').read_text()), config,
                    json.loads(Path('/tmp/native-trusted-files.json').read_text()),
                    fingerprints(Path.cwd()), profile=profile)
    source = checkpoint(root / 'flow')
    log = source.parent / 'openroad-resizertimingpostgrt.log'
    validate_overflow(log.read_text())
    out = Path('runs/native-clock8-route' if profile == 'clock8' else 'runs/native-stock-route')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.pop('LIBRELANE_IMAGE_OVERRIDE', None)
    run_step(config, source, out / 'antenna', ['OpenROAD.CheckAntennas'])
    metrics = list((out / 'antenna').glob('*-openroad-checkantennas/or_metrics_out.json'))
    if len(metrics) != 1:
        raise ValueError('Fresh antenna evidence missing')
    antenna = json.loads(metrics[0].read_text())
    if antenna.get('antenna__violating__nets', 0) or antenna.get('antenna__violating__pins', 0):
        # Stock timing repair runs after stock antenna repair and can introduce
        # new violations. Preserve repaired guides (BUG79): do not run another
        # full GRT after cleanup. Require congestion-disallowed stock repair.
        print('Post-timing antenna violations:', antenna, flush=True)
        cleanup = out / 'antenna-cleanup'
        cleanup_config = dict(config, GRT_ALLOW_CONGESTION=False)
        run_step(cleanup_config, source, cleanup, ['OpenROAD.RepairAntennas', 'OpenROAD.CheckAntennas'])
        resolved = json.loads((cleanup / 'resolved.json').read_text())
        repair_logs = list(cleanup.glob('*-openroad-repairantennas/*-openroad-diodeinsertion/openroad-diodeinsertion.log'))
        states = list(cleanup.glob('*-openroad-checkantennas/state_out.json'))
        fresh_metrics = list(cleanup.glob('*-openroad-checkantennas/or_metrics_out.json'))
        if len(repair_logs) != 1 or len(states) != 1 or len(fresh_metrics) != 1:
            raise ValueError('Fresh post-cleanup routing/antenna checkpoint missing')
        log = repair_logs[0].read_text()
        if (resolved.get('GRT_ALLOW_CONGESTION') is not False
                or 'repair_antennas' not in log or '-allow_congestion' in log):
            raise ValueError('Antenna repair congestion policy not enforced')
        source = states[0]
        antenna = json.loads(fresh_metrics[0].read_text())
    screen(config_path, source, out / 'timing', os.environ['PDK_ROOT'],
           repaired=source, sdc=Path('src/signoff.sdc'))
    timing = json.loads((out / 'timing/comparison.json').read_text())
    ready = qualified(timing, antenna)
    (out / 'gates.json').write_text(json.dumps({'source_run': run_id, 'profile': profile,
        'strategy': 'AREA 1', 'state': str(source), 'qualified': ready,
        'minimum_fast_hold_ns': 0.05, 'official_signoff': False}, indent=2) + '\n')
    if not ready:
        raise ValueError(f'Fresh timing/50ps hold/antenna gate fails; routing refused: {antenna}')
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
        _, _, _, hold_target = profile_values(os.environ.get('NATIVE_ROUTE_PROFILE', 'stock125'))
        Path('/tmp/native-trusted-files.json').write_text(json.dumps(fingerprints(Path.cwd())))
        expected = configure(json.loads(Path('src/config_merged.json').read_text()),
                             'AREA 1', Path('src/signoff.sdc'), hold_target=hold_target,
                             clock_cluster=8 if os.environ.get('NATIVE_ROUTE_PROFILE') == 'clock8' else None)
        Path('/tmp/native-trusted-config.json').write_text(json.dumps(expected))
    else:
        main()
