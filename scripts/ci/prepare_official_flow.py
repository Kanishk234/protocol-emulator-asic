"""Prepare the reviewed plugin image and source/context checks for TT harden.

This entry point is proposed for one explicit setup step before the unchanged
TT action. It must not be added to protected template jobs without approval.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from physical_runtime import IMAGES

MANIFEST = Path(__file__).parent/'fixtures/wire600_selective/promoted_source.json'
IMAGE = 'tripwire-official:reviewed'


def validate_source(root):
    root = Path(root)
    manifest = json.loads(MANIFEST.read_text())
    for name, expected in manifest['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Main source differs from reviewed promotion: '+name)
    return manifest


def main():
    root = Path.cwd()
    manifest = validate_source(root)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    if head != os.environ['GITHUB_SHA']:
        raise ValueError('Official checkout differs from workflow head')
    context = json.loads(subprocess.check_output([
        'gh', 'api', f'repos/{os.environ["GITHUB_REPOSITORY"]}/actions/runs/{os.environ["GITHUB_RUN_ID"]}'
    ], text=True))
    expected = dict(id=int(os.environ['GITHUB_RUN_ID']), head_sha=head,
                    head_branch='main', path='.github/workflows/gds.yaml',
                    status='in_progress', conclusion=None)
    if any(context.get(k) != v for k, v in expected.items()):
        raise ValueError('Wrong official run context')
    context_path = root/'runs/tripwire-official-context.json'
    context_path.parent.mkdir(exist_ok=True)
    if context_path.exists():
        raise ValueError('Official setup requires a fresh context')
    context_path.write_text(json.dumps(context, indent=2)+'\n')
    macro = root/'macro/RM_IHPSG13_1P_512x16_c2_bm_bist'
    env = dict(os.environ, PDK_REV=manifest['pdk_revision'])
    subprocess.run(['bash', 'spikes/r3_sram/fetch_macro.sh', str(macro)], env=env, check=True)
    for name, expected_sha in manifest['macro_files'].items():
        if hashlib.sha256((macro/name).read_bytes()).hexdigest() != expected_sha:
            raise ValueError('Wrong pinned official macro view: '+name)
    subprocess.run(['docker', 'build', '-t', IMAGE, '-f',
                    'scripts/ci/Dockerfile.tripwire-official', 'scripts/ci'], check=True)
    image_id = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', IMAGE], text=True).strip()
    (root/'runs/tripwire-image.json').write_text(json.dumps(dict(
        image=IMAGE, image_id=image_id,
        native_backend_profiles=list(IMAGES),
        profile_names_are_instrumentation_modes=True), indent=2)+'\n')
    with open(os.environ['GITHUB_ENV'], 'a') as f:
        f.write('LIBRELANE_IMAGE_OVERRIDE='+IMAGE+'\n')
    print('Reviewed source, pinned macro and native plugin image prepared; official TT action follows.')


if __name__ == '__main__':
    main()
