#!/usr/bin/env python3
"""Bounded one-cell ECO with fresh GRT, netlists, antennas and STA; no DRT."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from placement_route import timing_pass
from postgrt_timing import CORNERS, screen
from route_source import validate_identity

ROUTE_RUN = 37574267994
SOURCE_RUN = 37533969613
VARIANT = 'bs-event-late'


def validate_run(run):
    if (run['id'] != ROUTE_RUN or run['head_branch'] != 'main'
            or run['conclusion'] != 'success'
            or run['path'] != '.github/workflows/gds-placement-route.yaml'):
        raise ValueError('Unreviewed original route source')


def logical_cells(text):
    cells = {}
    for master, name, ports in re.findall(r'\b(sg13cmos5l_\w+|RM_IHPSG13_\w+)\s+(\\?\S+)\s*\((.*?)\);', text, re.S):
        if master.startswith(('sg13cmos5l_fill_', 'sg13cmos5l_decap_')):
            continue
        if name in cells:
            raise ValueError('Duplicate mapped cell')
        cells[name] = (master, tuple(sorted(re.findall(r'\.(\w+)\((.*?)\)', ports))))
    if not cells:
        raise ValueError('Missing mapped cells')
    return cells


def validate_netlist(before, after):
    original, changed = logical_cells(before), logical_cells(after)
    expected = ('sg13cmos5l_nor2_1', (('A', '_21095_'), ('B', '_02509_'), ('Y', '_02510_')))
    if original.get('_27853_') != expected:
        raise ValueError('Original cell identity or connectivity changed')
    original['_27853_'] = ('sg13cmos5l_nor2_2', expected[1])
    if original != changed:
        raise ValueError('ECO changed additional logical cells or connections')


def validate_physical_baseline(inherited, physical):
    old, exported = logical_cells(inherited), logical_cells(physical)
    added = exported.keys() - old.keys()
    if (len(added) != 92 or any(exported[n][0] != 'sg13cmos5l_antennanp' for n in added)
            or any(exported.get(n) != cell for n, cell in old.items())):
        raise ValueError('Source ODB/netlist differs beyond audited92 antenna cells')


def validate_antenna_only_changes(before, after):
    original, changed = logical_cells(before), logical_cells(after)
    if any(changed.get(n) != cell for n, cell in original.items()):
        raise ValueError('Antenna repair changed existing logical cells or connections')
    nets = {net for _, ports in original.values() for _, net in ports}
    for name in changed.keys() - original.keys():
        master, ports = changed[name]
        if (master != 'sg13cmos5l_antennanp' or len(ports) != 1
                or ports[0][0] != 'A' or ports[0][1] not in nets):
            raise ValueError('Antenna repair added unreviewed logic or wiring')


def validate_overflow(log):
    if 'Final congestion report:' not in log:
        raise ValueError('Missing fresh global routing congestion report')
    final = log.rsplit('Final congestion report:', 1)[1]
    rows = re.findall(r'^\s*(Metal\d+|TopMetal\d+)\s+\d+\s+\d+\s+[\d.]+%\s+(\d+)\s*/\s*(\d+)\s*/\s*(\d+)', final, re.M)
    if not {'Metal1', 'Metal2', 'Metal3', 'Metal4'}.issubset({r[0] for r in rows}):
        raise ValueError('Incomplete fresh routing layer report')
    if any(int(v) for row in rows for v in row[1:]):
        raise ValueError('ECO global routing overflow')


def promote_netlists(state_path, original_netlist):
    state = json.loads(state_path.read_text())
    odb = Path(state['odb'])
    nl = odb.with_suffix('.eco.nl.v')
    pnl = odb.with_suffix('.eco.pnl.v')
    baseline = odb.with_suffix('.baseline.nl.v')
    if not nl.is_file() or not pnl.is_file() or not baseline.is_file():
        raise ValueError('Fresh ECO netlists missing; stale STA refused')
    validate_physical_baseline(original_netlist.read_text(), baseline.read_text())
    validate_netlist(baseline.read_text(), nl.read_text())
    if not re.search(r'\bsg13cmos5l_nor2_2\s+_27853_\s*\(', pnl.read_text()):
        raise ValueError('Powered netlist missing ECO')
    state.update(nl=str(nl), pnl=str(pnl), spef=None, sdf=None, lib=None)
    promoted = state_path.with_name('eco_state.json')
    promoted.write_text(json.dumps(state, indent=2) + '\n')
    return promoted


def promote_antenna_netlists(state_path, original_netlist):
    state = json.loads(state_path.read_text())
    odb = Path(state['odb'])
    nl, pnl = odb.with_suffix('.eco.nl.v'), odb.with_suffix('.eco.pnl.v')
    if not nl.is_file() or not pnl.is_file():
        raise ValueError('Fresh antenna-repaired netlists missing')
    validate_antenna_only_changes(original_netlist.read_text(), nl.read_text())
    if not re.search(r'\bsg13cmos5l_nor2_2\s+_27853_\s*\(', pnl.read_text()):
        raise ValueError('Antenna-repaired powered netlist missing ECO')
    state.update(nl=str(nl), pnl=str(pnl), spef=None, sdf=None, lib=None)
    promoted = state_path.with_name('eco_state.json')
    promoted.write_text(json.dumps(state, indent=2) + '\n')
    return promoted


def main():
    validate_run(json.loads(Path('/tmp/event-nor2-route-run.json').read_text()))
    root = Path('runs/placement-route')
    identity = validate_identity(json.loads((root / 'source_identity.json').read_text()), Path.cwd(), VARIANT)
    expected = validate_identity(json.loads(Path('/tmp/placement-source-identity.json').read_text()), Path.cwd(), VARIANT)
    if identity != expected or identity['source_run_id'] != SOURCE_RUN:
        raise ValueError('Original hardware fingerprints changed')
    gates = json.loads((root / 'gates.json').read_text())
    source = Path(gates['state'])
    timing = json.loads((root / 'postantenna-sta/comparison.json').read_text())
    if (not gates['timing_and_antenna_pass'] or not timing_pass(timing)
            or Path(timing['after_state']).resolve() != source.resolve()
            or source.resolve() != (root / 'antenna/3-openroad-checkantennas-1/state_out.json').resolve()):
        raise ValueError('Original checkpoint timing/state gate fails')
    saved = json.loads(source.read_text())
    for key in ('odb', 'def', 'nl', 'pnl', 'sdc'):
        if not Path(saved[key]).is_file():
            raise ValueError(f'Missing original checkpoint {key}')
    base_path = Path('src/config_rx_screen.json')
    base = json.loads(base_path.read_text())
    for key, value in {'CLOCK_PERIOD': 20, 'PL_TARGET_DENSITY_PCT': 56,
                       'GRT_ADJUSTMENT': 0.16, 'PL_TIMING_DRIVEN': True,
                       'PL_OPTIMIZE_MIRRORING': False}.items():
        if base[key] != value:
            raise ValueError(f'Unexpected source {key}')
    if Path(base['PNR_SDC_FILE']).resolve() != Path('src/signoff.sdc').resolve():
        raise ValueError('Source constraints changed')
    out = Path('runs/event-nor2')
    out.mkdir(exist_ok=False)
    (out / 'source_identity.json').write_text(json.dumps(identity, indent=2) + '\n')
    os.environ['LIBRELANE_IMAGE_OVERRIDE'] = 'tripwire-event-nor2:local'

    def run(tag, steps, initial):
        cfg = dict(base)
        cfg.update(PNR_CORNERS=list(CORNERS), RSZ_CORNERS=list(CORNERS), OPENROAD_THREADS=4,
                   PNR_SDC_FILE=str(Path('src/signoff.sdc').resolve()),
                   meta={'version': base.get('meta', {}).get('version', 1), 'flow': steps})
        path = Path(f'src/config_event_nor2_{tag}.json')
        path.write_text(json.dumps(cfg, indent=2) + '\n')
        dest = out / tag
        dest.mkdir()
        subprocess.run([sys.executable, '-m', 'librelane', '--pdk-root', os.environ['PDK_ROOT'],
                        '--docker-no-tty', '--dockerized', '--pdk', 'ihp-sg13cmos5l', '--manual-pdk',
                        '--run-tag', tag, '--force-run-dir', str(dest), '--hide-progress-bar',
                        '--with-initial-state', str(initial), str(path)], check=True)
        return dest

    routed = run('grt', ['OpenROAD.GlobalRouting'], source)
    state_path = routed / '1-openroad-globalrouting/state_out.json'
    log = state_path.with_name('openroad-globalrouting.log').read_text()
    if 'TRIPWIRE event NOR2:' not in log or 'TRIPWIRE hotspot screen:' not in log:
        raise ValueError('Missing ECO or routing reservation evidence')
    validate_overflow(log)
    changed = promote_netlists(state_path, Path(saved['nl']))
    repair_antennas = os.environ.get('REPAIR_ECO_ANTENNAS', '0')
    if repair_antennas not in {'0', '1'}:
        raise ValueError('Unknown antenna repair selection')
    steps = ['OpenROAD.CheckAntennas']
    if repair_antennas == '1':
        steps += ['OpenROAD.RepairAntennas', 'OpenROAD.CheckAntennas']
    antenna_root = run('antenna', steps, changed)
    checked = antenna_root / ('3-openroad-checkantennas-1/state_out.json' if repair_antennas == '1'
                              else '1-openroad-checkantennas/state_out.json')
    antenna = json.loads(checked.with_name('or_metrics_out.json').read_text())
    if repair_antennas == '1':
        repaired_log = antenna_root / '2-openroad-repairantennas/1-openroad-diodeinsertion/openroad-diodeinsertion.log'
        validate_overflow(repaired_log.read_text())
        changed_nl = Path(json.loads(changed.read_text())['nl'])
        checked = promote_antenna_netlists(checked, changed_nl)
    screen(base_path, source, out / 'timing', os.environ['PDK_ROOT'],
           repaired=checked, sdc=Path('src/signoff.sdc'))
    data = json.loads((out / 'timing/comparison.json').read_text())
    ready = (timing_pass(data) and antenna['antenna__violating__nets'] == 0
             and antenna['antenna__violating__pins'] == 0)
    gates = {'state': str(checked), 'source_route': ROUTE_RUN,
             'ready_for_route_review': ready, 'drt_launched': False,
             'antenna_repair_requested': repair_antennas == '1',
             'timing_pass': timing_pass(data),
             'antenna_nets': antenna['antenna__violating__nets'],
             'antenna_pins': antenna['antenna__violating__pins']}
    (out / 'gates.json').write_text(json.dumps(gates, indent=2) + '\n')
    print(json.dumps(gates, indent=2), flush=True)
    if not ready:
        raise ValueError('ECO timing/antenna gate fails; DRT not launched')
    print('One-cell ECO GRT/antenna/all-corner gates pass; no DRT or official signoff')


if __name__ == '__main__':
    main()
