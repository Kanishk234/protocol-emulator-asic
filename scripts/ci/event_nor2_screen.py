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
DROP_SOURCE_RUN = 37736921949
HOLD_SOURCE_RUN = 37803300460
DRIVER_SOURCE_RUN = 37806209914
RESIDUAL_SOURCE_RUN = 37818177484


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


def validate_drop_netlist(before, after):
    original, changed = logical_cells(before), logical_cells(after)
    expected = ('sg13cmos5l_nor2_1', (('A', '_05964_'), ('B', '_05968_'), ('Y', '_05970_')))
    if original.get('_31567_') != expected:
        raise ValueError('Dropped-event cell identity or connectivity changed')
    if original.get('_27853_', ('',))[0] != 'sg13cmos5l_nor2_2':
        raise ValueError('Missing prior qualified event NOR2 repair')
    original['_31567_'] = ('sg13cmos5l_nor2_2', expected[1])
    if original != changed:
        raise ValueError('Dropped-event ECO changed additional cells or connections')


def validate_driver_netlist(before, after):
    original, changed = logical_cells(before), logical_cells(after)
    expected = ('sg13cmos5l_a21oi_1', (('A1', '_12085_'), ('A2', '_12163_'),
                                     ('B1', '_12191_'), ('Y', '_12192_')))
    if original.get('_38386_') != expected:
        raise ValueError('Driver cell identity or connectivity changed')
    for name in ('_27853_', '_31567_'):
        if original.get(name, ('',))[0] != 'sg13cmos5l_nor2_2':
            raise ValueError('Missing prior qualified NOR2 repair')
    from drop_leaf_hold import TARGETS
    for sink, net, *_ in TARGETS:
        new_net = f'tripwire_drop_hold_net{sink}'
        if original.get(f'tripwire_drop_hold_buf{sink}') != (
                'sg13cmos5l_buf_1', (('A', net), ('X', new_net))):
            raise ValueError('Missing qualified hold leaf')
        master, pins = original.get(sink, ('', ()))
        if master != 'sg13cmos5l_dfrbpq_1' or dict(pins).get('D') != new_net:
            raise ValueError('Qualified hold leaf destination changed')
    original['_38386_'] = ('sg13cmos5l_a21oi_2', expected[1])
    if original != changed:
        raise ValueError('Driver ECO changed additional cells or connections')


def validate_residual_netlist(before, after):
    from residual_setup import TARGETS
    original, changed = logical_cells(before), logical_cells(after)
    # The complete prior driver/hold history is independently checked at entry.
    if original.get('_38386_', ('',))[0] != 'sg13cmos5l_a21oi_2':
        raise ValueError('Missing qualified driver repair')
    for name, old, new, pins in TARGETS:
        if original.get(name) != (old, tuple(sorted(pins.items()))):
            raise ValueError('Residual target identity or connectivity changed')
        original[name] = (new, tuple(sorted(pins.items())))
    if original != changed:
        raise ValueError('Residual ECO changed additional cells or connections')


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


def validate_antenna_overflow(log):
    marker = 'TRIPWIRE antenna overflow audit: incremental repair completed with congestion disallowed'
    if log.count(marker) != 1:
        raise ValueError('Missing or ambiguous post-repair routing audit')
    prefix = log.split(marker, 1)[0]
    if 'repair_antennas' not in prefix or '-allow_congestion' in prefix:
        raise ValueError('Antenna repair congestion policy not enforced')


