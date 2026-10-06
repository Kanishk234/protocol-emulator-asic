#!/usr/bin/env python3
"""Resume the authenticated snapshot in the pinned hosted Docker flow.

Only after zero native routing/antenna/disconnected checks, run extraction/STA
and independent GDS/DRC/LVS steps. Macro remains black-boxed for shell STA.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
work = ROOT / 'build/cloud_run'
state = ROOT / 'build/cloud_input/route_state.json'
config = ROOT / 'build/cloud_input/route_config.json'
work.mkdir(exist_ok=False, parents=True)
# Resolve absolute snapshot paths; outputs go in the fresh cloud run directory.
common = [sys.executable, '-m', 'librelane', '--dockerized', '--docker-no-tty',
          '--pdk', 'ihp-sg13cmos5l', '--pdk-root', os.environ['PDK_ROOT'], '--manual-pdk',
          '--hide-progress-bar']
native = common + ['--run-tag', 'native_route', '--force-run-dir', str(work / 'runs/native_route'),
                   '--from', 'OpenROAD.DetailedRouting',
                   '--with-initial-state', str(state), '--to', 'Checker.DisconnectedPins', str(config)]
with (work / 'native_route.log').open('w') as log:
    result = subprocess.run(native, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
(work / 'native_exit.json').write_text(json.dumps({'returncode': result.returncode})+'\n')
if result.returncode:
    raise SystemExit(result.returncode)
states = list((work / 'runs/native_route').glob('*-checker-disconnectedpins/state_out.json'))
if len(states) != 1:
    raise RuntimeError(f'Expected one checked state, found {states}')
checked = json.loads(states[0].read_text())
for key in ('route__drc_errors', 'antenna__violating__nets', 'antenna__violating__pins',
            'design__critical_disconnected_pin__count'):
    if key not in checked['metrics'] or checked['metrics'][key] != 0:
        raise RuntimeError(f'Missing/nonzero native acceptance metric: {key}')
full = common + ['--run-tag', 'geometry_and_timing',
                 '--force-run-dir', str(work / 'runs/geometry_and_timing'),
                 '--from', 'Odb.ReportWireLength',
                 '--with-initial-state', str(states[0]), str(config)]
with (work / 'geometry_and_timing.log').open('w') as log:
    result = subprocess.run(full, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
(work / 'geometry_exit.json').write_text(json.dumps({'returncode': result.returncode,
    'timing_scope': 'shell extracted STA; macro black-boxed, not configured-fabric timing'})+'\n')
raise SystemExit(result.returncode)
