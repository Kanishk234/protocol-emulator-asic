#!/usr/bin/env python3
"""Cloud RTL control then native mapped-fabric real-load test; failures propagate."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
details = json.loads((ROOT / 'build/cloud_input/materialized.json').read_text())
base = [sys.executable, str(ROOT / 'spikes/compact_edges/simulate.py'),
        '--work', details['native_work'], '--words', details['words'],
        '--chip-dir', 'chip_shared_crc_cfgbranches']
out = ROOT / 'build/cloud_native'
out.mkdir(exist_ok=False)
with (out / 'rtl_control.log').open('w') as log:
    control = subprocess.run(base, stdout=log, stderr=subprocess.STDOUT)
if control.returncode:
    raise SystemExit(control.returncode)
env = dict(os.environ, WARP_COMPACT_DIAG='1')
with (out / 'native_fabric.log').open('w') as log:
    result = subprocess.run(base+['--mapped-fabric'], env=env, stdout=log, stderr=subprocess.STDOUT)
(out / 'result.json').write_text(json.dumps({'rtl_returncode': control.returncode,
    'native_returncode': result.returncode, 'no_sdf': True,
    'configuration_or_user_state_forced': False})+'\n')
raise SystemExit(result.returncode)
