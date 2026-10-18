"""Read-only audit of downloaded controlled-repair evidence; never runs EDA.

A separately fetched GitHub run identity and explicit expected run/source are
required. The supplied identity is trusted as the caller's API record; this
module does not independently authenticate a local file's origin.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'test_internal'))
import cloud_route_force_repair as hosted


def source_hash(revision, name):
    data = subprocess.check_output(['git', '-C', str(ROOT), 'show', revision+':'+name],
                                   stderr=subprocess.PIPE, timeout=30)
    return hashlib.sha256(data).hexdigest()


def check_identity(identity, result, *, revision, run_id, attempt):
    if (not re.fullmatch(r'[0-9a-f]{40}', revision) or
            not re.fullmatch(r'[1-9][0-9]*', str(run_id)) or
            isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1):
        raise ValueError('Explicit full revision, positive run ID and attempt required')
    expected = {'id': int(run_id), 'head_sha': revision, 'run_attempt': attempt,
                'head_branch': 'efpga', 'name': 'controlled native pair repair',
                'status': 'completed', 'conclusion': 'success'}
    if any(identity.get(key) != value for key, value in expected.items()):
        raise ValueError('GitHub identity differs from explicit expected completed run')
    if (result.get('source_revision') != revision or
            str(result.get('workflow_run')) != str(run_id) or
            str(result.get('workflow_attempt')) != str(attempt) or
            result.get('diagnostic_completed') is not True or
            result.get('physical_acceptance') is not False):
        raise ValueError('Collector identity/completion/physical scope differs')


def audit(directory, identity, *, revision, run_id, attempt, candidate=False):
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('Expected regular downloaded repair directory')
    # Validators must never follow linked evidence outside the supplied tree.
    if any(p.is_symlink() for p in directory.rglob('*')):
        raise ValueError('Linked repair evidence is forbidden')
    result_path = directory/'result.json'
    result = json.loads(result_path.read_text())
    check_identity(identity, result, revision=revision, run_id=run_id, attempt=attempt)
    if result.get('patch_sha256') != source_hash(revision, 'patches/openroad_force_reroute.patch'):
        raise ValueError('Retained primary patch differs from exact Git source')
    cases = ['default_identity', 'forced_pair'] + (['rebuilt_pair'] if candidate else [])
    if set(result.get('cases', {})) != set(cases):
        raise ValueError('Missing/extra cases or wrong candidate audit mode')
    if candidate and result.get('used_grid_patch_sha256') != source_hash(revision, 'patches/openroad_force_used_grid.patch'):
        raise ValueError('Candidate patch differs from exact Git source')
    summary = {}
    for name in cases:
        stages = list((directory/name/'replay').glob('*-openroad-globalrouting'))
        if len(stages) != 1 or not stages[0].is_dir():
            raise ValueError('Missing or ambiguous native stage')
        stage = stages[0]
        actual = hosted.validate_stage(stage, name != 'default_identity')
        if name == 'forced_pair':
            actual['observer'] = hosted.validate_observer(stage, actual)
        if candidate:
            actual['used_grid_rebuild_calls'] = hosted.validate_rebuild_witness(stage, name)
        stored = result['cases'][name]
        if any(stored.get(key) != value for key, value in actual.items()):
            raise ValueError('Retained collector result contradicts independently parsed '+name)
        summary[name] = {'overflow': actual['final_observed_full_grid_overflow'],
                         'native_repair_passed': actual['native_repair_passed'],
                         'native_error': actual['native_error'],
                         'physical_acceptance': False}
        if name == 'forced_pair':
            summary[name]['observed_passes'] = [
                {'pass': row['pass'], 'nets': row['actual_native_pass_net_count'],
                 'overflow': row['observed_full_grid_overflow']}
                for row in actual['observer']['passes']]
    return {'verified': True, 'run_id': str(run_id), 'attempt': attempt,
            'source_revision': revision, 'result_sha256': hashlib.sha256(result_path.read_bytes()).hexdigest(),
            'cases': summary, 'physical_acceptance': False,
            'scope': 'Downloaded native evidence audit; no physical promotion or local EDA'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    p.add_argument('--identity', type=Path, required=True)
    p.add_argument('--revision', required=True)
    p.add_argument('--run-id', required=True)
    p.add_argument('--attempt', type=int, required=True)
    p.add_argument('--candidate', action='store_true')
    a = p.parse_args()
    print(json.dumps(audit(a.directory, json.loads(a.identity.read_text()), revision=a.revision,
                           run_id=a.run_id, attempt=a.attempt, candidate=a.candidate), indent=2))


if __name__ == '__main__':
    main()
