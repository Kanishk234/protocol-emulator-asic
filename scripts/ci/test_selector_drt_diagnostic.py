import json

import pytest

from selector_drt_diagnostic import (context, admit_failure, assess, restore_source,
    SOURCE_RUN, SOURCE_SHA, ARTIFACT_ID, ARCHIVE_SHA, ANTENNA_FAILURES)
from selector_route import ARTIFACT_NAME, WORKFLOW
from postgrt_timing import CORNERS
from test_closure_route import restored_fixture, timing
from closure_route import restore


def metadata():
    return (dict(id=SOURCE_RUN, head_sha=SOURCE_SHA, head_branch='tripwire/closure-8x4',
                 path=WORKFLOW, status='completed', conclusion='failure', run_attempt=1),
            dict(id=ARTIFACT_ID, name=ARTIFACT_NAME, expired=False, digest=ARCHIVE_SHA,
                 workflow_run=dict(id=SOURCE_RUN, head_sha=SOURCE_SHA)))


@pytest.mark.parametrize('fault', [None, 'success', 'running', 'artifact', 'sha'])
def test_only_exact_retained_failure_can_start_diagnostic(fault):
    run, artifact = metadata()
    if fault == 'success': run['conclusion'] = 'success'
    if fault == 'running': run['status'] = 'in_progress'
    if fault == 'artifact': artifact['id'] = 1
    if fault == 'sha': run['head_sha'] = 'wrong'
    if fault is None: context(run, artifact)
    else:
        with pytest.raises(ValueError): context(run, artifact)


@pytest.mark.parametrize('fault', [None, 'qualified', 'overflow', 'timing', 'extra_antenna'])
def test_diagnostic_admission_does_not_allow_other_failed_gates(fault):
    result = dict(qualified=False, failures=list(ANTENNA_FAILURES), final_global_overflow=0)
    if fault == 'qualified': result['qualified'] = True
    if fault == 'overflow': result['final_global_overflow'] = 1
    if fault == 'timing': result['failures'].append('slow setup: -1 ns')
    if fault == 'extra_antenna': result['failures'] = ['antenna__violating__nets: 5', 'antenna__violating__pins: 5']
    if fault is None: admit_failure(result)
    else:
        with pytest.raises(ValueError): admit_failure(result)


def source_fixture(tmp_path):
    root, frozen, expected = restored_fixture(tmp_path)
    audit = frozen / 'runs/stock-corner-audit'
    path = audit / 'read_only_audit.json'
    receipt = json.loads(path.read_text())
    receipt['fresh_antenna_metrics'] = dict(antenna__violating__nets=1, antenna__violating__pins=1)
    path.write_text(json.dumps(receipt))
    path = next((audit / 'fresh-antenna').glob('*-openroad-checkantennas/or_metrics_out.json'))
    path.write_text(json.dumps(receipt['fresh_antenna_metrics']))
    return root, frozen, expected


def test_failed_source_is_preserved_and_never_marked_qualified(tmp_path):
    root, frozen, expected = source_fixture(tmp_path)
    source = restore_source(root, frozen, expected)
    assert source.is_file()
    receipt = json.loads((root / 'runs/selector-diagnostic-source.json').read_text())
    assert receipt['qualified'] is False and receipt['release_qualified'] is False
    assert not (root / 'runs/closure-restoration.json').exists()


def test_normal_release_restoration_still_refuses_same_failed_source(tmp_path):
    root, frozen, expected = source_fixture(tmp_path)
    with pytest.raises(ValueError): restore(root, frozen, expected)
    assert not (root / 'runs/closure-restoration.json').exists()


@pytest.mark.parametrize('fault', [None, 'timing', 'antenna', 'electrical'])
def test_final_measurements_never_promote_even_when_numeric_gates_pass(fault):
    values = {k: v for row in timing()['corners'].values()
              for k, v in row['before'].items() if k.startswith('timing__')}
    electrical = {c: dict(counts=dict(slew=0, capacitance=0, fanout=0)) for c in CORNERS}
    antenna = dict(antenna__violating__nets=0, antenna__violating__pins=0)
    if fault == 'timing': values[f'timing__setup__ws__corner:{CORNERS[1]}'] = -1
    if fault == 'antenna': antenna['antenna__violating__nets'] = antenna['antenna__violating__pins'] = 1
    if fault == 'electrical': electrical[CORNERS[1]]['counts']['slew'] = 1
    result = assess(values, electrical, antenna)
    assert result['final_measured_gates_passed'] is (fault is None)
    assert result['release_qualified'] is False and result['source_screen_qualified'] is False
    assert result['official_gds_qualified'] is False and result['hardware_promoted'] is False
