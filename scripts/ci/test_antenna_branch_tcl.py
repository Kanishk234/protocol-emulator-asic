"""Execute prototype Tcl against mocked OpenDB; no physical pass claimed."""
import os
from pathlib import Path
import subprocess
import pytest


@pytest.mark.parametrize('fault', ['none', 'missing', 'connectivity', 'driver', 'diode', 'master', 'repeat', 'power'])
def test_guarded_identity_branch_split(tmp_path, fault):
    helper = Path(__file__).with_name('antenna_branch.tcl').resolve()
    script = r'''
namespace eval ord {proc get_db_block {} {return block}; proc get_db {} {return db}}
namespace eval odb {
    proc dbInst_create {args} {puts CREATE_BUFFER; return buffer}
    proc dbNet_create {args} {puts CREATE_NET; return downstream}
}
set terms {_28807_/Y ANTENNA_1/A ANTENNA_2/A ANTENNA_3/A ANTENNA_4/A ANTENNA_5/A ANTENNA_6/A ANTENNA_7/A _28812_/S1 _28936_/B _28973_/B _29032_/B _29046_/B _29087_/B _44662_/A1 place7617/A}
proc dispatch {obj method args} {
    switch $method {
        findNet {
            if {[lindex $args 0] eq "_03831_"} {if {$::fault eq "missing"} {return NULL}; return branch}
            return NULL
        }
        findInst {
            set name [lindex $args 0]
            if {$name eq "tripwire_antenna_branch_buf"} {return [expr {$::fault eq "repeat" ? "buffer" : "NULL"}]}
            return $name
        }
        findMaster {if {$::fault eq "master"} {return NULL}; return bufmaster}
        getMaster {return master$obj}
        getName {
            if {$obj eq "master_28807_"} {return [expr {$::fault eq "driver" ? "wrong" : "sg13cmos5l_nand3_1"}]}
            if {[string match masterANTENNA* $obj]} {return [expr {$::fault eq "diode" ? "wrong" : "sg13cmos5l_antennanp"}]}
            return $obj
        }
        getITerms {if {$::fault eq "connectivity"} {return [lrange $::terms 1 end]}; return $::terms}
        getBTerms {return {}}
        getInst {return [lindex [split $obj /] 0]}
        getMTerm {return [lindex [split $obj /] 1]}
        findITerm {return $obj/[lindex $args 0]}
        getNet {return [expr {$::fault eq "power" ? "NULL" : "rail"}]}
        connect - disconnect - setOrient - setLocation - setPlacementStatus {puts "$obj $method $args"}
        default {error "Unexpected $obj $method"}
    }
}
set objects {block db branch buffer downstream rail bufmaster _28807_ master_28807_ _28807_/VDD _28807_/VSS buffer/A buffer/X buffer/VDD buffer/VSS}
foreach term $terms {
    lassign [split $term /] inst pin
    lappend objects $term $inst $pin master$inst
}
foreach obj [lsort -unique $objects] {interp alias {} $obj {} dispatch $obj}
'''
    script += f'\nset fault {fault}\nsource {{{helper}}}\ntripwire_split_antenna_branch\n'
    path = tmp_path / 'branch.tcl'
    path.write_text(script)
    result = subprocess.run([os.environ.get('TRIPWIRE_TCLSH', 'tclsh'), str(path)], capture_output=True, text=True)
    if fault != 'none':
        assert result.returncode != 0
        assert 'CREATE_' not in result.stdout
    else:
        assert result.returncode == 0, result.stderr
        assert result.stdout.count(' disconnect ') == 8
        assert 'ANTENNA_2/A connect downstream' in result.stdout
        assert 'ANTENNA_1/A disconnect' not in result.stdout
        assert '_28807_/Y disconnect' not in result.stdout
        assert 'buffer/VDD connect rail' in result.stdout
        assert 'buffer setLocation 1250400 291060' in result.stdout


@pytest.mark.parametrize('name', ['grt.tcl', 'antenna_repair.tcl', 'drt.tcl'])
def test_wrapper_inserts_once_and_preserves_cleanup_routing(tmp_path, name):
    fake = tmp_path / 'openroad'
    fake.write_text('#!/bin/bash\ncat "${@: -1}"\n')
    fake.chmod(0o755)
    path = tmp_path / name
    path.write_text('read_current_odb\nputs done\n')
    wrapper = Path(__file__).with_name('openroad_antenna_branch_wrapper.sh')
    result = subprocess.run(['bash', str(wrapper), str(path)], capture_output=True, text=True,
                            env=dict(os.environ, PATH=str(tmp_path)+':'+os.environ['PATH'], RUNNER_TEMP=str(tmp_path)))
    assert result.returncode == 0, result.stderr
    if name == 'grt.tcl':
        operations = ['baseline.nl.v', 'tripwire_split_antenna_branch', 'common/dpl.tcl',
                      'legalization completed', 'tripwire_clear_native_signal_routes', 'eco.nl.v']
        indexes = [result.stdout.index(op) for op in operations]
        assert indexes == sorted(indexes)
        assert result.stdout.count('tripwire_split_antenna_branch') == 1
    else:
        assert 'tripwire_split_antenna_branch' not in result.stdout
        assert 'tripwire_clear_native_signal_routes' not in result.stdout
    assert 'tripwire_relocate_sram' not in result.stdout
