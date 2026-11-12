import pytest

from functional_setup_frontier import parse_report


def report(slacks):
    return ('TRIPWIRE_FUNCTIONAL_SETUP slow\nFLOP_DATA_ENDPOINTS 100\nOUTPUT_ENDPOINTS 24\n'
            + '\n'.join(f'{s} slack (MET)' for s in slacks))


def test_positive_and_negative_actual_slacks():
    assert parse_report(report(['0.15','0.32']), 'slow')['worst_reported_setup_slack_ns'] == .15
    assert parse_report(report(['0.15','-2.435476']), 'slow')['worst_reported_setup_slack_ns'] == -2.435476


def test_clamped_summary_is_insufficient():
    with pytest.raises(ValueError, match='No actual'):
        parse_report(report([])+'\nworst slack 0.00\n', 'slow')


def test_wrong_corner_and_missing_endpoints_fail():
    with pytest.raises(ValueError, match='exact-corner'):
        parse_report(report(['1']), 'fast')
    with pytest.raises(ValueError, match='flop endpoints'):
        parse_report(report(['1']).replace('ENDPOINTS 100', 'ENDPOINTS 0'), 'slow')


def test_nonfinite_value_fails():
    with pytest.raises(ValueError, match='Nonfinite'):
        parse_report(report(['nan']), 'slow')
