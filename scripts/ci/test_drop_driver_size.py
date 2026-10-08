"""Physical ECO preconditions must fail before the cell is replaced."""
import os
from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.mark.parametrize('target', ['driver'])
@pytest.mark.parametrize('failure', ['none', 'missing', 'master', 'pins',
                                    'replacement', 'missing_master', 'unknown', 'net', 'power', 'post_net'])
def test_exact_driver_cell_guard(tmp_path, failure, target):
    interpreter = os.environ.get('TRIPWIRE_TCLSH', 'tclsh')
    if shutil.which(interpreter) is None:
        pytest.skip('Tcl interpreter unavailable')
    helper = Path(__file__).with_name('drop_driver_size.tcl').resolve()
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
  findMaster {return [expr {$::failure eq "missing_master" ? "NULL" : "replacement"}]}
  getMaster {return original}
  getName {
   if {$obj eq "original"} {
    if {$::replaced} {return ${::new_master}}
    return [expr {$::failure eq "master" ? "wrong" : "${::old_master}"}]
   }
   return $obj
  }
  getITerms {return [expr {$::failure eq "pins" ? "A" : $::pins}]}
  getMTerms {return [expr {$::failure eq "replacement" ? "A B X VDD VSS" : $::pins}]}
  getMTerm {return $obj}
  findITerm {return [lindex $args 0]}
  getNet {
   if {$obj eq "A1" && ($::failure eq "net" || ($::failure eq "post_net" && $::replaced))} {return wrong}
   if {$obj eq "VDD" && $::failure eq "power"} {return NULL}
   return [dict get $::nets $obj]
  }
  default {error "Unexpected call: $obj $method"}
 }
}
foreach name {block db inst original replacement A B Y X VDD VSS _21095_ _02509_ _02510_ power ground wrong _05964_ _05968_ _05970_ _12192_ _12193_ A1 A2 B1 _12085_ _12163_ _12191_} {
 interp alias {} $name {} dispatch $name
}
''' + 'set old_master sg13cmos5l_a21oi_1\nset new_master sg13cmos5l_a21oi_2\nset pins {A1 A2 B1 Y VDD VSS}\nset nets {A1 _12085_ A2 _12163_ B1 _12191_ Y _12192_ VDD power VSS ground}\n' + f'set failure {failure}\nsource {{{helper}}}\ntripwire_size_drop_driver {"unreviewed" if failure == "unknown" else target}\n')
    result = subprocess.run([interpreter, str(script)], capture_output=True, text=True)
    if failure == 'none':
        assert result.returncode == 0, result.stderr
        assert result.stdout.count('REPLACE') == 1
    else:
        assert result.returncode != 0
        assert ('REPLACE' in result.stdout) == (failure == 'post_net')
