from copy import deepcopy
from pathlib import Path

import pytest

from closure_clock_probe import context, configure, reference_matches, PERIODS, REFERENCE, ARTIFACT_ID, ARCHIVE_SHA
from test_closure_final_gl import context as route_context


def test_only_exact_failed_route_is_a_diagnostic_source():
    run, artifact = route_context()
    run['conclusion'] = 'failure'; artifact.update(id=ARTIFACT_ID, digest=ARCHIVE_SHA)
    context(run, artifact)
    for key, value in [('conclusion', 'success'), ('status', 'in_progress'), ('head_sha', 'other')]:
        changed = dict(run); changed[key] = value
        with pytest.raises(ValueError): context(changed, artifact)


@pytest.mark.parametrize('period', PERIODS)
def test_period_probe_keeps_physical_controls_and_source_unchanged(period):
    original = dict(CLOCK_PERIOD=20, MACROS={'pinned': 'views'}, GRT_ADJUSTMENT=.16,
                    STA_CORNERS=['original'], STA_THREADS=3)
    before = deepcopy(original)
    result = configure(original, period, Path('/preserved/effective-signoff.sdc'))
    assert original == before
    assert result['CLOCK_PERIOD'] == period
    assert result['MACROS'] == original['MACROS'] and result['GRT_ADJUSTMENT'] == .16
    assert set(k for k in result if original.get(k) != result[k]) <= {
        'CLOCK_PERIOD', 'STA_CORNERS', 'STA_THREADS', 'SIGNOFF_SDC_FILE'}


@pytest.mark.parametrize('period', [19, 23, 30, True, 25.0])
def test_unreviewed_periods_refused(period):
    with pytest.raises(ValueError): configure({'CLOCK_PERIOD': 20}, period, Path('/sdc'))


def test_baseline_failure_is_not_relabelled_or_tolerated():
    ref = {f'timing__{kind}__ws__corner:{c}': value
           for c, pair in REFERENCE.items() for kind, value in zip(('setup', 'hold'), pair)}
    reference_matches(ref)
    key = 'timing__setup__ws__corner:nom_slow_1p08V_125C'
    for value in (0, float('nan'), True):
        changed = dict(ref); changed[key] = value
        with pytest.raises(ValueError): reference_matches(changed)


def test_unreviewed_extra_tcl_refused():
    with pytest.raises(ValueError): configure({'CLOCK_PERIOD': 20, 'STA_EXTRA_CORNER_TCL_FILE': 'other.tcl'}, 25, Path('/sdc'))
