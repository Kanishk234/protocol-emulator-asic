from pathlib import Path
import pytest
from screen_fanout_finish_plan import BINDING,plan
from screen_fanout_finish import PROFILE
from extracted_hold_targets import endpoints


def hold(slack):
    return f'nom_fast_1p32V_m40C\nStartpoint: latch\nEndpoint: flop (rising edge-triggered flip-flop clocked by clk)\n {slack} slack (MET)\n'


def test_no_delay_candidate_requires_complete_timing_report():
    assert endpoints(hold('.0751412'),.075,allow_empty=True)=={}
    assert endpoints(hold('.049'),.075,allow_empty=True)=={'flop':.049}
    with pytest.raises(ValueError):endpoints('nom_fast_1p32V_m40C',.075,allow_empty=True)
    with pytest.raises(ValueError):endpoints(hold('.0751412'),.075)


def test_fanout_only_source_binding_preserves_timing_acceptance():
    assert BINDING['source_run']==38349702735
    assert BINDING['hold_count']==0 and BINDING['hold_target_ns']==.075
    assert not BINDING['setup'] and BINDING['electrical_nets']==2
    assert PROFILE['source_gate_receipt']['minimum_fast_hold_ns']==.05
    assert PROFILE['source_gate_receipt']['added_buffers']==54
    assert PROFILE['source_gate_receipt']['source_global_screen'] is True
    with pytest.raises(ValueError,match='Wrong combined source'):
        plan('old','old','old',{},Path('std.lef'),Path('macro.lef'))


def test_workflow_uses_actual_timing_clean_failed_screen():
    import yaml
    p=Path(__file__).resolve().parents[2]/'.github/workflows/gds-screen-fanout-finish.yaml'
    steps=yaml.safe_load(p.read_text())['jobs']['harden']['steps']
    d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['name']=='gds-screen-followup-38349702735'
    assert d['with']['run-id']==38349702735
    assert any(s.get('run')=='python workflow-src/scripts/ci/screen_fanout_finish.py' for s in steps)
