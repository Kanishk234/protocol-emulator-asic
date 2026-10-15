"""Failed-route observer retains native error and rejects malformed exports."""
from pathlib import Path
import shutil
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'test_internal'))
import cloud_route_trace as trace


def sample():
    return ''.join(name+'\n(\n10 20 Metal1 10 20 Metal2\n10 20 Metal2 10 40 Metal2\n)\n'
                   for name in sorted(trace.TARGETS))


def test_native_segments_require_all_measured_nets():
    result = trace.parse_segments(sample())
    assert result['native_net_count'] == 4
    assert set(result['targets']) == trace.TARGETS
    with pytest.raises(ValueError, match='absent'):
        trace.parse_segments('n\n(\n0 0 Metal1 10 0 Metal1\n)\n')


@pytest.mark.parametrize('old,new', [('10 40 Metal2','20 40 Metal2'),
    ('10 40 Metal2','10 40 Metal3'), ('Metal1','Metal5'), (')\n','')])
def test_native_segments_reject_unsafe_or_partial_geometry(old,new):
    with pytest.raises(ValueError):trace.parse_segments(sample().replace(old,new))


def test_observer_rethrows_original_native_failure(tmp_path):
    tcl = shutil.which('tclsh')
    if not tcl:pytest.skip('Tcl interpreter unavailable')
    prefix = r'''
set ::env(STEP_DIR) [lindex $argv 0]
proc log_cmd {args} {return -code error -errorcode {GRT 116} "GRT-0116"}
proc write_global_route_segments {path} {set f [open $path w]; puts $f "native witness"; close $f}
set arg_list {-congestion_iterations 50}
proc observer {} {
    global arg_list
'''
    suffix = r'''
}
set status [catch observer message options]
if {$status != 1 || $message ne "GRT-0116" || [dict get $options -errorcode] ne {GRT 116}} {exit 4}
if {![file exists $::env(STEP_DIR)/native-segments.txt]} {exit 5}
'''
    script=tmp_path/'test.tcl';script.write_text(prefix+trace.TRACE+suffix)
    subprocess.run([tcl,str(script),str(tmp_path)],check=True,timeout=5)
    assert (tmp_path/'native-return.txt').read_text() == '1\nGRT-0116\n'


def test_observer_does_not_mask_unrelated_error(tmp_path):
    tcl = shutil.which('tclsh')
    if not tcl:pytest.skip('Tcl interpreter unavailable')
    prefix = r'''
set ::env(STEP_DIR) [lindex $argv 0]
proc log_cmd {args} {error "unrelated"}
proc write_global_route_segments {path} {error "must not export unrelated failure"}
set arg_list {}
proc observer {} {
    global arg_list
'''
    suffix = r'''
}
set status [catch observer message]
if {$status != 1 || $message ne "unrelated"} {exit 4}
'''
    script=tmp_path/'test.tcl';script.write_text(prefix+trace.TRACE+suffix)
    subprocess.run([tcl,str(script),str(tmp_path)],check=True,timeout=5)
    assert not (tmp_path/'native-segments.txt').exists()
