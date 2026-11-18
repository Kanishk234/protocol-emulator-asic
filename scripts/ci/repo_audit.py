"""Check maintained repository navigation, source lists, baseline inputs and official workflows."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import yaml
from verify_integrated_candidate import verify

ROOT = Path(__file__).resolve().parents[2]


def audit(root=ROOT):
    root = Path(root).resolve()
    verify(root)
    frozen = json.loads((root / 'scripts/ci/official_workflows.json').read_text())
    for name, expected in frozen.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Official workflow changed: ' + name)
    expected = yaml.safe_load((root / 'info.yaml').read_text())['project']['source_files']
    actual = re.search(r'^PROJECT_SOURCES\s*=\s*(.+)$', (root / 'test/Makefile').read_text(), re.M)[1].split()
    if actual != expected: raise ValueError('Source lists differ')
    for name in expected:
        if not (root / 'src' / name).is_file(): raise ValueError('Missing synthesis source: ' + name)
    broken = []
    for path in [root / 'README.md', *(root / 'docs').rglob('*.md')]:
        for target in re.findall(r'(?<!!)\[[^\]]*\]\(([^\s)]+)\)', path.read_text()):
            if '://' in target or target.startswith(('#', 'mailto:')): continue
            target = target.split('#')[0]
            if target and not (path.parent / target).exists(): broken.append(f'{path.relative_to(root)}: {target}')
    if broken: raise ValueError('Broken documentation links:\n' + '\n'.join(broken))
    subprocess.run(['python', 'tools/gen/gen.py', '--check'], cwd=root, check=True)
    return dict(qualified_inputs_match=True, official_workflows_unchanged=True, source_lists_match=True,
                documentation_links_ok=True, generated_files_match=True)


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
