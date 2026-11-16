"""Exact density60 replay after successful stock routing and extraction."""
from closure_final_gl import validate as validate_route
from selector_final_gl import prepare_expected as prepare_selector
from selector_final_gl import verify_expected as verify_selector, screen_views
from density_route import SOURCE_RUN, SOURCE_SHA, context as screen_context
from selector_density_trial import prepare as apply_density, CONFIG_SHA

ROUTE_RUN = 43962211849
ROUTE_SHA = '7ba8d40dfe52ff3801566ebfd598a6b52b9d1f02'
ARTIFACT_NAME = f'tripwire-density-route-{ROUTE_RUN}'


def source_context(run, artifact=None, *, completed=True):
    expected = dict(id=ROUTE_RUN, head_sha=ROUTE_SHA, head_branch='tripwire/closure-8x4',
                    path='.github/workflows/tripwire-density-route.yaml', run_attempt=1)
    if completed:
        expected.update(status='completed', conclusion='success')
    if any(run.get(k) != v for k, v in expected.items()):
        raise ValueError('Unqualified or foreign density route')
    if artifact is not None:
        value = artifact.get('digest', '')
        if (artifact.get('name') != ARTIFACT_NAME or artifact.get('expired') is not False
                or artifact.get('workflow_run', {}).get('id') != ROUTE_RUN
                or artifact.get('workflow_run', {}).get('head_sha') != ROUTE_SHA
                or not isinstance(value, str) or not value.startswith('sha256:')
                or len(value) != 71 or any(c not in '0123456789abcdef' for c in value[7:])):
            raise ValueError('Foreign density route artifact')


def prepare_expected(output):
    prepare_selector(output)
    apply_density(output)
    verify_expected(output)


def verify_expected(root):
    verify_selector(root, config_sha=CONFIG_SHA)


def validate(run, artifact, archive, expected, output, *, screen_run, screen_artifact, screen_archive):
    views = screen_views(screen_run, screen_artifact, screen_archive, admit=screen_context)
    verify_expected(expected)
    return validate_route(run, artifact, archive, expected, output, admit=source_context,
        screen_identity=(SOURCE_RUN, SOURCE_SHA), route_identity=(ROUTE_RUN, ROUTE_SHA),
        frozen_views=views, config_sha=CONFIG_SHA)
