import json
from pathlib import Path
import pytest
from electrical_risk_inventory import inventory
from electrical_margin_gate import enforce
from margin_risk_plan import BINDING, PROTECTED, plan
from margin_risk_screen import PROFILE
from postgrt_timing import CORNERS


def evidence(ratio=.46):
    return dict(source_run=38689478738, read_only=True,
        stages={'screen': {c: {'nets': {'n': {'slew': {'utilization': ratio}}}} for c in CORNERS}})


def fixture(pin='A'):
    nl = 'sg13cmos5l_buf_1 driver (.A(in),.X(n)); sg13cmos5l_buf_1 sink (.A(n),.X(out));'
    layout = '\nNETS 1 ;\n- n ( driver X ) ( sink '+pin+' ) ;\nEND NETS\n'
    return nl, layout


def test_risk_class_includes_legal_but_underestimated_slew():
    nl, layout = fixture()
    assert inventory(evidence(), nl, layout)['sources'] == {'n': ['slew']}
    assert inventory(evidence(.4), nl, layout)['sources'] == {}


def test_clock_or_reset_pins_are_not_rewired():
    nl, layout = fixture('GATE')
    result = inventory(evidence(), nl, layout)
    assert result['sources'] == {}
    assert result['protected_sources'] == {'n': ['slew']}


def test_complete_diagnostic_and_exact_source_required():
    nl, layout = fixture()
    data = evidence(); del data['stages']['screen'][CORNERS[0]]
    with pytest.raises(ValueError): inventory(data, nl, layout)
    with pytest.raises(ValueError, match='Wrong margin-risk netlist'):
        plan('wrong', 'wrong')


def test_missing_margin_reports_revoke_previous_qualification(tmp_path):
    path = tmp_path/'gates.json'; path.write_text(json.dumps(dict(qualified=True)))
    with pytest.raises(ValueError): enforce(tmp_path)
    assert json.loads(path.read_text())['qualified'] is False


def test_preventive_set_and_source_binding_are_fixed():
    assert BINDING['source_run'] == PROFILE['source_run'] == 38689478738
    assert BINDING['electrical_nets'] == 4
    assert len(BINDING['preventive_sources']) == 64
    assert len(PROTECTED) == 1
    assert PROFILE['electrical_margin_tcl'].endswith('electrical_margin_probe.tcl')
    assert BINDING['hold_count'] == 0


def test_workflow_downloads_both_exact_evidence_sets_and_stops_before_drt():
    import yaml
    root = Path(__file__).resolve().parents[2]
    w = yaml.safe_load((root/'.github/workflows/gds-margin-risk-screen.yaml').read_text())
    steps = w['jobs']['harden']['steps']
    downloads = [s['with'] for s in steps if 'download-artifact@' in s.get('uses', '')]
    assert [s['run-id'] for s in downloads] == [38689478738, 38762064184]
    assert downloads[1]['path'] == 'runs/electrical-margin-probe'
    assert any(s.get('run') == 'python workflow-src/scripts/ci/margin_risk_screen.py' for s in steps)
    assert 'detailedrouting' not in str(w).lower()


@pytest.mark.parametrize('actual,passes', [(1.0,True),(1.2,False)])
def test_global_margin_checks_legal_rows_at_every_corner(tmp_path, actual, passes):
    (tmp_path/'gates.json').write_text(json.dumps(dict(qualified=True)))
    for corner in CORNERS:
        stage=tmp_path/'timing'/('after-'+corner)/'1-openroad-stamidpnr'
        stage.mkdir(parents=True)
        (stage/'electrical_margin.rpt').write_text(
            f'TRIPWIRE_MARGIN_BEGIN {corner}\nTRIPWIRE_NET_HEX 6e\n'
            f'max slew\nsink/A 2.5 {actual} 0.1 (MET)\n'
            f'max capacitance\ndriver/X 0.3 0.1 0.2 (MET)\n'
            f'TRIPWIRE_MARGIN_END {corner} 1\n')
    if passes:enforce(tmp_path)
    else:
        with pytest.raises(ValueError, match='Conservative global'):enforce(tmp_path)
    result=json.loads((tmp_path/'gates.json').read_text())
    assert result['qualified'] is passes
    assert result['estimated_margin_pass'] is passes
