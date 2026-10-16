import copy

import pytest

from native_margin_screen import configure, evaluate
from native_stock_screen import configure as stock_configure
from postgrt_timing import CORNERS


def test_native_margin_changes_only_reviewed_policy(tmp_path):
    base = stock_configure(dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56),
                           'AREA 1', tmp_path/'src/signoff.sdc',
                           hold_target=.10, clock_cluster=8)
    original = copy.deepcopy(base)
    result = configure(base)
    assert base == original
    changed = {k for k in result if result[k] != base.get(k)}
    assert changed == {'RUN_POST_GRT_DESIGN_REPAIR', 'GRT_DESIGN_REPAIR_MAX_SLEW_PCT',
                       'GRT_DESIGN_REPAIR_MAX_CAP_PCT', 'GRT_ALLOW_CONGESTION',
                       'ERROR_ON_MAGIC_DRC', 'ERROR_ON_ILLEGAL_OVERLAPS'}
    assert result['GRT_DESIGN_REPAIR_MAX_SLEW_PCT'] == 55
    assert result['GRT_DESIGN_REPAIR_MAX_CAP_PCT'] == 55
    for key in ('PNR_SDC_FILE', 'SIGNOFF_SDC_FILE', 'GRT_RESIZER_HOLD_SLACK_MARGIN', 'meta'):
        assert result[key] == base[key]
    for key, value in [('CLOCK_PERIOD', 25), ('CTS_SINK_CLUSTERING_SIZE', 16),
                       ('GRT_RESIZER_HOLD_SLACK_MARGIN', .125), ('RSZ_CORNERS', [CORNERS[1]])]:
        with pytest.raises(ValueError):
            configure(dict(base, **{key: value}))


def evidence():
    timing = {'corners': {c: {'after': {f'timing__setup__ws__corner:{c}': 0,
                                      f'timing__hold__ws__corner:{c}': .1}}
                          for c in CORNERS}}
    antenna = {'antenna__violating__nets': 0, 'antenna__violating__pins': 0}
    reports = {c: 'max slew violation count 0\nmax fanout violation count 0\nmax cap violation count 0\n'
               for c in CORNERS}
    return timing, antenna, reports, {'estimated_margin_pass': True}


def test_strict_gate_accepts_measured_clean_screen_only():
    result = evaluate(*evidence())
    assert result['qualified'] is True
    assert result['official_signoff'] is False
    assert result['checkpoint_ecos'] is False
    assert result['antenna']['antenna__violating__nets'] == 0


@pytest.mark.parametrize('failure', ['setup', 'hold', 'antenna', 'electrical', 'margin'])
def test_each_independent_failure_blocks_routing(failure):
    timing, antenna, reports, margin = evidence()
    if failure == 'setup':
        timing['corners'][CORNERS[1]]['after'][f'timing__setup__ws__corner:{CORNERS[1]}'] = -.001
    elif failure == 'hold':
        timing['corners'][CORNERS[0]]['after'][f'timing__hold__ws__corner:{CORNERS[0]}'] = .049
    elif failure == 'antenna':
        antenna['antenna__violating__nets'] = 1
    elif failure == 'electrical':
        reports[CORNERS[1]] = ('max slew\nnet 1 2 -1 (VIOLATED)\n'
                              'max slew violation count 1\nmax fanout violation count 0\nmax cap violation count 0\n')
    else:
        margin['estimated_margin_pass'] = False
    assert evaluate(timing, antenna, reports, margin)['qualified'] is False
    if failure == 'antenna':
        assert evaluate(timing, antenna, reports, margin)['antenna']['antenna__violating__nets'] == 1


def test_missing_electrical_evidence_rejected():
    timing, antenna, reports, margin = evidence()
    reports[CORNERS[1]] = ''
    with pytest.raises(ValueError):
        evaluate(timing, antenna, reports, margin)


def test_watched_recipe_changes_only_logging(tmp_path):
    from native_margin_watched_screen import configure as watched
    source = stock_configure(dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56),
                             'AREA 1', tmp_path/'src/signoff.sdc',
                             hold_target=.10, clock_cluster=8)
    expected = configure(source)
    result = watched(source)
    assert result.pop('YOSYS_LOG_LEVEL') == 'WARNING'
    assert result == expected


def test_wire_repair_trial_changes_only_positive_wire_limit(tmp_path):
    from native_margin_watched_screen import configure as watched
    from native_margin_wire_screen import configure as wire_repair
    source = stock_configure(dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56),
                             'AREA 1', tmp_path/'src/signoff.sdc',
                             hold_target=.10, clock_cluster=8)
    expected = watched(source)
    result = wire_repair(source)
    assert result.pop('GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH') == 200
    assert result == expected


def test_clockspacing_trial_preserves_wire_repair_and_all_constraints(tmp_path):
    from native_margin_wire_screen import configure as wire_repair
    from native_clockspacing_screen import configure as clockspacing
    source = stock_configure(dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56),
                             'AREA 1', tmp_path/'src/signoff.sdc',
                             hold_target=.10, clock_cluster=8)
    expected = wire_repair(source)
    result = clockspacing(source)
    assert result.pop('CTS_DISTANCE_BETWEEN_BUFFERS') == 100
    assert result == expected


def test_shortwire_changes_only_data_wire_length(tmp_path):
    from native_clockspacing_screen import configure as clockspacing
    from native_shortwire_screen import configure as shortwire
    source = stock_configure(dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56),
                             'AREA 1', tmp_path/'src/signoff.sdc',
                             hold_target=.10, clock_cluster=8)
    expected = clockspacing(source)
    result = shortwire(source)
    assert result['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH'] == 100
    assert expected.pop('GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH') == 200
    result.pop('GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH')
    assert result == expected


def test_antenna_margin_changes_one_repair_target_and_preserves_constraints(tmp_path):
    from native_shortwire_screen import configure as shortwire
    from native_antenna_margin_screen import configure as antenna_margin
    source = stock_configure(dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56,
                                  GRT_ANTENNA_REPAIR_MARGIN=10),
                             'AREA 1', tmp_path/'src/signoff.sdc',
                             hold_target=.10, clock_cluster=8)
    expected = shortwire(source)
    result = antenna_margin(source)
    assert result.pop('GRT_ANTENNA_REPAIR_MARGIN') == 50
    assert expected.pop('GRT_ANTENNA_REPAIR_MARGIN') == 10
    assert result == expected
    with pytest.raises(ValueError):
        antenna_margin(dict(source, GRT_ANTENNA_REPAIR_MARGIN=30))
