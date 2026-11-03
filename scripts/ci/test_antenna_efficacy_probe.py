import pytest
from antenna_efficacy_probe import separation, sink_violation
from protected_endpoint_probe import connectivity


def test_only_target_sink_counts():
    text = 'Net: other\n  Pin: trw_ap_sink/A (buf)\n(VIOLATED)\n'
    assert not sink_violation(text)
    assert sink_violation(text.replace('other', 'trw_ap_node'))
    assert not sink_violation(text.replace('other', 'trw_ap_node').replace('trw_ap_sink/A', 'trw_ap_driver/A'))


def test_def_distance_and_missing_instance():
    text = '''UNITS DISTANCE MICRONS 1000 ;
COMPONENTS 2 ;
- trw_ap_driver buf + PLACED ( 300000 350000 ) N ;
- trw_ap_sink buf + PLACED ( 900000 350000 ) N ;
END COMPONENTS'''
    assert separation(text) == 600
    with pytest.raises(ValueError, match='Missing relay'):
        separation(text.replace('trw_ap_sink', 'missing'))


def test_absent_diode_control():
    text = 'sg13cmos5l_buf_2 trw_ap_driver (.A(a),.X(n));\nsg13cmos5l_buf_2 trw_ap_sink (.A(n),.X(y));'
    assert connectivity(text, False)
    assert not connectivity(text, True)
    assert not connectivity(text + '\nsg13cmos5l_antennanp unexpected (.A(n));', False)


def test_repairable_driver_still_requires_buffer_and_same_node():
    text = 'sg13cmos5l_buf_4 trw_ap_driver (.A(a),.X(n));\nsg13cmos5l_buf_2 trw_ap_sink (.A(n),.X(y));'
    assert not connectivity(text, False)
    assert connectivity(text, False, True)
    assert not connectivity(text.replace('sg13cmos5l_buf_4', 'sg13cmos5l_nand2_1'), False, True)
    assert not connectivity(text.replace('.A(n)', '.A(other)'), False, True)
