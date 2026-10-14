from pathlib import Path
import pytest
from hold_electrical_plan import BINDING,plan
from hold_electrical_screen import PROFILE


def test_exact_source_requires_measured_hold_and_electrical_repairs():
    assert BINDING['source_run']==PROFILE['source_run']==38507730942
    assert BINDING['electrical_nets']==4
    assert BINDING['hold_count']==132 and BINDING['hold_target_ns']==.1
    assert BINDING['setup']==BINDING['targets']=={}
    assert PROFILE['run_binding']['head_sha']=='c242b5a71ae48252fafcafde8d197b202f6001f9'
    assert PROFILE['run_binding']['conclusion']=='failure'
    assert PROFILE['post_antenna_audit'] is not None


def test_stale_source_is_refused_before_loading_geometry():
    with pytest.raises(ValueError,match='Wrong combined source'):
        plan('wrong','wrong','wrong',{},Path('missing.lef'),Path('missing_macro.lef'))


def test_manual_workflow_matches_exact_route_and_screen_helper():
    import yaml
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/gds-hold-electrical-screen.yaml').read_text())
    steps=w['jobs']['harden']['steps']
    d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38507730942
    assert d['with']['name']=='gds-strength-residual-route-38507730942'
    assert any(s.get('run')=='python workflow-src/scripts/ci/hold_electrical_screen.py' for s in steps)
    assert 'detailedrouting' not in str(w).lower()
