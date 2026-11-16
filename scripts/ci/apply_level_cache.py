"""Apply the source-bound ASIC same-edge output materialization experiment."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def apply(root, evidence_dir):
    root, evidence_dir = Path(root).resolve(), Path(evidence_dir).resolve()
    evidence = json.loads((evidence_dir / 'candidate.json').read_text())
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    inventory = lambda: {str(p.relative_to(root)): digest(p)
                         for p in (root / 'src').rglob('*') if p.is_file()}
    before = inventory()
    expected = evidence['reference_files']
    for name, sha in expected.items():
        if before.get('src/' + name) != sha:
            raise ValueError('Output-cache reference source mismatch: ' + name)
    if digest(root / 'src/trw_pin_cfg.v') != evidence['configuration_source_sha256']:
        raise ValueError('Wrong root-clock IDLE storage contract')
    if digest(root / 'src/config.json') != evidence['reference_config_sha256']:
        raise ValueError('Output-cache physical settings mismatch')
    patch = evidence_dir / 'level_cache.patch'
    if digest(patch) != evidence['patch_sha256']:
        raise ValueError('Output-cache patch mismatch')
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=root, check=True)
    subprocess.run(['git', 'apply', str(patch)], cwd=root, check=True)
    after = inventory()
    changes = {'src/' + name: sha for name, sha in evidence['candidate_files'].items()}
    if after != {**before, **changes}:
        raise ValueError('Unexpected output-cache source changes')
    return dict(before=before, after=after, changed_files=sorted(changes),
                physical_qualified=False, official_signoff=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--evidence', type=Path,
                        default=Path('spikes/phase2_stock_flow/level_cache'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    receipt = apply(args.root, args.evidence)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
