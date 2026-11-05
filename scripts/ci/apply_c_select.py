"""Apply the bound C-selector experiment to an already prepared full design."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def apply(root, evidence_dir):
    root, evidence_dir = Path(root).resolve(), Path(evidence_dir).resolve()
    evidence = json.loads((evidence_dir / 'c_select_candidate.json').read_text())
    patch = evidence_dir / 'c_select_unclamped.patch'

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def sources():
        return {str(p.relative_to(root)): sha(p)
                for p in (root / 'src').rglob('*') if p.is_file()}

    target = 'src/trw_pin_io.v'
    before = sources()
    if before.get(target) != evidence['reference_sha256']:
        raise ValueError('C-selector reference source mismatch')
    if sha(patch) != evidence['patch_sha256']:
        raise ValueError('C-selector patch mismatch')
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=root, check=True)
    subprocess.run(['git', 'apply', str(patch)], cwd=root, check=True)
    after = sources()
    if after != {**before, target: evidence['candidate_sha256']}:
        raise ValueError('Unexpected C-selector source changes')
    return {'before': before, 'after': after, 'changed_files': [target],
            'patch_sha256': evidence['patch_sha256'],
            'scope': 'Source preparation only; no timing or physical qualification'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--evidence', type=Path,
                        default=Path('spikes/phase2_stock_flow/pin_input_decode'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = apply(args.root, args.evidence)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Verified one-file C-selector source change')


if __name__ == '__main__':
    main()
