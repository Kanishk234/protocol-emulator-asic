"""Runtime net identity checks; no OpenDB behavior or physical timing claim."""
from pathlib import Path
import shutil
import subprocess
import pytest


def test_escaped_net_names_resolve_unique_objects_and_refuse_aliases(tmp_path):
    tcl=shutil.which('tclsh')
    if not tcl: pytest.skip('Tcl runtime unavailable')
    helper=Path(__file__).with_name('electrical_repair.tcl').resolve()
    script=tmp_path/'names.tcl'
    script.write_text('source {'+str(helper)+'}\n'+r'''
proc block {method args} {return {net1 net2}}
proc net1 {method args} {return {u_chip.port_state[45\]}}
proc net2 {method args} {return other}
if {[tripwire_electrical_find_net block {u_chip.port_state[45]}] ne "net1"} {error mismatch}
if {[tripwire_electrical_find_net block {u_chip.port_state\[45\]}] ne "net1"} {error mismatch}
if {![catch {tripwire_electrical_find_net block missing}]} {error "missing accepted"}
rename net2 old_net2
proc net2 {method args} {return {u_chip.port_state[45]}}
if {![catch {tripwire_electrical_find_net block {u_chip.port_state[45]}}]} {error "alias accepted"}
puts complete
''')
    r=subprocess.run([tcl,str(script)],capture_output=True,text=True,check=True)
    assert 'complete' in r.stdout.splitlines()


def test_escaped_instance_names_resolve_uniquely(tmp_path):
    tcl=shutil.which('tclsh')
    if not tcl:pytest.skip('Tcl runtime unavailable')
    helper=Path(__file__).with_name('electrical_repair.tcl').resolve()
    script=tmp_path/'instances.tcl'
    script.write_text('source {'+str(helper)+'}\n'+r'''
proc block {method args} {
    if {$method eq "findInst"} {return NULL}
    if {$method eq "getInsts"} {return {one two}}
    error unexpected
}
proc one {method} {return {clk\[0\]}}
proc two {method} {return other}
if {[tripwire_electrical_find_inst block {clk[0]}] ne "one"} {error mismatch}
if {![catch {tripwire_electrical_find_inst block missing}]} {error missing}
rename two old_two
proc two {method} {return {clk[0]}}
if {![catch {tripwire_electrical_find_inst block {clk[0]}}]} {error ambiguity}
puts complete
''')
    r=subprocess.run([tcl,str(script)],capture_output=True,text=True,check=True)
    assert 'complete' in r.stdout.splitlines()
