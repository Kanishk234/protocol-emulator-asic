"""Apply the hash-bound input-selector configuration staging RTL experiment."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def apply(root, evidence_dir):
    root, evidence_dir = Path(root).resolve(), Path(evidence_dir).resolve()
    evidence = json.loads((evidence_dir / 'candidate.json').read_text())
    patch = evidence_dir / 'input_word_bank.patch'
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    inventory = lambda: {str(p.relative_to(root)): sha(p)
                         for p in (root / 'src').rglob('*') if p.is_file()}
    target = 'src/trw_pin_cfg.v'
    before = inventory()
    if before.get(target) != evidence['reference_sha256']:
        raise ValueError('Input-word bank reference source mismatch')
    if sha(patch) != evidence['patch_sha256']:
        raise ValueError('Input-word bank patch mismatch')
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=root, check=True)
    subprocess.run(['git', 'apply', str(patch)], cwd=root, check=True)
    after = inventory()
    if after != {**before, target: evidence['candidate_sha256']}:
        raise ValueError('Unexpected Input-word bank source changes')
    return dict(before=before, after=after, changed_files=[target],
                patch_sha256=evidence['patch_sha256'], physical_qualified=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--evidence', type=Path,
                        default=Path('spikes/phase2_stock_flow/input_word_bank'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = apply(args.root, args.evidence)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Verified one-file input-selector configuration staging source change')
