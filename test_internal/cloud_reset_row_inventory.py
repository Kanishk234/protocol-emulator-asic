"""Read-only native DEF/row/blockage inventory of authenticated shell source."""
import json
import os
from pathlib import Path
import subprocess

import cloud_cfg_fanout as cfg
from cloud_fanout_local_grt import BUFFERED, validate_candidate

ROOT = cfg.ROOT
INPUT = ROOT / 'build/reset_row_inventory_input'
OUT = ROOT / 'build/reset_row_inventory'


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('Native execution is cloud-only')
    OUT.mkdir(parents=True, exist_ok=True)
    source = INPUT / 'fixed_original'
    evidence = validate_candidate(source)
    odb = source / 'buffered.odb'
    if cfg.sha(odb) != BUFFERED['odb']:
        raise ValueError('Authenticated source ODB differs')
    script = OUT / 'inventory.tcl'
    script.write_text(cfg.CENSUS + r'''
read_db $::env(WARP_SOURCE)
check_placement -verbose
census $::env(WARP_CENSUS)
# DEF preserves actual fragmented ROW records, macro geometry and BLOCKAGES.
# Read-only export: no legalization or placement repair occurs.
write_def $::env(WARP_DEF)
''')
    command = ['docker', 'run', '--rm', '-v', f'{ROOT}:{ROOT}', '-w', str(ROOT)]
    for key, path in {'WARP_SOURCE': odb, 'WARP_CENSUS': OUT/'census.tsv',
                      'WARP_DEF': OUT/'placement.def'}.items():
        command.extend(['-e', f'{key}={path}'])
    command.extend(['--entrypoint', 'openroad', cfg.IMAGE, '-exit', str(script)])
    with (OUT/'native.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    if cfg.sha(odb) != BUFFERED['odb'] or cfg.parse_census((OUT/'census.tsv').read_text()) != cfg.parse_census((source/'after.tsv').read_text()):
        raise ValueError('Read-only inventory source changed')
    text = (OUT/'placement.def').read_text()
    rows = [line for line in text.splitlines() if line.startswith('ROW ')]
    if not rows:
        raise ValueError('Native export has no actual rows')
    (OUT/'rows.def').write_text('\n'.join(rows)+'\n')
    result = {'passed': True, 'source_run': 38101405271,
              'source_odb_sha256': BUFFERED['odb'], 'source_validation': evidence,
              'actual_row_record_count': len(rows),
              'files_sha256': {name: cfg.sha(OUT/name) for name in ('placement.def','rows.def','census.tsv')},
              'scope': 'Read-only native placement inventory; no routing/timing/physical promotion'}
    (OUT/'result.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
