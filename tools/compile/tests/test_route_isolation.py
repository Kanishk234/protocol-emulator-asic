"""Connection isolation must be explicit and preserve routing rejection."""
from pathlib import Path
import sys
import shutil
import subprocess
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'test_internal'))
import cloud_route_isolation as isolate
import cloud_route_trace as trace
from cloud_route_121_grid import observed_trace, PATCH


def test_control_is_exact_grid_observer_without_net_selection():
    assert isolate.isolation_trace(trace.TRACE, None) == observed_trace(trace.TRACE, PATCH.read_text())


@pytest.mark.parametrize('names', [isolate.CASES['pad31'], isolate.CASES['val30'], isolate.CASES['south_pair']])
def test_selection_is_fixed_literal_before_original_route_and_rethrow(names):
    text = isolate.isolation_trace(trace.TRACE, names)
    assert text.startswith('set warp_selected_nets {' + ' '.join(names) + '}\n')
    assert text.count('log_cmd grt::add_net_to_route [lindex $warp_matches 0]') == 1
    assert 'string map [list [format %c 92] {}]' in text
    assert text.index('grt::add_net_to_route') < text.index('log_cmd global_route')
    assert 'return -options $warp_route_options $warp_route_error' in text
    assert '-allow_congestion' not in text


def test_arbitrary_reduced_sets_rejected():
    with pytest.raises(ValueError):
        isolate.isolation_trace(trace.TRACE, ['clk'])


@pytest.mark.parametrize('duplicate', [False, True])
def test_actual_tcl_resolves_escaped_database_names_and_rejects_ambiguity(duplicate):
    tcl = shutil.which('tclsh')
    if not tcl:
        pytest.skip('Tcl interpreter unavailable')
    prefix = r'''
namespace eval ord {proc get_db_block {} {return block}}
namespace eval grt {proc add_net_to_route {net} {lappend ::selected $net}}
proc log_cmd {args} {uplevel 1 $args}
proc net31 {method} {return {cell_pad\[31\]}}
proc net30 {method} {return {cell_val\[30\]}}
set selected {}
'''
    prefix += 'proc block {method} {return {' + ('net31 net31 net30' if duplicate else 'net31 net30') + '}}\n'
    code = isolate.isolation_trace(trace.TRACE, isolate.CASES['south_pair']).split('set warp_route_code', 1)[0]
    script = prefix + '\nset code [catch {\n' + code + '\n} message]\n'
    script += ('if {$code != 1 || $message ne "Missing or ambiguous selected net"} {exit 1}\n' if duplicate
               else 'if {$code != 0 || $selected ne "net31 net30"} {puts stderr $message; exit 1}\n')
    subprocess.run([tcl], input=script, text=True, capture_output=True, check=True)
