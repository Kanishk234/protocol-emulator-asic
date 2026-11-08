"""Apply one byte-bound slot-store enable-drive source variant."""
import hashlib
import json
from pathlib import Path
import subprocess


def apply(root, evidence_dir, variant):
    if variant not in ('constants', 'all_words'):
        raise ValueError('Unreviewed enable-drive variant')
    root, evidence_dir = Path(root).resolve(), Path(evidence_dir).resolve()
    evidence = json.loads((evidence_dir/'evidence.json').read_text())
    selected = evidence['variants'][variant]
    patch = evidence_dir/(variant+'.patch')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    inventory = lambda: {str(p.relative_to(root)): sha(p)
                         for p in (root/'src').rglob('*') if p.is_file()}
    before = inventory()
    if before.get('src/trw_slots.v') != evidence['reference_sha256']:
        raise ValueError('Wrong slot-store reference source')
    if sha(patch) != selected['patch_sha256']:
        raise ValueError('Wrong enable-drive patch')
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=root, check=True)
    subprocess.run(['git', 'apply', str(patch)], cwd=root, check=True)
    after = inventory()
    if after != {**before, 'src/trw_slots.v': selected['candidate_sha256']}:
        raise ValueError('Unexpected enable-drive source changes')
    return dict(before=before, after=after, variant=variant,
                changed_files=['src/trw_slots.v'], physical_qualified=False)
