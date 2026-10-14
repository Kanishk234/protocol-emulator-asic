from pathlib import Path
import pytest
from sram_residual_plan import BINDING,plan
from sram_residual_screen import PROFILE


def test_timing_passing_source_has_only_measured_electrical_repairs():
    assert BINDING['source_run']==PROFILE['source_run']==38621290574
    assert BINDING['electrical_nets']==4
    assert BINDING['hold_count']==0 and BINDING['hold_target_ns']==.075
    assert BINDING['setup']==BINDING['targets']=={}
    assert PROFILE['run_binding']['head_sha']=='372fcace90fd6bc278a099dcc7fd677dc7134bae'
    assert PROFILE['run_binding']['conclusion']=='failure'
    assert PROFILE['post_antenna_audit'] is not None


def test_stale_source_is_refused_before_loading_geometry():
    with pytest.raises(ValueError,match='Wrong combined source'):
        plan('wrong','wrong','wrong',{},Path('missing.lef'),Path('missing_macro.lef'))


def test_manual_workflow_matches_exact_route_and_screen_helper():
    import yaml
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/gds-sram-residual-screen.yaml').read_text())
    steps=w['jobs']['harden']['steps']
    d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38621290574
    assert d['with']['name']=='gds-final-combined-route-38621290574'
    assert any(s.get('run')=='python workflow-src/scripts/ci/sram_residual_screen.py' for s in steps)
    assert 'detailedrouting' not in str(w).lower()
