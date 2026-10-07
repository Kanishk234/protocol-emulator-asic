#!/usr/bin/env python3
"""Continue the independently audited placement screen through antenna/DRT."""
import json
import os
from pathlib import Path
import subprocess
import sys

from postgrt_timing import CORNERS, screen
from route_source import validate_identity


def timing_pass(data):
    return all(data['corners'][c]['after'][f'timing__{k}__ws__corner:{c}'] >= 0
               and data['corners'][c]['after'][f'timing__{k}_vio__count__corner:{c}'] == 0
               for c in CORNERS for k in ('setup', 'hold'))


def hold_followup(config_path, state, output, pdk_root):
    """One repair only, with unchanged constraints and every corner checked."""
    screen(config_path, state, output, pdk_root,
           sdc=Path('src/signoff.sdc'), repair_corners=CORNERS)
    followup = json.loads((output / 'comparison.json').read_text())
    if not timing_pass(followup):
        raise ValueError('Bounded timing follow-up still fails timing; routing refused')
    return Path(followup['after_state'])


def postantenna_followup(config_path, state, output, pdk_root, check_antennas):
    """One repair, then independent antenna and timing gates; never retry."""
    repaired = hold_followup(config_path, state, output / 'repair', pdk_root)
    checked = check_antennas(repaired)
    screen(config_path, repaired, output / 'checked-sta', pdk_root,
           repaired=checked, sdc=Path('src/signoff.sdc'))
    data = json.loads((output / 'checked-sta/comparison.json').read_text())
    if not timing_pass(data):
        raise ValueError('Post-repair checkpoint fails timing; routing refused')
    return checked


def hold_only_failure(data):
    return (not timing_pass(data) and all(
        data['corners'][c]['after'][f'timing__setup__ws__corner:{c}'] >= 0
        and data['corners'][c]['after'][f'timing__setup_vio__count__corner:{c}'] == 0
        for c in CORNERS))


def hold_headroom(config_path, state, output, pdk_root, hold_margin=0.10):
    """One bounded repair target; retain the zero setup target."""
    screen(config_path, state, output, pdk_root, sdc=Path('src/signoff.sdc'),
           setup_margin=0.0, repair_corners=CORNERS, hold_margin=hold_margin)
    data = json.loads((output / 'comparison.json').read_text())
    if not timing_pass(data) or data['corners'][CORNERS[0]]['after'][f'timing__hold__ws__corner:{CORNERS[0]}'] < 0.05:
        raise ValueError('Insufficient repaired hold headroom; routing refused')
    return Path(data['after_state'])


