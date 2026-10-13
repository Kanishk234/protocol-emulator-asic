from pathlib import Path
import pytest
import combined_physical_plan as engine
from residual_combined_plan import BINDING,plan,target_call


def test_binding_uses_new_source_without_repeating_existing_repairs():
    assert BINDING['source_run']==38336141213
    assert BINDING['hold_count']==32 and BINDING['electrical_nets']==8
    assert set(BINDING['setup'])=={'_43582_','hold12766','_43311_'}
    assert BINDING['prefix']=='tripwire_residual_'
    assert BINDING['hold_target_ns']==.075
    assert not set(engine.SETUP)&set(BINDING['setup'])
    assert set(BINDING['checks_sha'])=={'nom_fast_1p32V_m40C','nom_typ_1p20V_25C','nom_slow_1p08V_125C'}


def test_new_source_refuses_old_checkpoint_inputs(tmp_path):
    with pytest.raises(ValueError,match='Wrong combined source'):plan('old','old','old',{},tmp_path/'std.lef',tmp_path/'macro.lef')
    with pytest.raises(ValueError,match='Wrong combined Tcl source'):target_call('old',{'source_run':38336141213,'def_sha256':BINDING['def_sha']})


def test_profile_does_not_change_default_combined_source():
    d=engine.source_binding()
    assert d['source_run']==38305592967 and d['hold_count']==19 and d['electrical_nets']==29
    assert d['prefix']=='tripwire_combined_'


def test_prepared_workflow_binds_residual_source_and_cannot_route():
    import yaml
    from residual_combined_screen import PROFILE
    p=Path(__file__).resolve().parents[2]/'.github/workflows/gds-residual-combined-screen.yaml'
    w=yaml.safe_load(p.read_text());steps=w['jobs']['harden']['steps']
    d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==BINDING['source_run']
    assert d['with']['name']==f"gds-combined-physical-route-{BINDING['source_run']}"
    assert any(s.get('run')=='python workflow-src/scripts/ci/residual_combined_screen.py' for s in steps)
    assert PROFILE['route_root']=='runs/combined-physical-route'
    assert PROFILE['output_root']=='runs/residual-combined-screen'
    assert PROFILE['run_binding']['conclusion']=='failure'


def test_selected_setup_matches_smallest_successful_diagnostic():
    from residual_delay_sensitivity import CASES
    assert {n:m for n,m in BINDING['setup'].items() if n!='_43311_'}==CASES['medium12766']
    assert 'hold12715' not in BINDING['setup']
