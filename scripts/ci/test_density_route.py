import json

import pytest

from density_route import context, SOURCE_RUN, SOURCE_SHA, WORKFLOW, ARTIFACT_NAME, CONFIG_SHA
from closure_route import restore
from selector_density_trial import select, encoded
from test_closure_route import restored_fixture


@pytest.mark.parametrize('failed', [False, True])
def test_exact_density_screen_must_succeed(failed):
    run = dict(id=SOURCE_RUN, head_sha=SOURCE_SHA, head_branch='tripwire/closure-8x4',
               path=WORKFLOW, run_attempt=1, status='completed',
               conclusion='failure' if failed else 'success')
    artifact = dict(name=ARTIFACT_NAME, expired=False,
                    workflow_run=dict(id=SOURCE_RUN, head_sha=SOURCE_SHA),
                    digest='sha256:' + 'a' * 64)
    if failed:
        with pytest.raises(ValueError): context(run, artifact)
    else:
        context(run, artifact)
        artifact['workflow_run']['head_sha'] = 'wrong'
        with pytest.raises(ValueError): context(run, artifact)


@pytest.mark.parametrize('explicit_density_recipe', [False, True])
def test_density_restoration_requires_the_exact_reviewed_recipe(tmp_path, explicit_density_recipe):
    root, frozen, expected = restored_fixture(tmp_path)
    for directory in (frozen, expected):
        path = directory / 'src/config.json'
        path.write_text(encoded(select(json.loads(path.read_text()))))
    if not explicit_density_recipe:
        with pytest.raises(ValueError): restore(root, frozen, expected)
        assert not (root / 'runs').exists()
    else:
        restore(root, frozen, expected, source_run=SOURCE_RUN, source_sha=SOURCE_SHA, config_sha=CONFIG_SHA)
        receipt = json.loads((root / 'runs/closure-restoration.json').read_text())
        assert receipt['qualified'] is True
        assert receipt['source_run'] == SOURCE_RUN and receipt['source_sha'] == SOURCE_SHA