def main():
    root = Path('runs/rtl-grt-screen')
    variant = os.environ.get('SOURCE_VARIANT', 'placement')
    if variant not in {'placement', 'lane', 'sram', 'cts', 'bs-resync', 'bs-event-late', 'bs-load-flat', 'bs-event-drop-qual', 'bs-event-rx-timer'}:
        raise ValueError('Unknown route source variant')
    timing_root = root / 'timing' if variant in {'placement', 'cts', 'bs-resync', 'bs-event-late', 'bs-load-flat', 'bs-event-drop-qual', 'bs-event-rx-timer'} else Path('runs/slew-screen')
    comparison = json.loads((timing_root / 'comparison.json').read_text())
    if variant != 'cts' and not timing_pass(comparison):
        raise ValueError('Failing source timing')
    state = Path(comparison['after_state'])
    states = list((timing_root / 'repair').glob('*-openroad-resizertimingpostgrt/state_out.json'))
    if len(states) != 1 or state.resolve() != states[0].resolve():
        raise ValueError('Timing covers the wrong saved state')
    cfg = json.loads(state.with_name('config.json').read_text())
    base = json.loads(Path('src/config_rx_screen.json').read_text())
    for key, value in {'CLOCK_PERIOD': 20, 'PL_TARGET_DENSITY_PCT': 56,
                       'GRT_ADJUSTMENT': 0.16, 'OPENROAD_THREADS': 4,
                       'PL_TIMING_DRIVEN': True, 'PL_OPTIMIZE_MIRRORING': False}.items():
        if base[key] != value:
            raise ValueError(f'Wrong saved {key}')
    placement = list((root / 'flow').glob('*-openroad-globalplacement/config.json'))
    if len(placement) != 1 or json.loads(placement[0].read_text())['PL_TIMING_DRIVEN'] is not True:
        raise ValueError('Missing actual timing-driven placement evidence')
    if set(cfg['RSZ_CORNERS']) != set(CORNERS):
        raise ValueError('Source repair must load every corner')
    if Path(cfg['PNR_SDC_FILE']).resolve() != Path('src/signoff.sdc').resolve():
        raise ValueError('Wrong constraints')
    for key in ('odb', 'def', 'nl', 'pnl', 'sdc'):
        if not Path(json.loads(state.read_text())[key]).is_file():
            raise ValueError(f'Missing checkpoint {key}')
    if variant in {'lane', 'sram'}:
        netlist = Path(json.loads(state.read_text())['nl']).read_text()
        if f'tripwire_slew_{variant}_buf' not in netlist:
            raise ValueError('Missing selected physical buffer')
    if variant == 'cts':
        cts = list((root / 'flow').glob('*-openroad-cts/config.json'))
        if (len(cts) != 1 or json.loads(cts[0].read_text()).get('CTS_SINK_CLUSTERING_SIZE') != 8
                or base.get('CTS_SINK_CLUSTERING_SIZE') != 8):
            raise ValueError('Wrong clock-clustering source')
    config_path = Path('src/config_rx_screen.json')
    base = json.loads(config_path.read_text())
    out = Path('runs/placement-route')
    out.mkdir(exist_ok=False)
    identity = validate_identity(json.loads(Path('/tmp/placement-source-identity.json').read_text()),
                                 Path.cwd(), variant)
    (out / 'source_identity.json').write_text(json.dumps(identity, indent=2) + '\n')
    os.environ['LIBRELANE_IMAGE_OVERRIDE'] = 'tripwire-hotspot:local'

    if variant == 'cts':
        state = hold_followup(config_path, state, out / 'hold-followup', os.environ['PDK_ROOT'])
    selected_hold = os.environ.get('PRE_ROUTE_HOLD_TARGET', 'source')
    if selected_hold not in {'source', '0.10', '0.15'}:
        raise ValueError('Unknown pre-route hold target')
    if selected_hold != 'source':
        if variant != 'bs-event-late':
            raise ValueError('Hold-headroom experiment is scoped to event-late')
        state = hold_headroom(config_path, state, out / 'hold-headroom', os.environ['PDK_ROOT'],
                              hold_margin=float(selected_hold))

    def run(tag, steps, source):
        config = dict(base)
        config['meta'] = {'version': base.get('meta', {}).get('version', 1), 'flow': steps}
        config['PNR_CORNERS'] = list(CORNERS)
        config['RSZ_CORNERS'] = list(CORNERS)
        config['DRT_SAVE_DRC_REPORT_ITERS'] = 5
        path = Path(f'src/config_placement_{tag}.json')
        path.write_text(json.dumps(config, indent=2) + '\n')
        dest = out / tag
        dest.mkdir()
        subprocess.run([sys.executable, '-m', 'librelane', '--pdk-root', os.environ['PDK_ROOT'],
                        '--docker-no-tty', '--dockerized', '--pdk', 'ihp-sg13cmos5l', '--manual-pdk',
                        '--run-tag', tag, '--force-run-dir', str(dest), '--hide-progress-bar',
                        '--with-initial-state', str(source), str(path)], check=True)
        return dest

    antenna = run('antenna', ['OpenROAD.CheckAntennas', 'OpenROAD.RepairAntennas',
                             'OpenROAD.CheckAntennas'], state)
    states = list(antenna.glob('*-openroad-checkantennas-1/state_out.json'))
    if len(states) != 1:
        raise ValueError('Missing final antenna check')
    final = states[0]
    metrics = json.loads(final.with_name('or_metrics_out.json').read_text())
    if metrics['antenna__violating__nets'] or metrics['antenna__violating__pins']:
        raise ValueError('Dirty antenna checkpoint')
    screen(config_path, state, out / 'postantenna-sta', os.environ['PDK_ROOT'],
           repaired=final, sdc=Path('src/signoff.sdc'))
    data = json.loads((out / 'postantenna-sta/comparison.json').read_text())
    ready = timing_pass(data)
    if not ready and os.environ.get('REPAIR_POSTANTENNA_HOLD', '0') == '1':
        if not hold_only_failure(data):
            raise ValueError('Post-antenna setup failure; hold recovery refused')
        def check_repaired_antennas(repaired):
            checked_root = run('antenna-recheck', ['OpenROAD.CheckAntennas'], repaired)
            checked_states = list(checked_root.glob('*-openroad-checkantennas/state_out.json'))
            if len(checked_states) != 1:
                raise ValueError('Missing post-repair antenna check')
            checked = checked_states[0]
            checked_metrics = json.loads(checked.with_name('or_metrics_out.json').read_text())
            if checked_metrics['antenna__violating__nets'] or checked_metrics['antenna__violating__pins']:
                raise ValueError('Post-repair antennas fail; routing refused')
            return checked
        recovery = out / 'postantenna-hold-followup'
        recovery.mkdir()
        final = postantenna_followup(config_path, final, recovery, os.environ['PDK_ROOT'],
                                     check_repaired_antennas)
        data = json.loads((recovery / 'checked-sta/comparison.json').read_text())
        ready = timing_pass(data)
    (out / 'gates.json').write_text(json.dumps({'timing_and_antenna_pass': ready,
                                             'state': str(final)}, indent=2) + '\n')
    if not ready:
        raise ValueError('Antenna repair regressed timing; detailed routing refused')
    run('drt', ['OpenROAD.DetailedRouting'], final)


if __name__ == '__main__':
    main()
