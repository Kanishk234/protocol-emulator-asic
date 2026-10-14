from pathlib import Path
import pytest
from strength_residual_plan import BINDING,plan
from strength_residual_screen import PROFILE


def test_timing_passing_source_has_only_measured_electrical_repairs():
    assert BINDING['source_run']==PROFILE['source_run']==38499287760
    assert BINDING['electrical_nets']==7
    assert BINDING['hold_count']==0 and BINDING['hold_target_ns']==.075
    assert BINDING['setup']==BINDING['targets']=={}
    assert PROFILE['run_binding']['head_sha']=='0501e0a50a5fb3832c6ac81d6fa48b6fe330555d'
    assert PROFILE['run_binding']['conclusion']=='failure'
    assert PROFILE['post_antenna_audit'] is not None


def test_stale_source_is_refused_before_loading_geometry():
    with pytest.raises(ValueError,match='Wrong combined source'):
        plan('wrong','wrong','wrong',{},Path('missing.lef'),Path('missing_macro.lef'))


def test_manual_workflow_matches_exact_route_and_screen_helper():
    import yaml
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/gds-strength-residual-screen.yaml').read_text())
    steps=w['jobs']['harden']['steps']
    d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38499287760
    assert d['with']['name']=='gds-strength-fanout-route-38499287760'
    assert any(s.get('run')=='python workflow-src/scripts/ci/strength_residual_screen.py' for s in steps)
    assert 'detailedrouting' not in str(w).lower()
