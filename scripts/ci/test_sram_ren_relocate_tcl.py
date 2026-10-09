"""Actual Tcl execution; OpenDB calls mocked, no physical qualification claimed."""
import os
from pathlib import Path
import subprocess
import pytest


@pytest.mark.parametrize('failure', ['none', 'missing', 'master', 'fixed', 'position',
                                    'orientation', 'pins', 'net', 'power', 'occupied',
                                    'post_net', 'post_position'])
def test_ren_relocation_guards(tmp_path, failure):
    helper = Path(__file__).with_name('sram_ren_relocate.tcl').resolve()
    script = r'''
namespace eval ord {proc get_db_block {} {return block}}
set mutations 0
set x 438720
set y 226800
set orient MX
proc dispatch {object method args} {
    switch $method {
        findInst {if {$::failure eq "missing"} {return NULL}; return buffer}
        getMaster {return master}
        isFixed {return [expr {$::failure eq "fixed"}]}
        getName {
            if {$object eq "master"} {if {$::failure eq "master"} {return wrong}; return sg13cmos5l_nor2b_1}
            if {$object eq "netA"} {if {$::failure eq "net"} {return wrong}; return _04439_}
            if {$object eq "netB_N"} {return _04440_}
            if {$object eq "netY"} {return _00076_}
            return $object
        }
        getBBox {if {$object eq "other"} {return otherbox}; return box}
        xMin {if {$object eq "otherbox"} {return 122400}; if {$::failure eq "position"} {return 1}; return $::x}
        xMax {if {$object eq "otherbox"} {return 126240}; return [expr {$::x+2400}]}
        yMin {if {$object eq "otherbox"} {return 245700}; return $::y}
        yMax {if {$object eq "otherbox"} {return 249480}; return [expr {$::y+3780}]}
        getOrient {if {$::failure eq "orientation"} {return R180}; return $::orient}
        getITerms {if {$::failure eq "pins"} {return {A B_N Y VDD}}; return {A B_N Y VDD VSS}}
        getMTerm {return $object}
        getNet {
            if {$object eq "VDD" && $::failure eq "power"} {return NULL}
            if {$object eq "A" && $::failure eq "post_net" && $::mutations} {return netY}
            return net$object
        }
        findITerm {return [lindex $args 0]}
        getInsts {if {$::failure eq "occupied"} {return {buffer other}}; return buffer}
        setOrient {incr ::mutations; set ::orient [lindex $args 0]}
        setLocation {
            if {$::orient ne "R0"} {error "Location set before orientation"}
            incr ::mutations
            lassign $args ::x ::y
            if {$::failure eq "post_position"} {set ::x 0}
        }
        default {error "Unexpected mock operation $method"}
    }
}
foreach name {block buffer master box other otherbox A B_N Y VDD VSS netA netB_N netY netVDD netVSS} {
    interp alias {} $name {} dispatch $name
}
'''
    script += f'set failure {failure}\nsource {{{helper}}}\n'
    script += 'set rc [catch {tripwire_relocate_sram_ren; tripwire_verify_sram_ren} message]\nputs "RESULT $rc $mutations $message"\n'
    path = tmp_path / 'relocate.tcl'
    path.write_text(script)
    result = subprocess.run([os.environ.get('TRIPWIRE_TCLSH', 'tclsh'), str(path)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    if failure == 'none':
        assert 'RESULT 0 2' in result.stdout
    elif failure.startswith('post_'):
        assert 'RESULT 1 2' in result.stdout
    else:
        assert 'RESULT 1 0' in result.stdout

