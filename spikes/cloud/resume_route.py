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
import re

ROOT = Path(__file__).resolve().parents[2]
work = ROOT / 'build/cloud_run'
state = ROOT / 'build/cloud_input/route_state.json'
config = ROOT / 'build/cloud_input/route_config.json'
work.mkdir(exist_ok=False, parents=True)
# Resolve absolute snapshot paths; outputs go in the fresh cloud run directory.
common = [sys.executable, '-m', 'librelane', '--docker-no-tty', '--dockerized',
          '--pdk', 'ihp-sg13cmos5l', '--pdk-root', os.environ['PDK_ROOT'], '--manual-pdk',
          '--hide-progress-bar']


def run_logged(command, path):
    """Keep full evidence while exposing bounded live progress in Actions."""
    last = None
    with path.open('w') as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        while True:
            try:
                return process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                candidates = (sorted(work.glob('runs/**/*detailedrouting.log'))
                              if path.name == 'native_route.log' else []) or [path]
                source = candidates[-1]
                with source.open('rb') as progress:
                    progress.seek(max(0, source.stat().st_size-65536))
                    lines = progress.read().decode(errors='replace').splitlines()
                selected = [line for line in lines if re.search(
                    r'iteration|Number of violations|Antenna|ERROR|WARNING|Running|Pull|Digest', line)]
                status = '\n'.join((selected or lines)[-4:])
                if status and status != last:
                    print(f'Progress from {source.relative_to(ROOT)}:\n{status}', flush=True)
                    last = status
native = common + ['--run-tag', 'native_route', '--force-run-dir', str(work / 'runs/native_route'),
                   '--from', 'OpenROAD.DetailedRouting',
                   '--with-initial-state', str(state), '--to', 'Checker.DisconnectedPins', str(config)]
returncode = run_logged(native, work / 'native_route.log')
(work / 'native_exit.json').write_text(json.dumps({'returncode': returncode})+'\n')
if returncode:
    raise SystemExit(returncode)
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
returncode = run_logged(full, work / 'geometry_and_timing.log')
(work / 'geometry_exit.json').write_text(json.dumps({'returncode': returncode,
    'timing_scope': 'shell extracted STA; macro black-boxed, not configured-fabric timing'})+'\n')
raise SystemExit(returncode)
