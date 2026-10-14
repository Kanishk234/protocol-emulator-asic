from pathlib import Path
import pytest
from final_combined_plan import BINDING,plan
from final_combined_screen import PROFILE


def test_exact_source_requires_measured_hold_and_electrical_repairs():
    assert BINDING['source_run']==PROFILE['source_run']==38515215944
    assert BINDING['electrical_nets']==3
    assert BINDING['hold_count']==0 and BINDING['hold_target_ns']==.075
    assert BINDING['setup']=={'_24896_':'sg13cmos5l_nor2_2'}
    assert BINDING['targets']=={'_24896_':('sg13cmos5l_nor2_1','sg13cmos5l_nor2_2')}
    assert PROFILE['run_binding']['head_sha']=='ad0f3ec1fa2bf66341ca79ef00df6f51a09b0066'
    assert PROFILE['run_binding']['conclusion']=='failure'
    assert PROFILE['post_antenna_audit'] is not None


def test_stale_source_is_refused_before_loading_geometry():
    with pytest.raises(ValueError,match='Wrong combined source'):
        plan('wrong','wrong','wrong',{},Path('missing.lef'),Path('missing_macro.lef'))


def test_manual_workflow_matches_exact_route_and_screen_helper():
    import yaml
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/gds-final-combined-screen.yaml').read_text())
    steps=w['jobs']['harden']['steps']
    d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38515215944
    assert d['with']['name']=='gds-hold-electrical-route-38515215944'
    assert any(s.get('run')=='python workflow-src/scripts/ci/final_combined_screen.py' for s in steps)
    assert 'detailedrouting' not in str(w).lower()
