import os
import subprocess
from pathlib import Path

import pytest

from residual_setup import TARGETS


@pytest.mark.parametrize('failure', ['none', 'master', 'missing', 'pins', 'net', 'power', 'post_net'])
def test_all_targets_preflight_before_any_replace(tmp_path, failure):
    script = r'''
namespace eval ord {proc get_db {} {return db}; proc get_db_block {} {return block}}
set count 0
set changed {}
proc replace_cell {name master} {incr ::count; dict set ::changed $name $master}
proc dispatch {object method args} {
    switch $method {
        findInst {
            set name [lindex $args 0]
            if {$::failure eq "missing" && $name eq "_27962_"} {return NULL}
            return $name
        }
        findMaster {return [lindex $args 0]}
        getMaster {return master_$object}
        getName {
            if {[string match master_* $object]} {
                set name [string range $object 7 end]
                if {[dict exists $::changed $name]} {return [dict get $::changed $name]}
                if {$::failure eq "master" && $name eq "_27962_"} {return wrong}
                return [dict get $::old $name]
            }
            if {[dict exists $::netnames $object]} {return [dict get $::netnames $object]}
            return $object
        }
        getITerms {set result {}; foreach pin [dict keys [dict get $::terms $object]] {lappend result $object/$pin}; return $result}
        getMTerms {
            if {$::failure eq "pins" && $object eq "sg13cmos5l_nor4_2"} {return {A}}
            return [dict get $::masterpins $object]
        }
        getMTerm {return [lindex [split $object /] 1]}
        findITerm {return $object/[lindex $args 0]}
        getNet {
            lassign [split $object /] name pin
            if {$name eq "_27962_"} {
                if {$::failure eq "net" && $pin eq "A"} {return wrong}
                if {$::failure eq "power" && $pin eq "VDD"} {return NULL}
                if {$::failure eq "post_net" && $::count && $pin eq "A"} {return wrong}
            }
            return [dict get $::terms $name $pin]
        }
        default {error "Unexpected mock operation"}
    }
}
'''
    aliases = {'block', 'db', 'wrong', 'A'}
    for name, old, new, pins in TARGETS:
        complete = dict(pins, VDD='power', VSS='ground')
        script += f'dict set old {name} {old}\n'
        script += f'dict set masterpins {new} {{{" ".join(complete)}}}\n'
        aliases.update([name, 'master_' + name, new, *complete])
        for pin, net in complete.items():
            ref = name + '/' + pin
            netref = 'net_' + name + '_' + pin
            script += f'dict set terms {name} {pin} {netref}\ndict set netnames {netref} {net}\n'
            aliases.update([ref, netref])
    for alias in sorted(aliases):
        script += f'interp alias {{}} {alias} {{}} dispatch {alias}\n'
    helper = Path(__file__).with_name('residual_setup.tcl').resolve()
    script += f'set failure {failure}\nsource {{{helper}}}\n'
    script += 'set rc [catch {tripwire_size_residual_setup} message]\nputs "RESULT $rc $count $message"\n'
    path = tmp_path / 'guard.tcl'; path.write_text(script)
    result = subprocess.run([os.environ.get('TRIPWIRE_TCLSH', 'tclsh'), str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    if failure == 'none':
        assert 'RESULT 0 3' in result.stdout
    elif failure == 'post_net':
        assert 'RESULT 1 3' in result.stdout
    else:
        assert 'RESULT 1 0' in result.stdout
