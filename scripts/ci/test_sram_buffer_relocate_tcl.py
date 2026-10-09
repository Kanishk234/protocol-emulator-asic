"""Actual Tcl execution; OpenDB calls mocked, no physical qualification claimed."""
import os
from pathlib import Path
import subprocess
import pytest


@pytest.mark.parametrize('failure', ['none', 'missing', 'master', 'fixed', 'position',
                                    'orientation', 'pins', 'net', 'power', 'occupied',
                                    'post_net', 'post_position'])
def test_relocation_guards(tmp_path, failure):
    helper = Path(__file__).with_name('sram_buffer_relocate.tcl').resolve()
    script = r'''
namespace eval ord {proc get_db_block {} {return block}}
set mutations 0
set x 473760
set y 230580
set orient R0
proc dispatch {object method args} {
    switch $method {
        findInst {if {$::failure eq "missing"} {return NULL}; return buffer}
        getMaster {return master}
        isFixed {return [expr {$::failure eq "fixed"}]}
        getName {
            if {$object eq "master"} {if {$::failure eq "master"} {return wrong}; return sg13cmos5l_buf_4}
            if {$object eq "netA"} {if {$::failure eq "net"} {return wrong}; return {u_chip.g_lane\[0\].u_lane.mem_rdata\[0\]}}
            if {$object eq "netX"} {return net9447}
            return $object
        }
        getBBox {if {$object eq "other"} {return otherbox}; return box}
        xMin {if {$object eq "otherbox"} {return 20640}; if {$::failure eq "position"} {return 1}; return $::x}
        xMax {if {$object eq "otherbox"} {return 24480}; return [expr {$::x+3840}]}
        yMin {if {$object eq "otherbox"} {return 249480}; return $::y}
        yMax {if {$object eq "otherbox"} {return 253260}; return [expr {$::y+3780}]}
        getOrient {if {$::failure eq "orientation"} {return R180}; return $::orient}
        getITerms {if {$::failure eq "pins"} {return {A X VDD}}; return {A X VDD VSS}}
        getMTerm {return $object}
        getNet {
            if {$object eq "VDD" && $::failure eq "power"} {return NULL}
            if {$object eq "A" && $::failure eq "post_net" && $::mutations} {return netX}
            return net$object
        }
        findITerm {return [lindex $args 0]}
        getInsts {if {$::failure eq "occupied"} {return {buffer other}}; return buffer}
        setOrient {incr ::mutations; set ::orient [lindex $args 0]}
        setLocation {
            if {$::orient ne "MX"} {error "Location set before orientation"}
            incr ::mutations
            lassign $args ::x ::y
            if {$::failure eq "post_position"} {set ::x 0}
        }
        default {error "Unexpected mock operation $method"}
    }
}
foreach name {block buffer master box other otherbox A X VDD VSS netA netX netVDD netVSS} {
    interp alias {} $name {} dispatch $name
}
'''
    script += f'set failure {failure}\nsource {{{helper}}}\n'
    script += 'set rc [catch {tripwire_relocate_sram_output0; tripwire_verify_sram_output0} message]\nputs "RESULT $rc $mutations $message"\n'
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


@pytest.mark.parametrize('name', ['grt.tcl', 'antenna_repair.tcl', 'drt.tcl'])
@pytest.mark.parametrize('target', ['dout0', 'ren'])
def test_wrapper_only_relocates_at_first_grt_read(tmp_path, name, target):
    fake = tmp_path / 'openroad'
    fake.write_text('#!/bin/bash\ncat "${@: -1}"\n')
    fake.chmod(0o755)
    source = tmp_path / name
    source.write_text('read_current_odb\nputs done\n')
    wrapper = Path(__file__).with_name('openroad_sram_relocate_wrapper.sh' if target == 'dout0'
                                     else 'openroad_sram_ren_relocate_wrapper.sh')
    env = dict(os.environ, PATH=str(tmp_path) + ':' + os.environ['PATH'], RUNNER_TEMP=str(tmp_path))
    result = subprocess.run(['bash', str(wrapper), '-exit', str(source)],
                            capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr
    if name == 'grt.tcl':
        suffix = 'output0' if target == 'dout0' else 'ren'
        operations = ['read_current_odb', 'tripwire_relocate_sram_' + suffix,
                      'common/dpl.tcl', 'tripwire_verify_sram_' + suffix,
                      'tripwire_clear_native_signal_routes']
        assert [result.stdout.index(op) for op in operations] == sorted(result.stdout.index(op) for op in operations)
        assert result.stdout.count('tripwire_relocate_sram_' + suffix) == 1
        assert ('tripwire_relocate_sram_ren' if target == 'dout0' else 'tripwire_relocate_sram_output0') not in result.stdout
    else:
        assert 'tripwire_relocate_sram_output0' not in result.stdout
        assert 'tripwire_relocate_sram_ren' not in result.stdout
        assert 'tripwire_clear_native_signal_routes' not in result.stdout
    assert 'native_hold100_targets' not in result.stdout
    if name == 'antenna_repair.tcl':
        assert 'GRT_ALLOW_CONGESTION' in result.stdout


@pytest.mark.parametrize('reads', [0, 2])
@pytest.mark.parametrize('target', ['dout0', 'ren'])
def test_wrapper_rejects_ambiguous_checkpoint_read(tmp_path, reads, target):
    source = tmp_path / 'grt.tcl'
    source.write_text('read_current_odb\n' * reads)
    fake = tmp_path / 'openroad'
    fake.write_text('#!/bin/bash\nexit 99\n'); fake.chmod(0o755)
    env = dict(os.environ, PATH=str(tmp_path) + ':' + os.environ['PATH'])
    wrapper = 'openroad_sram_relocate_wrapper.sh' if target == 'dout0' else 'openroad_sram_ren_relocate_wrapper.sh'
    result = subprocess.run(['bash', str(Path(__file__).with_name(wrapper)), str(source)],
                            capture_output=True, text=True, env=env)
    assert result.returncode == 1
    assert 'Expected one native checkpoint read' in result.stderr
