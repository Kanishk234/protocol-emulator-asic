"""Admit the exact density60 screen with unchanged strict route/extraction gates."""
import argparse
import json
import os
from pathlib import Path

from closure_route import unpack, restore, route
from prepare_closure_candidate import export, verify
from selector_route import expected_source as selector_source
from selector_density_trial import prepare as apply_density, CONFIG_SHA

SOURCE_RUN = 43961635994
SOURCE_SHA = '9e4c74f4f901059b56ae1fdf337b956cea10fa06'
WORKFLOW = '.github/workflows/tripwire-selector-density-screen.yaml'
ARTIFACT_NAME = f'selector-density60-{SOURCE_RUN}'
EXTRA_ROOTS = ('cache-functional-source.json', 'bitsync-cache-physical-source.json',
               'pin-select-physical-source.json')
ROOT = Path(__file__).resolve().parents[2]


def context(run, artifact=None, completed=True):
    expected = dict(id=SOURCE_RUN, head_sha=SOURCE_SHA, head_branch='tripwire/closure-8x4',
                    path=WORKFLOW, run_attempt=1)
    if any(run.get(k) != v for k, v in expected.items()):
        raise ValueError('Foreign selector physical source')
    if completed and (run.get('status'), run.get('conclusion')) != ('completed', 'success'):
        raise ValueError('Selector screen must pass before routing')
    if artifact is not None:
        if (artifact.get('name') != ARTIFACT_NAME or artifact.get('expired') is not False
                or artifact.get('workflow_run', {}).get('id') != SOURCE_RUN
                or artifact.get('workflow_run', {}).get('head_sha') != SOURCE_SHA):
            raise ValueError('Foreign selector screen artifact')
        digest = artifact.get('digest', '')
        if (not isinstance(digest, str) or len(digest) != 71
                or not digest.startswith('sha256:')
                or any(c not in '0123456789abcdef' for c in digest[7:])):
            raise ValueError('Missing exact archive digest')


def expected_source(output):
    selector_source(output)
    import shutil
    profile = Path('spikes/phase2_stock_flow/selected_profile.json')
    (output / profile).parent.mkdir(parents=True, exist_ok=True)
    baseline = output.with_name(output.name + '-baseline')
    shutil.copy2(baseline / profile, output / profile)
    apply_density(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('prepare', 'restore', 'route'))
    args = parser.parse_args()
    expected = Path(os.environ['CLOSURE_EXPECTED_SOURCE'])
    if args.stage == 'prepare':
        expected_source(expected)
    elif args.stage == 'restore':
        run = json.loads(Path('closure-source-run.json').read_text())
        artifact = json.loads(Path('closure-source-artifact.json').read_text())
        context(run, artifact)
        frozen = Path.cwd() / 'closure-frozen'
        unpack(Path('closure-source.zip'), artifact, frozen, EXTRA_ROOTS)
        restore(Path.cwd(), frozen, expected, source_run=SOURCE_RUN, source_sha=SOURCE_SHA, config_sha=CONFIG_SHA)
    else:
        route(Path.cwd(), source_run=SOURCE_RUN, source_sha=SOURCE_SHA, config_sha=CONFIG_SHA)
