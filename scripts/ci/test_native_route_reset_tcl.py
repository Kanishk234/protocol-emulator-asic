import os
import subprocess
from pathlib import Path
import pytest


@pytest.mark.parametrize('failure', ['none', 'api', 'empty', 'retained'])
def test_route_reset_preserves_power_and_net_objects(tmp_path, failure):
    script = r'''
namespace eval ord {proc get_db_block {} {return block}}
namespace eval odb {}
set removed {}
set wires [dict create signal ws clock wc power wp ground wg unrouted NULL]
proc block {method} {return {signal clock power ground unrouted}}
proc net {name method} {
    if {$method eq "getSigType"} {
        if {$name eq "power"} {return POWER}
        if {$name eq "ground"} {return GROUND}
        if {$name eq "clock"} {return CLOCK}
        return SIGNAL
    }
    if {$method eq "getWire"} {return [dict get $::wires $name]}
    error "Unexpected operation"
}
foreach name {signal clock power ground unrouted} {interp alias {} $name {} net $name}
proc odb::dbWire_destroy {wire} {
    lappend ::removed $wire
    if {$::failure ne "retained"} {
        dict for {name current} $::wires {
            if {$current eq $wire} {dict set ::wires $name NULL}
        }
    }
}
'''
    helper = Path(__file__).with_name('native_hold100_size.tcl').resolve()
    script += f'set failure {failure}\nsource {{{helper}}}\n'
    if failure == 'api': script += 'rename odb::dbWire_destroy {}\n'
    if failure == 'empty': script += 'dict set wires signal NULL\ndict set wires clock NULL\n'
    script += 'set rc [catch {tripwire_clear_native_signal_routes} message]\n'
    script += 'puts "RESULT $rc $removed $message"\nputs "POWER [dict get $wires power] GROUND [dict get $wires ground]"\n'
    path = tmp_path / 'reset.tcl'; path.write_text(script)
    result = subprocess.run([os.environ.get('TRIPWIRE_TCLSH', 'tclsh'), str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'POWER wp GROUND wg' in result.stdout
    if failure == 'none':
        assert 'RESULT 0 ws wc' in result.stdout
        assert 'cleared 2 ordinary routed wires' in result.stdout
    else:
        assert 'RESULT 1' in result.stdout
    if failure in ['api', 'empty']: assert 'RESULT 1  ' in result.stdout
