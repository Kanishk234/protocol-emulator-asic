"""Bind final replay to the selector route and its independently authenticated screen."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from closure_final_gl import validate as validate_route, member
from closure_route import digest
from prepare_closure_candidate import candidate_inputs, sha
from selector_route import SOURCE_RUN, SOURCE_SHA, context as screen_context, expected_source

ROUTE_RUN = 43956306270
ROUTE_SHA = '29c0e63c40696c1f038035fa94234efa26c3e8d6'
ARTIFACT_NAME = f'tripwire-selector-route-{ROUTE_RUN}'
ROOT = Path(__file__).resolve().parents[2]


def source_context(run, artifact=None, *, completed=True):
    expected = dict(id=ROUTE_RUN, head_sha=ROUTE_SHA, head_branch='tripwire/closure-8x4',
                    path='.github/workflows/tripwire-selector-route.yaml', run_attempt=1)
    if completed:
        expected.update(status='completed', conclusion='success')
    if any(run.get(k) != v for k, v in expected.items()):
        raise ValueError('Unqualified or foreign selector route')
    if artifact is not None:
        value = artifact.get('digest', '')
        if (artifact.get('name') != ARTIFACT_NAME or artifact.get('expired') is not False
                or artifact.get('workflow_run', {}).get('id') != ROUTE_RUN
                or artifact.get('workflow_run', {}).get('head_sha') != ROUTE_SHA
                or not isinstance(value, str) or not value.startswith('sha256:')
                or len(value) != 71 or any(c not in '0123456789abcdef' for c in value[7:])):
            raise ValueError('Foreign selector route artifact')


def prepare_expected(output):
    expected_source(output)
    baseline = output.with_name(output.name + '-baseline')
    # Add the independently exported firmware/model/test harness without replacing
    # the composed selector RTL or macro views.
    for source in baseline.iterdir():
        if source.name in ('src', 'macro', 'info.yaml'):
            continue
        target = output / source.name
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
    verify_expected(output)


def verify_expected(root):
    baseline = json.loads((root / 'closure-candidate.json').read_text())
    identity = json.loads((ROOT / 'spikes/phase2_stock_flow/pin_select_word_ff/identity.json').read_text())
    expected = dict(baseline['inputs'], **{'src/trw_pin_cfg.v': identity['candidate_sha256']})
    if candidate_inputs(root) != expected or sha(root / baseline['workflow']) != baseline['workflow_sha256']:
        raise ValueError('Selector replay inputs changed')


def screen_views(run, artifact, archive):
    screen_context(run, artifact)
    if 'sha256:' + digest(archive) != artifact['digest']:
        raise ValueError('Independent screen archive digest mismatch')
    with zipfile.ZipFile(archive) as bundle:
        recorded = json.loads(bundle.read('runs/stock-corner-audit/read_only_audit.json'))
        result = {member(path, 'runs/stock-official-baseline'): value
                  for path, value in recorded['unchanged_physical_view_hashes'].items()}
        if len(result) != 6:
            raise ValueError('Incomplete independent frozen screen views')
        for path, value in result.items():
            if hashlib.sha256(bundle.read(path)).hexdigest() != value:
                raise ValueError('Independent screen view hash mismatch')
    return result


def validate(run, artifact, archive, expected, output, *, screen_run, screen_artifact, screen_archive):
    views = screen_views(screen_run, screen_artifact, screen_archive)
    verify_expected(expected)
    return validate_route(run, artifact, archive, expected, output, admit=source_context,
        screen_identity=(SOURCE_RUN, SOURCE_SHA), route_identity=(ROUTE_RUN, ROUTE_SHA),
        frozen_views=views)
