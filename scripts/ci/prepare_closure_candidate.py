"""Export the current 8x4 CI candidate for local integration checks.

Executes only the committed workflow's source preparation and tile selection.
No physical flow is launched and the source checkout is never patched.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile

import yaml

WORKFLOW = '.github/workflows/gds-official-dev4-hold125-screen.yaml'
PREPARE = 'Prepare the full design with strict stock project inputs'
GEOMETRY = 'Select only the comparison tile size'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preparation(workflow):
    job = workflow['jobs']['screen']
    if job['strategy']['matrix']['tiles'] != ['8x4']:
        raise ValueError('Expected the reviewed 8x4-only comparison')
    env = job['env']
    if (env['STOCK_PROFILE'], env['PORTABLE_VARIANT']) != (
            'rtl_shared_minbuf2_host_idle_ff', 'clock75_hold125'):
        raise ValueError('Unexpected closure candidate profile')
    scripts = []
    for name in (PREPARE, GEOMETRY):
        matches = [step for step in job['steps'] if step['name'] == name]
        if len(matches) != 1 or 'run' not in matches[0]:
            raise ValueError('Expected one source preparation step: ' + name)
        script = matches[0]['run']
        scripts.append(script.replace('${{ matrix.tiles }}', '8x4'))
    return scripts, {key: env[key] for key in ('STOCK_PROFILE', 'PORTABLE_VARIANT')}


def candidate_inputs(root):
    info = yaml.safe_load((root / 'info.yaml').read_text())['project']
    if (info['tiles'], info['clock_hz'], info['top_module']) != (
            '8x4', 50000000, 'tt_um_tripwire'):
        raise ValueError('Wrong candidate metadata')
    sources = info['source_files']
    if 'trw_chip.v' not in sources or len(sources) < 2:
        raise ValueError('Candidate still contains placeholder source metadata')
    makefile = (root / 'test/Makefile').read_text().splitlines()
    project_sources = [line.split('=', 1)[1].split() for line in makefile
                       if line.startswith('PROJECT_SOURCES =')]
    if project_sources != [sources]:
        raise ValueError('Candidate source lists differ')
    for name in sources:
        if not (root / 'src' / name).is_file():
            raise ValueError('Missing candidate source: ' + name)
    selected = json.loads((root / 'spikes/phase2_stock_flow/selected_profile.json').read_text())
    if selected['profile'] != 'portable_clock75_hold125':
        raise ValueError('Wrong prepared physical profile')
    if sha(root / 'src/config.json') != selected['config_sha256']:
        raise ValueError('Prepared project configuration changed')
    paths = [root / 'info.yaml', root / 'test/Makefile', root / 'test/test.py']
    paths += [p for folder in ('src', 'macro')
              for p in (root / folder).rglob('*') if p.is_file()]
    paths += [p for folder in ('tools', 'programs', 'spec', 'test_internal')
              for p in (root / folder).rglob('*') if p.is_file()
              and not any(part in ('sim_build', '__pycache__', '.pytest_cache')
                          for part in p.relative_to(root).parts)
              and (p.suffix in ('.py', '.v', '.vh', '.trw', '.yaml') or p.name == 'Makefile')]
    return {str(path.relative_to(root)): sha(path) for path in sorted(paths)}


def export(root, output):
    root, output = root.resolve(), output.resolve()
    if output == root or root in output.parents:
        raise ValueError('Export outside the source worktree')
    if output.exists():
        raise ValueError('Output must not exist; preserve previous candidates')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    # Refuse tracked or untracked source edits that an archive would silently omit.
    dirty = subprocess.check_output([
        'git', 'status', '--porcelain', '--', 'src', 'macro', 'info.yaml', 'test',
        'spec', 'tools', 'spikes', '.github/workflows'], cwd=root, text=True)
    if dirty.strip():
        raise ValueError('Candidate inputs have local edits; archive would omit them')
    with tempfile.TemporaryFile() as archive:
        subprocess.run(['git', 'archive', '--format=tar', head], cwd=root,
                       stdout=archive, check=True)
        archive.seek(0)
        output.mkdir(parents=True)
        with tarfile.open(fileobj=archive) as bundle:
            bundle.extractall(output, filter='data')
    workflow = yaml.safe_load((output / WORKFLOW).read_text())
    scripts, profile_env = preparation(workflow)
    env = dict(os.environ, **profile_env, PYTHONOPTIMIZE='', PWD=str(output))
    # Ignore ambient Git/configuration/runtime overrides; use the CI macro revision.
    for key in list(env):
        if key.startswith('GIT_') or key in (
                'PYTHONPATH', 'PDK_REV', 'PDK_ROOT', 'LIBRELANE_IMAGE_OVERRIDE',
                'TRIPWIRE_NATIVE_RUNTIME', '_LLN_OVERRIDE_OPENROAD'):
            env.pop(key)
    for script in scripts:
        subprocess.run(['bash', '-c', script], cwd=output, env=env, check=True)
    receipt = dict(source_commit=head, workflow=WORKFLOW,
                   workflow_sha256=sha(output / WORKFLOW),
                   preparation_sha256=[hashlib.sha256(s.encode()).hexdigest() for s in scripts],
                   profile=profile_env, inputs=candidate_inputs(output),
                   scope='Prepared source only; no physical or timing qualification',
                   physical_flow_launched=False, official_gds_passed=False)
    (output / 'closure-candidate.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def verify(root):
    receipt = json.loads((root / 'closure-candidate.json').read_text())
    if candidate_inputs(root) != receipt['inputs']:
        raise ValueError('Candidate inputs changed after export')
    if sha(root / receipt['workflow']) != receipt['workflow_sha256']:
        raise ValueError('Candidate workflow changed after export')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('export', 'verify'))
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    if args.stage == 'export':
        result = export(Path(__file__).resolve().parents[2], args.directory)
    else:
        result = verify(args.directory.resolve())
    print(f"Candidate {args.stage}: {result['source_commit']}; {len(result['inputs'])} checked inputs")
