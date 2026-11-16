"""Reject foreign/failed selector sources and preserve strict route defaults."""
from copy import deepcopy
import inspect

import pytest

from selector_route import SOURCE_RUN, SOURCE_SHA, ARTIFACT_NAME, WORKFLOW, context
from closure_route import restore, route, SOURCE_RUN as OLD_RUN, SOURCE_SHA as OLD_SHA


def source():
    run = dict(id=SOURCE_RUN, head_sha=SOURCE_SHA, head_branch='tripwire/closure-8x4',
               path=WORKFLOW, run_attempt=1, status='completed', conclusion='success')
    artifact = dict(name=ARTIFACT_NAME, expired=False,
                    workflow_run=dict(id=SOURCE_RUN, head_sha=SOURCE_SHA),
                    digest='sha256:' + 'a' * 64)
    return run, artifact


def test_exact_passing_source_and_archive():
    context(*source())


@pytest.mark.parametrize('key,value', [('id', 1), ('head_sha', 'other'),
    ('head_branch', 'main'), ('path', 'other.yaml'), ('run_attempt', 2),
    ('conclusion', 'failure'), ('conclusion', 'cancelled'), ('status', 'in_progress')])
def test_source_substitution_and_failure_rejected(key, value):
    run, artifact = source()
    run[key] = value
    with pytest.raises(ValueError):
        context(run, artifact)


@pytest.mark.parametrize('key,value', [('name', 'other'), ('expired', True),
                                     ('digest', 'sha256:' + 'z' * 64)])
def test_wrong_archive_rejected(key, value):
    run, artifact = source()
    artifact[key] = value
    with pytest.raises(ValueError):
        context(run, artifact)


def test_archive_run_binding_required():
    run, artifact = source()
    for key, value in [('id', 1), ('head_sha', 'other')]:
        bad = deepcopy(artifact)
        bad['workflow_run'][key] = value
        with pytest.raises(ValueError):
            context(run, bad)


def test_old_continuation_defaults_stay_bound_to_original_source():
    for function in (restore, route):
        params = inspect.signature(function).parameters
        assert params['source_run'].default == OLD_RUN
        assert params['source_sha'].default == OLD_SHA
