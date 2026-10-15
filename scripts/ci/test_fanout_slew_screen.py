from pathlib import Path
import pytest
from fanout_slew_plan import BINDING,plan
from fanout_slew_screen import PROFILE


def test_timing_passing_source_has_only_measured_electrical_repairs():
    assert BINDING['source_run']==PROFILE['source_run']==38668749394
    assert BINDING['electrical_nets']==3
    assert BINDING['hold_count']==0 and BINDING['hold_target_ns']==.075
    assert BINDING['setup']==BINDING['targets']=={}
    assert PROFILE['run_binding']['head_sha']=='e54a07b661a53337e16b49aca846cafc0efbef1d'
    assert PROFILE['run_binding']['conclusion']=='failure'
    assert PROFILE['post_antenna_audit'] is not None


def test_stale_source_is_refused_before_loading_geometry():
    with pytest.raises(ValueError,match='Wrong combined source'):
        plan('wrong','wrong','wrong',{},Path('missing.lef'),Path('missing_macro.lef'))


def test_manual_workflow_matches_exact_route_and_screen_helper():
    import yaml
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/gds-fanout-slew-screen.yaml').read_text())
    steps=w['jobs']['harden']['steps']
    d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38668749394
    assert d['with']['name']=='gds-fanout-finish-route-38668749394'
    assert any(s.get('run')=='python workflow-src/scripts/ci/fanout_slew_screen.py' for s in steps)
    assert 'detailedrouting' not in str(w).lower()


def test_small_gate_artifact_requires_current_screen_receipt():
    import yaml
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/gds-fanout-slew-screen.yaml').read_text())
    uploads=[s for s in w['jobs']['harden']['steps'] if 'upload-artifact@' in s.get('uses','')]
    assert len(uploads)==2
    first,bulk=uploads
    assert first['if']=="always() && hashFiles('runs/fanout-slew-screen/gates.json') != ''"
    assert 'runs/fanout-slew-screen/timing/comparison.json' in first['with']['path']
    assert first['with']['name']!=bulk['with']['name']
    assert 'runs/**' in bulk['with']['path']
