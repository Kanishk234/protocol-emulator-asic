"""Immutable content identities and fail-closed workspace boundaries."""
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                     separators=(',', ':')).encode()).hexdigest()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def run(args, cwd=ROOT):
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.PIPE).strip()

def workspace():
    if ROOT != Path('/home/younix/tripwire-autonomous-pd'):
        raise ValueError('Workspace is not the authorized worktree')
    if run(['git', 'branch', '--show-current']) != 'autonomous-pd':
        raise ValueError('Requires autonomous-pd branch')
    return {'root': str(ROOT), 'head': run(['git', 'rev-parse', 'HEAD']),
            'dirty': run(['git', 'status', '--porcelain', '--untracked-files=all'])}

def inside(root, relative):
    root = Path(root).resolve()
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        raise ValueError('Unsafe relative path')
    candidate = root / p
    if any(x.is_symlink() for x in [candidate, *candidate.parents] if x != root.parent):
        raise ValueError('Symlink input forbidden')
    if not candidate.resolve().is_relative_to(root):
        raise ValueError('Path escapes root')
    return candidate

def snapshot(root, paths):
    return {p: sha(inside(root, p)) for p in sorted(paths)}

def materialize(root, hashes, destination):
    dest = Path(destination).resolve()
    if not dest.is_relative_to(ROOT / 'pdforge' / '.local'):
        raise ValueError('Copies must stay in pdforge/.local')
    if snapshot(root, hashes) != hashes:
        raise ValueError('Baseline mutation before copy')
    dest.mkdir(parents=True, exist_ok=False)
    for name, expected in hashes.items():
        source = inside(root, name)
        target = inside(dest, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if sha(target) != expected:
            raise ValueError('Copy changed during materialization')
    if snapshot(root, hashes) != hashes:
        raise ValueError('Baseline mutation during copy')
    return str(dest)

def finite(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError('Expected finite numeric observation')
    return value

def load(path):
    return json.loads(Path(path).read_text(), parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))

def pins():
    tree = ast.parse((ROOT / 'scripts/ci/status_merge_screen.py').read_text())
    wanted = {'TOOLS', 'PDK', 'IMAGE', 'IMAGE_DIGEST', 'OPENROAD', 'CORNERS'}
    return {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id in wanted}

def inventory():
    result = workspace()
    inputs = [str(p.relative_to(ROOT)) for base in ['src', 'macro']
              for p in (ROOT / base).rglob('*') if p.is_file()]
    inputs += ['info.yaml', 'spec/tripwire.yaml']
    result.update(inputs=snapshot(ROOT, inputs), pins=pins(),
                  tools={x: shutil.which(x) for x in ['codex', 'openroad', 'yosys', 'docker', 'bwrap', 'unshare']},
                  disk_free_bytes=shutil.disk_usage(ROOT).free,
                  memory=Path('/proc/meminfo').read_text(),
                  environment={k: os.environ.get(k) for k in ['PDK_ROOT', 'OMP_NUM_THREADS']},
                  missing=['resolved config', 'seed', 'SDC/corner receipt', 'native engine manifest'])
    result['identity'] = digest({'head': result['head'], 'inputs': result['inputs'], 'pins': result['pins']})
    return result
