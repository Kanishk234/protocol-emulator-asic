import pytest
from electrical_report import audit, audit_corners


def test_classifies_each_limit_without_counting_timing_failures():
    report = '''setup slack -1 (VIOLATED)
max slew
pin 1 2 -1 (VIOLATED)
max fanout
pin 8 9 (VIOLATED)
max capacitance
pin .064 .129 -.065 (VIOLATED)
===========================================================================
another path (VIOLATED)
'''
    result = audit(report)
    assert result['counts'] == {'slew': 1, 'fanout': 1, 'capacitance': 1}
    assert not result['no_reported_electrical_violations']
    assert result['official_signoff'] is False


def test_complete_empty_sections():
    assert audit('max slew\nmax fanout\nmax capacitance')['no_reported_electrical_violations']


@pytest.mark.parametrize('text', ['', 'max slew\nmax capacitance',
                                  'max slew\nmax fanout\nmax capacitance\nmax slew'])
def test_incomplete_or_duplicate_sections_rejected(text):
    with pytest.raises(ValueError):
        audit(text)


def test_truncated_rows_cannot_hide_printed_violations():
    with pytest.raises(ValueError, match='printed total'):
        audit('max slew\nmax fanout\nmax capacitance\nmax slew violation count 1\n')


def test_corner_evidence_is_required(tmp_path):
    stage = tmp_path / 'slow'
    stage.mkdir()
    report = stage / 'checks.rpt'
    report.write_text('slow Corner\nmax slew\nmax fanout\nmax capacitance\n')
    assert audit_corners(tmp_path, ['slow'])['slow']['counts']['slew'] == 0
    with pytest.raises(FileNotFoundError):
        audit_corners(tmp_path, ['slow', 'fast'])
    report.write_text('fast Corner\nmax slew\nmax fanout\nmax capacitance\n')
    with pytest.raises(ValueError, match='corner mismatch'):
        audit_corners(tmp_path, ['slow'])
