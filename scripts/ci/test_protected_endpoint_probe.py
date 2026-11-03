from protected_endpoint_probe import connectivity
import json
import pytest
from protected_endpoint_probe import main


TEXT = '''sg13cmos5l_buf_2 trw_ap_driver (.A(a), .X(n));
sg13cmos5l_buf_2 trw_ap_sink (.A(n), .X(y));
sg13cmos5l_antennanp trw_ap_diode (.A(n));'''


def test_intact():
    assert connectivity(TEXT)


def test_wrong_diode_node():
    assert not connectivity(TEXT.replace('trw_ap_diode (.A(n))', 'trw_ap_diode (.A(a))'))


def test_missing_sink():
    assert not connectivity(TEXT.replace('trw_ap_sink', 'removed'))


def test_wrong_sink_master():
    assert not connectivity(TEXT.replace('sg13cmos5l_buf_2 trw_ap_sink', 'sg13cmos5l_buf_1 trw_ap_sink'))


@pytest.mark.parametrize('case', ['intact', 'missing_stage', 'wrong_node', 'unprotected'])
def test_native_result_gate(tmp_path, monkeypatch, case):
    stages = ['repairdesignpostgpl', 'resizertimingpostcts',
              'repairdesignpostgrt', 'resizertimingpostgrt']
    for i, stage in enumerate(stages):
        p = tmp_path / f'{i}-openroad-{stage}'
        p.mkdir()
        message = "Net matched don't touch regular expression"
        if case == 'unprotected' or (case == 'missing_stage' and i == 0):
            message = ''
        (p / f'openroad-{stage}.log').write_text(message)
    text = TEXT if case in ('intact', 'missing_stage') else TEXT.replace('trw_ap_diode (.A(n))', 'trw_ap_diode (.A(a))')
    (tmp_path / '3-openroad-resizertimingpostgrt/probe.nl.v').write_text(text)
    p = tmp_path / '4-openroad-stamidpnr-3'
    p.mkdir()
    (p / 'or_metrics_out.json').write_text(json.dumps({'timing__setup__ws__corner:typ': 0}))
    monkeypatch.setattr('sys.argv', ['probe', str(tmp_path), '--protected',
                                    'false' if case == 'unprotected' else 'true'])
    if case in ('missing_stage', 'wrong_node'):
        with pytest.raises(ValueError, match='not preserved'):
            main()
    else:
        main()
    result = json.loads((tmp_path / 'probe_result.json').read_text())
    assert result['full_design_qualification'] is False
    if case == 'unprotected':
        assert result['connectivity_preserved'] is False
