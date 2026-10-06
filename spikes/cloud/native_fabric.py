#!/usr/bin/env python3
"""Cloud RTL control then native mapped-fabric real-load test; failures propagate."""
import json
import os
from pathlib import Path
import subprocess
import sys
import hashlib

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
# Parse the actual mapped tile with black-box library ports, without remapping
# or changing any logic. The probe walks unknown D-input cones read-only.
tile = Path(details['native_work'])/'fabulous-tiles/tiles/tiny/LUT4x8_ha/macro/ihp-sg13cmos5l/nl/LUT4x8_ha.nl.v'
library = Path(os.environ['PDK_ROOT'])/'ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_slow_1p08V_125C.lib'
cone = out/'actual_tile_cone.json'
with (out/'cone_parse.log').open('w') as log:
    subprocess.run(['yosys', '-Q', '-T', '-p',
        f'read_liberty -lib {library}; read_verilog {tile}; hierarchy -top LUT4x8_ha; write_json {cone}'],
        check=True, stdout=log, stderr=subprocess.STDOUT)
env['WARP_COMPACT_CONE_JSON'] = str(cone)
with (out / 'native_fabric.log').open('w') as log:
    result = subprocess.run(base+['--mapped-fabric'], env=env, stdout=log, stderr=subprocess.STDOUT)
# Explicitly diagnostic: an extra host USER_RESET never substitutes for passing
# the ordinary RUN path. Preserve baseline failure even if this probe passes.
reset_returncode = None
if result.returncode:
    with (out/'native_reset_probe.log').open('w') as log:
        probe = subprocess.run(base+['--mapped-fabric', '--reset-probe'], env=env,
                               stdout=log, stderr=subprocess.STDOUT)
    reset_returncode = probe.returncode
(out / 'result.json').write_text(json.dumps({'rtl_returncode': control.returncode,
    'native_returncode': result.returncode, 'reset_probe_returncode': reset_returncode,
    'mapped_tile_sha256': hashlib.sha256(tile.read_bytes()).hexdigest(), 'no_sdf': True,
    'configuration_or_user_state_forced': False})+'\n')
raise SystemExit(result.returncode)
