from pathlib import Path
import os
import subprocess
import pytest
from decode_combined_plan import BINDING,plan
from decode_combined_screen import PROFILE
from postant_setup_sensitivity import CASES


def test_selected_source_and_two_gate_candidate_match_measured_diagnostic():
    assert BINDING['source_run']==38358706808
    assert BINDING['setup']==CASES['two_gates']
    assert BINDING['hold_count']==4 and BINDING['hold_target_ns']==.075
    assert BINDING['electrical_nets']==12
    assert PROFILE.get('source_kind','detailed-route')=='detailed-route'
    assert PROFILE['run_binding']['path']=='.github/workflows/gds-postant-route.yaml'
    assert PROFILE['post_antenna_audit'] is not None
    with pytest.raises(ValueError,match='Wrong combined source'):
        plan('wrong','wrong','wrong',{},Path('std.lef'),Path('macro.lef'))


def test_wrapper_clears_actual_detailed_wires_before_full_route_and_postant_repair(tmp_path):
    binary=tmp_path/'openroad';binary.write_text('#!/bin/bash\ncat "${@: -1}"\n');binary.chmod(0o755)
    source='source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl'
    p=tmp_path/'grt.tcl';p.write_text('read_current_odb\n'+source+'\nwrite_views\n')
    env=dict(os.environ,PATH=str(tmp_path)+os.pathsep+os.environ['PATH'],RUNNER_TEMP=str(tmp_path))
    r=subprocess.run(['bash',str(Path(__file__).with_name('openroad_decode_combined_wrapper.sh')),str(p)],env=env,text=True,capture_output=True)
    assert r.returncode==0 and r.stdout.count(source)==1
    assert r.stdout.index('tripwire_clear_native_signal_routes')<r.stdout.index(source)<r.stdout.index('tripwire_post_antenna_finish')
    assert 'tripwire_require_unrouted_screen_source' not in r.stdout


def test_exact_source_workflow_never_performs_detailed_routing():
    import yaml
    root=Path(__file__).resolve().parents[2];w=yaml.safe_load((root/'.github/workflows/gds-decode-combined-screen.yaml').read_text())
    steps=w['jobs']['harden']['steps'];d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38358706808 and d['with']['name']=='gds-postant-route-38358706808'
    assert any(s.get('run')=='python workflow-src/scripts/ci/decode_combined_screen.py' for s in steps)
    assert 'OpenROAD.DetailedRouting' not in (root/'scripts/ci/combined_physical_screen.py').read_text()
