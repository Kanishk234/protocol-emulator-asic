from pathlib import Path
import pytest
from fanout_finish_plan import BINDING,plan
from fanout_finish_screen import PROFILE


def test_timing_passing_source_has_only_measured_electrical_repairs():
    assert BINDING['source_run']==PROFILE['source_run']==38641675550
    assert BINDING['electrical_nets']==2
    assert BINDING['hold_count']==0 and BINDING['hold_target_ns']==.075
    assert BINDING['setup']==BINDING['targets']=={}
    assert PROFILE['run_binding']['head_sha']=='44cdfdff239a63813b91f1678dc3503c94f37213'
    assert PROFILE['run_binding']['conclusion']=='failure'
    assert PROFILE['post_antenna_audit'] is not None


def test_stale_source_is_refused_before_loading_geometry():
    with pytest.raises(ValueError,match='Wrong combined source'):
        plan('wrong','wrong','wrong',{},Path('missing.lef'),Path('missing_macro.lef'))


def test_manual_workflow_matches_exact_route_and_screen_helper():
    import yaml
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/gds-fanout-finish-screen.yaml').read_text())
    steps=w['jobs']['harden']['steps']
    d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38641675550
    assert d['with']['name']=='gds-sram-residual-route-38641675550'
    assert any(s.get('run')=='python workflow-src/scripts/ci/fanout_finish_screen.py' for s in steps)
    assert 'detailedrouting' not in str(w).lower()
