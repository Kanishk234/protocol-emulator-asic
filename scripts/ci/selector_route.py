"""Admit only the exact selector screen; preserve all shared route/extraction gates."""
import argparse
import json
import os
from pathlib import Path

from closure_route import unpack, restore, route
from prepare_closure_candidate import export, verify
from verify_bitsync_cache_ff import prepare

SOURCE_RUN = 43951998125
SOURCE_SHA = '1258879c18e288c84f12decb0860a01ddf68b74c'
WORKFLOW = '.github/workflows/tripwire-pin-select-screen.yaml'
ARTIFACT_NAME = f'pin-select-screen-{SOURCE_RUN}'
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
    """Compose the same bound two-step source chain without launching hardware tools."""
    baseline = output.with_name(output.name + '-baseline')
    export(ROOT, baseline)
    verify(baseline)
    cache = output.with_name(output.name + '-cache')
    prepare(baseline, cache)
    prepare(cache, output, ROOT / 'spikes/phase2_stock_flow/pin_select_word_ff')
    # prepare() copies only source RTL; retain identical SRAM/metadata from baseline.
    import shutil
    shutil.copytree(baseline / 'macro', output / 'macro')
    shutil.copy2(baseline / 'info.yaml', output / 'info.yaml')


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
        restore(Path.cwd(), frozen, expected, source_run=SOURCE_RUN, source_sha=SOURCE_SHA)
    else:
        route(Path.cwd(), source_run=SOURCE_RUN, source_sha=SOURCE_SHA)
