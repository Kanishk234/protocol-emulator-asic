"""Prepare a review-only integration payload; never apply it to the worktree."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

import yaml

from prepare_closure_candidate import candidate_inputs
from selector_final_gl import verify_expected

ROOT = Path(__file__).resolve().parents[2]
REGRESSION_RUN = 43946078700
REGRESSION_ARCHIVE_SHA = '0b5f214e7fa11136c33a05a8b09977e5e3d78c771e3e7768d1594ca615d3d026'


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def bind_regression(archive, candidate):
    if hash_bytes(archive.read_bytes()) != REGRESSION_ARCHIVE_SHA:
        raise ValueError('Wrong complete selector regression archive')
    with zipfile.ZipFile(archive) as bundle:
        names = [n for n in bundle.namelist() if n.endswith('/trial-inputs.json')]
        if len(names) != 1:
            raise ValueError('Missing unique regression input receipt')
        if json.loads(bundle.read(names[0])) != candidate_inputs(candidate):
            raise ValueError('Integration source differs from successful regression')
    verify_expected(candidate)


def original_file(root, revision, name):
    result = subprocess.run(['git', 'show', f'{revision}:{name}'], cwd=root,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if result.returncode == 0:
        return result.stdout
    known = subprocess.run(['git', 'cat-file', '-e', f'{revision}:{name}'], cwd=root,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if known.returncode == 0:
        raise ValueError('Cannot read an existing baseline file')
    return None


def build(candidate, archive, output):
    candidate, output = candidate.resolve(), output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('Review payload must be outside the source checkout')
    if output.exists():
        raise ValueError('Preserve existing payload; use a fresh directory')
    bind_regression(archive, candidate)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    inputs = candidate_inputs(candidate)
    changes = []
    for name, proposed in inputs.items():
        previous = original_file(ROOT, revision, name)
        before = hash_bytes(previous) if previous is not None else None
        if before != proposed:
            changes.append(dict(path=name, before_sha256=before, after_sha256=proposed,
                                action='add' if previous is None else 'change'))
    old_cfg = json.loads(original_file(ROOT, revision, 'src/config.json'))
    new_cfg = json.loads((candidate / 'src/config.json').read_text())
    config_changes = {k: dict(before=old_cfg.get(k), after=new_cfg.get(k))
                      for k in sorted(set(old_cfg) | set(new_cfg))
                      if k != '//' and old_cfg.get(k) != new_cfg.get(k)}
    old_spec = yaml.safe_load(original_file(ROOT, revision, 'spec/tripwire.yaml'))
    new_spec = yaml.safe_load((candidate / 'spec/tripwire.yaml').read_text())
    for change in changes:
        target = output / 'payload' / change['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate / change['path'], target)
        if hash_bytes(target.read_bytes()) != change['after_sha256']:
            raise ValueError('Payload copy differs from bound source')
    report = dict(baseline_revision=revision, regression_run=REGRESSION_RUN,
        regression_archive_sha256=REGRESSION_ARCHIVE_SHA, source_input_count=len(inputs),
        changes=changes, config_changes=config_changes,
        configuration_comment_changed=old_cfg.get('//') != new_cfg.get('//'),
        resource_contract=dict(before=old_spec['fabric'], after=new_spec['fabric']),
        physical_qualified=False, source_applied=False, production_config_changed=False,
        approval_required_before_application=[
            'Finalize branch-only resource counts against the architecture contract',
            'Review physical configuration keys outside the standing whitelist',
            'Complete physical/extracted/replay/official qualification',
            'Retain upstream SRAM attribution and review standalone license/NOTICE packaging'],
        scope='Review-only committed-baseline delta; not an approved release or production edit')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--regression-archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.candidate, args.regression_archive, args.output)
    print(f"Prepared {len(result['changes'])} bound file changes; nothing applied")
