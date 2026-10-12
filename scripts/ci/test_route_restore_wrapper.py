import os
from pathlib import Path
import subprocess
import pytest


def run(tmp_path,name,text):
    binary=tmp_path/'openroad';binary.write_text('#!/bin/bash\ncat "${@: -1}"\n');binary.chmod(0o755)
    script=tmp_path/name;script.write_text(text)
    env=dict(os.environ,PATH=str(tmp_path)+os.pathsep+os.environ['PATH'],RUNNER_TEMP=str(tmp_path))
    return subprocess.run(['bash',str(Path(__file__).with_name('openroad_route_restore_wrapper.sh')),str(script)],env=env,text=True,capture_output=True)


def test_replaces_full_route_with_restore_and_no_edit_incremental(tmp_path):
    source='read_current_odb\nsource $::env(SCRIPTS_DIR)/openroad/common/grt.tcl\nwrite_views\n'
    r=run(tmp_path,'grt.tcl',source)
    assert r.returncode==0
    assert 'source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl' not in r.stdout
    assert r.stdout.index('read_global_route_segments')<r.stdout.index('global_route -start_incremental')<r.stdout.index('global_route -end_incremental')<r.stdout.index('write_views')
    assert 'electrical_repair_targets' not in r.stdout


@pytest.mark.parametrize('source',['read_current_odb\n','read_current_odb\nread_current_odb\nsource $::env(SCRIPTS_DIR)/openroad/common/grt.tcl\n'])
def test_changed_pinned_script_refused(tmp_path,source):
    r=run(tmp_path,'grt.tcl',source)
    assert r.returncode!=0 and 'Ambiguous pinned routing script' in r.stderr


def test_sta_script_passes_through_without_route_operations(tmp_path):
    r=run(tmp_path,'corner.tcl','read_current_odb\nreport_checks\n')
    assert r.returncode==0 and r.stdout=='read_current_odb\nreport_checks\n'