def promote_netlists(state_path, original_netlist, drop=False, hold=False, driver=False, residual=False):
    state = json.loads(state_path.read_text())
    odb = Path(state['odb'])
    nl = odb.with_suffix('.eco.nl.v')
    pnl = odb.with_suffix('.eco.pnl.v')
    baseline = odb.with_suffix('.baseline.nl.v')
    if not nl.is_file() or not pnl.is_file() or not baseline.is_file():
        raise ValueError('Fresh ECO netlists missing; stale STA refused')
    if drop or hold or driver:
        if logical_cells(original_netlist.read_text()) != logical_cells(baseline.read_text()):
            raise ValueError('Qualified source ODB/netlist mismatch')
        if driver:
            (validate_residual_netlist if residual else validate_driver_netlist)(baseline.read_text(), nl.read_text())
        elif hold:
            from drop_leaf_hold import validate_drop_leaf_hold
            validate_drop_leaf_hold(baseline.read_text(), nl.read_text())
        else:
            validate_drop_netlist(baseline.read_text(), nl.read_text())
    else:
        validate_physical_baseline(original_netlist.read_text(), baseline.read_text())
        validate_netlist(baseline.read_text(), nl.read_text())
    if not re.search(r'\bsg13cmos5l_nor2_2\s+_27853_\s*\(', pnl.read_text()):
        raise ValueError('Powered netlist missing ECO')
    if (drop or hold or driver) and not re.search(r'\bsg13cmos5l_nor2_2\s+_31567_\s*\(', pnl.read_text()):
        raise ValueError('Powered netlist missing dropped-event ECO')
    if driver and not re.search(r'\bsg13cmos5l_a21oi_2\s+_38386_\s*\(', pnl.read_text()):
        raise ValueError('Powered netlist missing driver ECO')
    if hold or driver:
        from drop_leaf_hold import TARGETS
        for sink, *_ in TARGETS:
            if not re.search(r'\bsg13cmos5l_buf_1\s+tripwire_drop_hold_buf' + sink + r'\s*\(', pnl.read_text()):
                raise ValueError('Powered netlist missing hold leaf')
    if residual:
        from residual_setup import TARGETS
        powered = logical_cells(pnl.read_text())
        for name, old, new, pins in TARGETS:
            master, ports = powered.get(name, ('', ()))
            ports = dict(ports)
            if master != new or any(ports.get(k) != v for k, v in pins.items()):
                raise ValueError('Powered residual target mismatch')
            if not ports.get('VDD') or not ports.get('VSS'):
                raise ValueError('Powered residual target disconnected supplies')
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
    profile = os.environ.get('ECO_PROFILE', 'original')
    if profile not in {'original', 'drop-nor2', 'drop-hold', 'drop-driver', 'residual-setup'}:
        raise ValueError('Unreviewed ECO profile')
    drop = profile == 'drop-nor2'
    hold = profile == 'drop-hold'
    residual = profile == 'residual-setup'
    driver = profile in {'drop-driver', 'residual-setup'}
    run_info = json.loads(Path('/tmp/event-nor2-route-run.json').read_text())
    if drop or hold or driver:
        source_run = RESIDUAL_SOURCE_RUN if residual else DRIVER_SOURCE_RUN if driver else HOLD_SOURCE_RUN if hold else DROP_SOURCE_RUN
        source_workflow = ('gds-drop-driver-screen' if residual else 'gds-drop-leaf-hold-screen' if driver else
                           'gds-drop-event-screen' if hold else 'gds-event-nor2-screen')
        if (run_info['id'] != source_run or run_info['head_branch'] != 'main'
                or run_info['conclusion'] != 'success'
                or run_info['path'] != f'.github/workflows/{source_workflow}.yaml'):
            raise ValueError('Unqualified dropped-event source screen')
    else:
        validate_run(run_info)
    root = Path('runs/drop-driver' if residual else 'runs/drop-hold' if driver else 'runs/drop-event' if hold else 'runs/event-nor2' if drop else 'runs/placement-route')
    identity = validate_identity(json.loads((root / 'source_identity.json').read_text()), Path.cwd(), VARIANT)
    expected = validate_identity(json.loads(Path('/tmp/placement-source-identity.json').read_text()), Path.cwd(), VARIANT)
    if identity != expected or identity['source_run_id'] != SOURCE_RUN:
        raise ValueError('Original hardware fingerprints changed')
    gates = json.loads((root / 'gates.json').read_text())
    source = Path(gates['state'])
    timing = json.loads((root / ('timing/comparison.json' if drop or hold or driver else 'postantenna-sta/comparison.json')).read_text())
    expected_state = root / ('antenna/3-openroad-checkantennas-1/eco_state.json' if drop or hold or driver
                             else 'antenna/3-openroad-checkantennas-1/state_out.json')
    if (not gates['ready_for_route_review' if drop or hold or driver else 'timing_and_antenna_pass'] or not timing_pass(timing)
            or Path(timing['after_state']).resolve() != source.resolve()
            or source.resolve() != expected_state.resolve()):
        raise ValueError('Original checkpoint timing/state gate fails')
    if drop or hold or driver:
        if (gates['antenna_repair_requested'] is not True
                or gates['antenna_nets'] != 0 or gates['antenna_pins'] != 0
                or gates['source_route'] != ROUTE_RUN):
            raise ValueError('Dropped-event source antenna/provenance gate fails')
        validate_antenna_overflow((root / 'antenna/2-openroad-repairantennas/1-openroad-diodeinsertion/openroad-diodeinsertion.log').read_text())
        if hold and (gates['eco_profile'] != 'drop-nor2' or gates['source_screen'] != DROP_SOURCE_RUN):
            raise ValueError('Unreviewed hold source repair history')
        if driver:
            from event_nor2_route import validate_hold_history, validate_driver_history, qualified, validate_repair_chain
            (validate_driver_history if residual else validate_hold_history)(gates)
            if not qualified(timing, {'antenna__violating__nets': gates['antenna_nets'],
                                      'antenna__violating__pins': gates['antenna_pins']}):
                raise ValueError('Driver source lacks qualified hold margin')
            validate_repair_chain(root, json.loads(source.read_text()), held=True, driver=residual)
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
    out = Path('runs/residual-setup' if residual else 'runs/drop-driver' if driver else 'runs/drop-hold' if hold else 'runs/drop-event' if drop else 'runs/event-nor2')
    out.mkdir(exist_ok=False)
    (out / 'source_identity.json').write_text(json.dumps(identity, indent=2) + '\n')
    os.environ['LIBRELANE_IMAGE_OVERRIDE'] = ('tripwire-residual-setup:local' if residual else 'tripwire-drop-driver:local' if driver else 'tripwire-drop-hold:local' if hold
                                            else 'tripwire-drop-event:local' if drop else 'tripwire-event-nor2:local')

    def run(tag, steps, initial):
        cfg = dict(base)
        cfg.update(PNR_CORNERS=list(CORNERS), RSZ_CORNERS=list(CORNERS), OPENROAD_THREADS=4,
                   PNR_SDC_FILE=str(Path('src/signoff.sdc').resolve()),
                   meta={'version': base.get('meta', {}).get('version', 1), 'flow': steps})
        if tag == 'antenna':
            cfg['GRT_ALLOW_CONGESTION'] = False
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
    marker = 'TRIPWIRE residual setup:' if residual else 'TRIPWIRE drop-driver sizing:' if driver else 'TRIPWIRE drop-leaf hold:' if hold else 'TRIPWIRE dropped-event sizing:' if drop else 'TRIPWIRE event NOR2:'
    if marker not in log or 'TRIPWIRE hotspot screen:' not in log:
        raise ValueError('Missing ECO or routing reservation evidence')
    validate_overflow(log)
    changed = promote_netlists(state_path, Path(saved['nl']), drop=drop, hold=hold, driver=driver, residual=residual)
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
        validate_antenna_overflow(repaired_log.read_text())
        changed_nl = Path(json.loads(changed.read_text())['nl'])
        checked = promote_antenna_netlists(checked, changed_nl)
    screen(base_path, source, out / 'timing', os.environ['PDK_ROOT'],
           repaired=checked, sdc=Path('src/signoff.sdc'))
    data = json.loads((out / 'timing/comparison.json').read_text())
    ready = (timing_pass(data) and antenna['antenna__violating__nets'] == 0
             and antenna['antenna__violating__pins'] == 0)
    if hold or driver:
        ready = ready and data['corners'][CORNERS[0]]['after'][f'timing__hold__ws__corner:{CORNERS[0]}'] >= 0.05
    gates = {'state': str(checked), 'source_route': ROUTE_RUN,
             'ready_for_route_review': ready, 'drt_launched': False,
             'antenna_repair_requested': repair_antennas == '1',
             'timing_pass': timing_pass(data),
             'antenna_nets': antenna['antenna__violating__nets'],
             'antenna_pins': antenna['antenna__violating__pins']}
    if drop or hold or driver:
        gates.update(eco_profile=profile, source_screen=RESIDUAL_SOURCE_RUN if residual else DRIVER_SOURCE_RUN if driver else HOLD_SOURCE_RUN if hold else DROP_SOURCE_RUN)
    if hold or driver:
        gates.update(minimum_fast_hold_ns=0.05,
                     fast_hold_margin_pass=data['corners'][CORNERS[0]]['after'][f'timing__hold__ws__corner:{CORNERS[0]}'] >= 0.05)
    (out / 'gates.json').write_text(json.dumps(gates, indent=2) + '\n')
    print(json.dumps(gates, indent=2), flush=True)
    if not ready:
        raise ValueError('ECO timing/antenna gate fails; DRT not launched')
    print('Bounded ECO GRT/antenna/all-corner gates pass; no DRT or official signoff')


if __name__ == '__main__':
    main()
