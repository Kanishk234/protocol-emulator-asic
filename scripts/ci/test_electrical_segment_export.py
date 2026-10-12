from pathlib import Path
import os
import subprocess
import pytest


@pytest.mark.parametrize('script',['grt.tcl','antenna_repair.tcl'])
def test_segment_export_follows_complete_physical_step(tmp_path,script):
    binary=tmp_path/'openroad'
    binary.write_text('#!/bin/bash\ncat "${@: -1}"\n');binary.chmod(0o755)
    path=tmp_path/script;path.write_text('read_current_odb\nputs physical_step\nwrite_views\n')
    wrapper=Path(__file__).with_name('openroad_electrical_repair_wrapper.sh')
    env=dict(os.environ,PATH=str(tmp_path)+os.pathsep+os.environ['PATH'],RUNNER_TEMP=str(tmp_path))
    r=subprocess.run(['bash',str(wrapper),'-exit',str(path)],env=env,text=True,capture_output=True,check=True)
    assert r.stdout.count('write_global_route_segments')==1
    assert r.stdout.index('write_views')<r.stdout.index('write_global_route_segments')
    if script=='grt.tcl': assert 'electrical_repair_targets.tcl' in r.stdout
    else: assert 'electrical_repair_targets.tcl' not in r.stdout


def test_ambiguous_checkpoint_read_refused_before_export(tmp_path):
    binary=tmp_path/'openroad';binary.write_text('#!/bin/bash\nexit 0\n');binary.chmod(0o755)
    path=tmp_path/'grt.tcl';path.write_text('read_current_odb\nread_current_odb\n')
    env=dict(os.environ,PATH=str(tmp_path)+os.pathsep+os.environ['PATH'])
    r=subprocess.run(['bash',str(Path(__file__).with_name('openroad_electrical_repair_wrapper.sh')),str(path)],env=env,text=True,capture_output=True)
    assert r.returncode!=0 and 'Expected one native checkpoint read' in r.stderr
