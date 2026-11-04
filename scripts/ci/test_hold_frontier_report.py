import pytest

from hold_frontier_report import summarize


def report(tmp_path, body):
    path = tmp_path / 'hold_frontier.rpt'
    path.write_text('TRIPWIRE_HOLD_FRONTIER_BEGIN fast 0.05 100000\n' + body +
                    '\nTRIPWIRE_HOLD_FRONTIER_END fast\n')
    return path


def test_shortfall_and_scope(tmp_path):
    path = report(tmp_path, 'Startpoint: a (flip-flop)\nEndpoint: b (flip-flop)\n'
                  'Path Type: min\n -0.016328 slack (VIOLATED)\n')
    result = summarize(path, 'fast')
    assert result['reported_negative_paths'] == 1
    assert result['paths'][0]['reserve_shortfall_ns'] == 0.066328
    assert result['exhaustive_endpoint_coverage_claimed'] is False


def test_explicit_empty_report(tmp_path):
    assert summarize(report(tmp_path, 'No paths found.'), 'fast')['reported_paths'] == 0


@pytest.mark.parametrize('body', ['', 'Startpoint: a\nEndpoint: b\nPath Type: min\n',
    'Startpoint: a\nEndpoint: b\nPath Type: max\n 0.01 slack (MET)\n',
    'Startpoint: a\nEndpoint: b\nPath Type: min\n 0.06 slack (MET)\n'])
def test_incomplete_or_wrong_paths_reject(tmp_path, body):
    with pytest.raises(ValueError):
        summarize(report(tmp_path, body), 'fast')


def test_wrong_corner_rejects(tmp_path):
    with pytest.raises(ValueError):
        summarize(report(tmp_path, 'No paths found.'), 'slow')
