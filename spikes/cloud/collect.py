#!/usr/bin/env python3
"""Collect compact cloud evidence without hundreds of redundant ODB snapshots."""
import json
import hashlib
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
out = ROOT / 'build/cloud_results'
out.mkdir(exist_ok=False, parents=True)
search = [ROOT / 'build/cloud_run', ROOT / 'build/cloud_native', ROOT / 'build/cloud_setup']
native_work = ROOT / 'build/cloud_input/materialized.json'
if native_work.is_file():
    details = json.loads(native_work.read_text())
    search += list(Path(details['native_work']).glob('simulation*'))
trajectory = []
snapshots = []
for directory in search:
    if not directory.is_dir():
        continue
    for path in directory.rglob('*'):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT / 'build')
        if path.suffix == '.lyrdb' or (path.suffix in {'.log', '.rpt', '.json', '.xml'}
                                      and path.stat().st_size < 8*1024*1024):
            dst = out / relative; dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dst)
        if path.name.startswith('drt_iter') and path.suffix == '.odb':
            snapshots.append(path)
        if path.name.startswith('tt_um_warp.drc-') and path.suffix == '.rpt':
            trajectory.append({'report': str(relative),
                               'markers': path.read_text().count('violation type:')})
        if path.name == 'openroad-detailedrouting.log':
            (out / 'routing_trajectory.txt').write_text('\n'.join(
                line for line in path.read_text().splitlines()
                if re.search(r'Start \d+.*iteration|Number of violations =|elapsed time|Antenna', line))+'\n')
# Keep last completed snapshot (not in-flight state). Native reports bind
# any marker count claim; the snapshot by itself is never called a pass.
if snapshots:
    latest = max(snapshots, key=lambda p:p.stat().st_mtime)
    shutil.copyfile(latest, out / 'last_complete_drt.odb')
    (out / 'last_complete_drt.json').write_text(json.dumps({
        'source': str(latest.relative_to(ROOT / 'build')),
        'sha256': hashlib.sha256(latest.read_bytes()).hexdigest(),
        'scope': 'Intermediate snapshot; final native checks determine acceptance',
    }, indent=2)+'\n')
(out / 'marker_history.json').write_text(json.dumps(trajectory, indent=2)+'\n')
# Keep views referenced by the final completed state of each flow, rather than
# assuming drt_iter snapshots include the final router result. Do not infer a
# pass from filenames: retain the exact metrics and hashes for review.
retained = []
for run in sorted((ROOT / 'build/cloud_run/runs').glob('*')):
    states = sorted(run.glob('*-*/state_out.json'),
                    key=lambda p: int(p.parent.name.split('-', 1)[0]))
    if not states:
        continue
    state_path = states[-1]
    state = json.loads(state_path.read_text())
    entry = {'run': run.name, 'state': str(state_path.relative_to(ROOT / 'build')),
             'metrics': state.get('metrics', {}), 'views': {}}
    def preserve_view(kind, value):
        if isinstance(value, dict):
            for corner, source in value.items():
                preserve_view(kind + '/' + corner, source)
        elif isinstance(value, str):
            source = Path(value)
            if not source.is_file():
                raise FileNotFoundError(source)
            relative = source.relative_to(ROOT / 'build')
            target = out / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            entry['views'][kind] = {'path': str(relative),
                'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
    for kind in ('odb', 'def', 'gds', 'nl', 'pnl', 'sdc', 'spef'):
        if state.get(kind) is not None:
            preserve_view(kind, state[kind])
    retained.append(entry)
(out / 'final_views.json').write_text(json.dumps(retained, indent=2)+'\n')
print('Collected bytes:', sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
