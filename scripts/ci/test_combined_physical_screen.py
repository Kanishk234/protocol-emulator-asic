import os
from pathlib import Path
import subprocess
import pytest
from combined_physical_screen import validate_placements


def wrapper(tmp_path,name,text):
    binary=tmp_path/'openroad';binary.write_text('#!/bin/bash\ncat "${@: -1}"\n');binary.chmod(0o755)
    script=tmp_path/name;script.write_text(text)
    env=dict(os.environ,PATH=str(tmp_path)+os.pathsep+os.environ['PATH'],RUNNER_TEMP=str(tmp_path))
    return subprocess.run(['bash',str(Path(__file__).with_name('openroad_combined_screen_wrapper.sh')),str(script)],env=env,text=True,capture_output=True)


def test_one_full_route_after_edits_and_wire_cleanup_then_inline_antennas(tmp_path):
    source='source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl'
    r=wrapper(tmp_path,'grt.tcl','read_current_odb\n'+source+'\nwrite_views\n')
    assert r.returncode==0 and r.stdout.count(source)==1
    operations=['baseline.nl.v','combined_physical_targets.tcl','common/dpl.tcl','after_edits.nl.v','tripwire_clear_native_signal_routes',source,'log_cmd repair_antennas','tripwire_restore_placement_status','write_views']
    assert [r.stdout.index(s) for s in operations]==sorted(r.stdout.index(s) for s in operations)
    assert 'OpenROAD.DetailedRouting' not in r.stdout


@pytest.mark.parametrize('name,text',[('antenna_repair.tcl','read_current_odb\n'),('grt.tcl','read_current_odb\nwrite_views\n')])
def test_separate_antenna_process_or_changed_pinned_script_refused(tmp_path,name,text):
    assert wrapper(tmp_path,name,text).returncode!=0


def test_only_reviewed_old_placement_changes_allowed():
    old='COMPONENTS 1 ;\n- original sg13cmos5l_buf_1 + PLACED ( 0 0 ) N ;\nEND COMPONENTS'
    proposal={'resizes':[dict(instance='original',new_master='sg13cmos5l_buf_2',location=[10,0,'N'])],'groups':[{'buffer':'new'}]}
    new='COMPONENTS 2 ;\n- original sg13cmos5l_buf_2 + PLACED ( 10 0 ) N ;\n- new sg13cmos5l_buf_4 + PLACED ( 20 0 ) N ;\nEND COMPONENTS'
    validate_placements(old,new,proposal)
    with pytest.raises(ValueError):validate_placements(old,new.replace('( 10 0 )','( 11 0 )'),proposal)
    with pytest.raises(ValueError):validate_placements(old,old,proposal)


def test_workflow_downloads_actual_failed_extracted_source_and_only_screens():
    import yaml
    p=Path(__file__).resolve().parents[2]/'.github/workflows/gds-combined-physical-screen.yaml';w=yaml.safe_load(p.read_text())
    steps=w['jobs']['harden']['steps'];d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38305592967
    assert any(s.get('run')=='python workflow-src/scripts/ci/combined_physical_screen.py' for s in steps)
    script=Path(__file__).with_name('combined_physical_screen.py').read_text()
    assert 'OpenROAD.DetailedRouting' not in script and 'electrical_clean(timing)' in script
