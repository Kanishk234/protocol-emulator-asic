"""Execute the read-only probe with strict OpenDB mocks, including bracketed nets."""
import os
from pathlib import Path
import subprocess

import pytest


@pytest.mark.parametrize('fault', ['none', 'escaped', 'missing_clock', 'ambiguous_driver', 'ambiguous_spelling'])
def test_read_only_c_select_probe(tmp_path, fault):
    helper = Path(__file__).with_name('native_c_select_geometry_audit.tcl').resolve()
    script = r'''
rename source native_source
proc source {file} {
    if {[file tail $file] eq "native_hold_frontier_audit.tcl"} {return}
    native_source $file
}
namespace eval ord {proc get_db_block {} {return block}}
set names [list _02001_ {u_chip.g_lane[1].ot[26]} \
    {clknet_2_0__leaf_u_chip.g_unit[0].u_cfg.g_word[0].g_stored.gclk} net14386 \
    {u_chip.g_unit[0].bitsync_active} {u_chip.u_fab.u_c0.pending_drop}]
proc block {method name} {
    if {$method ne "findNet"} {error "Unexpected block mutation/API: $method"}
    set stored $::names
    if {$::fault in {escaped missing_clock}} {
        set stored {}
        foreach n $::names {lappend stored [string map [list {[} {\[} {]} {\]}] $n]}
    }
    set index [lsearch -exact $stored $name]
    if {$::fault eq "ambiguous_spelling" && $name eq {u_chip.g_lane\[1\].ot\[26\]}} {return alternate_net}
    if {$::fault eq "missing_clock" && $index == 2} {return NULL}
    if {$index < 0} {return NULL}
    return net$index
}
proc net {index method args} {
    switch $method {
        getName {
            set name [lindex $::names $index]
            if {$::fault eq "escaped"} {return [string map [list {[} {\[} {]} {\]}] $name]}
            return $name
        }
        getSigType {return [expr {$index == 2 ? "CLOCK" : "SIGNAL"}]}
        getITerms {
            if {$::fault eq "ambiguous_driver" && $index == 4} {return {term4 term5}}
            return term$index
        }
        default {error "Unexpected net mutation/API: $method"}
    }
}
proc term {index method args} {
    switch $method {
        getInst {return inst$index}
        getMTerm {return mterm$index}
        default {error "Unexpected terminal mutation/API: $method"}
    }
}
proc inst {index method args} {
    switch $method {
        getName {return [lindex {_50780_ hold11285 _51789_ wire14386 _52357_ _51130_} $index]}
        getMaster {return master}
        getLocation {return {100 200}}
        getOrient {return R0}
        findITerm {if {[lindex $args 0] eq "D"} {return data}; return NULL}
        default {error "Unexpected instance mutation/API: $method"}
    }
}
proc mterm {index method args} {
    switch $method {
        getIoType {return [expr {$index >= 4 ? "OUTPUT" : "INPUT"}]}
        getName {return [lindex {D A GATE A Q Q} $index]}
        default {error "Unexpected master-term mutation/API: $method"}
    }
}
proc master {method} {if {$method eq "getName"} {return reviewed_master}; error unexpected}
for {set i 0} {$i < 6} {incr i} {
    foreach type {net term inst mterm} {interp alias {} $type$i {} $type $i}
}
proc write_global_route_segments {file} {puts "EXPORT_SEGMENTS"}
proc get_pins {name} {return $name}
proc report_checks {args} {puts "CHECK $args"}
proc check_antennas {args} {puts "ANTENNA $args"}
'''
    script += f'\nset fault {fault}\nset ::env(STEP_DIR) {{{tmp_path}}}\n'
    script += f'native_source {{{helper}}}\n'
    path = tmp_path / 'probe.tcl'
    path.write_text(script)
    result = subprocess.run([os.environ.get('TRIPWIRE_TCLSH', 'tclsh'), str(path)],
                            text=True, capture_output=True)
    if fault in ('none', 'escaped'):
        assert result.returncode == 0, result.stderr
        assert result.stdout.count('ANTENNA -net') == 4
        assert 'TRACKED_FROM _52357_/Q TRACKED_TO _51130_/D' in result.stdout
        assert '-from _52357_/Q -to _51130_/D' in result.stdout
        assert 'TYPE CLOCK' in result.stdout
    else:
        assert result.returncode != 0
        expected = {'missing_clock': 'Missing reviewed antenna net',
                    'ambiguous_driver': 'Expected one driver',
                    'ambiguous_spelling': 'Ambiguous reviewed net spelling'}
        assert expected[fault] in result.stderr
