import os
from pathlib import Path
import subprocess
import pytest


def run(tmp_path,name,text):
    binary=tmp_path/'openroad';binary.write_text('#!/bin/bash\ncat "${@: -1}"\n');binary.chmod(0o755)
    path=tmp_path/name;path.write_text(text)
    env=dict(os.environ,PATH=str(tmp_path)+os.pathsep+os.environ['PATH'],RUNNER_TEMP=str(tmp_path))
    return subprocess.run(['bash',str(Path(__file__).with_name('openroad_electrical_incremental_wrapper.sh')),str(path)],env=env,text=True,capture_output=True)


def test_one_full_initial_route_precedes_live_incremental_and_inline_antennas(tmp_path):
    s='read_current_odb\nsource $::env(SCRIPTS_DIR)/openroad/common/grt.tcl\nwrite_views\n'
    r=run(tmp_path,'grt.tcl',s);assert r.returncode==0
    full='source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl'
    assert r.stdout.count(full)==1 and 'read_global_route_segments' not in r.stdout
    assert r.stdout.index(full)<r.stdout.index('global_route -start_incremental')<r.stdout.index('electrical_incremental_targets.tcl')<r.stdout.index('repair_antennas')<r.stdout.index('tripwire_restore_placement_status')<r.stdout.index('write_views')
    assert r.stdout.count('global_route -start_incremental')==2


def test_separate_antenna_process_refused(tmp_path):
    r=run(tmp_path,'antenna_repair.tcl','read_current_odb\nwrite_views\n')
    assert r.returncode!=0 and 'keep antenna repair in the routing process' in r.stderr


def test_changed_pinned_script_refused(tmp_path):
    r=run(tmp_path,'grt.tcl','read_current_odb\nwrite_views\n')
    assert r.returncode!=0 and 'Ambiguous incremental script' in r.stderr


def test_freeze_restores_only_original_placement_statuses(tmp_path):
    import shutil
    tcl=shutil.which('tclsh')
    if not tcl:pytest.skip('Tcl runtime unavailable')
    helper=Path(__file__).with_name('incremental_placement.tcl').resolve()
    script=tmp_path/'freeze.tcl'
    script.write_text('source {'+str(helper)+'}\n'+r'''
namespace eval ord {proc get_db_block {} {return block}}
proc block {method args} {return {old macro}}
set old_status PLACED
set macro_status FIXED
set new_status PLACED
proc old {method args} {global old_status; if {$method eq "getPlacementStatus"} {return $old_status}; set old_status [lindex $args 0]}
proc macro {method args} {global macro_status; if {$method eq "getPlacementStatus"} {return $macro_status}; set macro_status [lindex $args 0]}
set saved [tripwire_freeze_existing_placement]
if {$old_status ne "FIXED" || $macro_status ne "FIXED"} {error freeze}
tripwire_restore_placement_status $saved
if {$old_status ne "PLACED" || $macro_status ne "FIXED" || $new_status ne "PLACED"} {error restore}
puts complete
''')
    r=subprocess.run([tcl,str(script)],capture_output=True,text=True,check=True)
    assert 'complete' in r.stdout.splitlines()
