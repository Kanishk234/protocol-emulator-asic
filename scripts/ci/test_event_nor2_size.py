"""Physical ECO preconditions must fail before the cell is replaced."""
import os
from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.mark.parametrize('failure', ['none', 'missing', 'master', 'pins',
                                    'replacement', 'net', 'power', 'post_net'])
def test_exact_cell_guard(tmp_path, failure):
    interpreter = os.environ.get('TRIPWIRE_TCLSH', 'tclsh')
    if shutil.which(interpreter) is None:
        pytest.skip('Tcl interpreter unavailable')
    helper = Path(__file__).with_name('event_nor2_size.tcl').resolve()
    script = tmp_path / 'check.tcl'
    script.write_text(r'''
namespace eval ord {
 proc get_db_block {} {return block}
 proc get_db {} {return db}
}
set replaced 0
proc replace_cell {inst master} {set ::replaced 1; puts REPLACE}
proc dispatch {obj method args} {
 switch $method {
  findInst {return [expr {$::failure eq "missing" ? "NULL" : "inst"}]}
  findMaster {return replacement}
  getMaster {return original}
  getName {
   if {$obj eq "original"} {
    if {$::replaced} {return sg13cmos5l_nor2_2}
    return [expr {$::failure eq "master" ? "wrong" : "sg13cmos5l_nor2_1"}]
   }
   return $obj
  }
  getITerms {return [expr {$::failure eq "pins" ? "A B Y" : "A B Y VDD VSS"}]}
  getMTerms {return [expr {$::failure eq "replacement" ? "A B X VDD VSS" : "A B Y VDD VSS"}]}
  getMTerm {return $obj}
  findITerm {return [lindex $args 0]}
  getNet {
   if {$obj eq "A" && ($::failure eq "net" || ($::failure eq "post_net" && $::replaced))} {return wrong}
   if {$obj eq "VDD" && $::failure eq "power"} {return NULL}
   return [dict get {A _21095_ B _02509_ Y _02510_ VDD power VSS ground} $obj]
  }
  default {error "Unexpected call: $obj $method"}
 }
}
foreach name {block db inst original replacement A B Y X VDD VSS _21095_ _02509_ _02510_ power ground wrong} {
 interp alias {} $name {} dispatch $name
}
''' + f'set failure {failure}\nsource {{{helper}}}\ntripwire_size_event_nor2\n')
    result = subprocess.run([interpreter, str(script)], capture_output=True, text=True)
    if failure == 'none':
        assert result.returncode == 0, result.stderr
        assert result.stdout.count('REPLACE') == 1
    else:
        assert result.returncode != 0
        assert ('REPLACE' in result.stdout) == (failure == 'post_net')
