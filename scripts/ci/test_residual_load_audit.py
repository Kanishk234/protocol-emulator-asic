import pytest
from residual_load_audit import inspect

NL = '''sg13cmos5l_buf_4 driver (.A(a), .X(n));
sg13cmos5l_buf_1 sink (.A(n), .X(q));
sg13cmos5l_antennanp diode (.A(n));'''
REPORT = '''max slew
max fanout
driver/X 1 2 -1 (VIOLATED)
max capacitance
max slew violation count 0
max fanout violation count 1
max cap violation count 0
'''


def test_diode_loads_are_counted_and_not_reclassified_as_logic():
    r = inspect(NL, REPORT)
    assert r['branches'][0]['actual_sink_pins'] == 2
    assert r['branches'][0]['diode_pins'] == 1
    assert r['branches'][0]['other_pins'] == 1
    assert not r['physical_change_applied']


@pytest.mark.parametrize('report', [REPORT.replace('driver/X', 'absent/X'),
                                   REPORT.replace('max capacitance\n', ''),
                                   REPORT.replace('fanout violation count 1', 'fanout violation count 0')])
def test_incomplete_or_mismatched_evidence_is_rejected(report):
    with pytest.raises(ValueError):
        inspect(NL, report)
