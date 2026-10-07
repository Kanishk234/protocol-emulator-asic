"""Connectivity guards for an unlaunched physical delay prototype."""
from pathlib import Path
import shutil
import os
import subprocess

import pytest


@pytest.mark.parametrize('failure', ['none', 'connectivity', 'master', 'duplicate', 'power'])
def test_only_audited_sram_sink_is_rewired(tmp_path, failure):
    interpreter = os.environ.get('TRIPWIRE_TCLSH', 'tclsh')
    if shutil.which(interpreter) is None:
        pytest.skip('Tcl interpreter unavailable')
    trial = Path(__file__).with_name('banked_sram_addr_hold.tcl').resolve()
    script = tmp_path / 'exercise.tcl'
    script.write_text(r'''
namespace eval ord {
 proc get_db_block {} {return block}
 proc get_db {} {return db}
}
namespace eval odb {
 proc dbInst_create {args} {puts CREATE;return buffer}
 proc dbNet_create {args} {puts CREATE;return downstream}
}
proc dispatch {obj method args} {
 switch $method {
  findNet {
   if {[lindex $args 0] eq "net9161"} {return branch}
   return NULL
  }
  findInst {
   set name [lindex $args 0]
   if {$name eq "tripwire_banked_addr8_hold_buf"} {
    return [expr {$::failure eq "duplicate" ? "buffer" : "NULL"}]
   }
   return $name
  }
  getMaster {return [expr {$obj eq "wire9161" ? "driver_master" : "sram_master"}]}
  findMaster {return driver_master}
  getName {
   if {$obj eq "driver_master"} {return [expr {$::failure eq "master" ? "wrong" : "sg13cmos5l_buf_2"}]}
   if {$obj eq "sram_master"} {return RM_IHPSG13_1P_512x16_c2_bm_bist}
   return $obj
  }
  getITerms {
   if {$::failure eq "connectivity"} {return {wire9161/X extra/A}}
   return {wire9161/X u_chip.u_sram.sram/A_ADDR[8]}
  }
  getBTerms {return {}}
  getInst {return [lindex [split $obj /] 0]}
  getMTerm {return [lindex [split $obj /] 1]}
  findITerm {return $obj/[lindex $args 0]}
  getNet {
   if {$obj eq {u_chip.u_sram.sram/A_ADDR[8]}} {return branch}
   return [expr {$::failure eq "power" ? "NULL" : "rail"}]
  }
  getLocation {return {10000 20000}}
  getDbUnitsPerMicron {return 1000}
  connect - disconnect - setLocation - setPlacementStatus {puts "$obj $method $args"}
  default {error "Unexpected method"}
 }
}
foreach name {block db branch wire9161 u_chip.u_sram.sram driver_master sram_master
 wire9161/X u_chip.u_sram.sram/A_ADDR[8] wire9161/VDD wire9161/VSS
 buffer buffer/A buffer/X buffer/VDD buffer/VSS downstream extra/A extra A X A_ADDR[8]} {
 interp alias {} $name {} dispatch $name
}
set failure ''' + failure + '\nsource {' + str(trial) + '}\ntripwire_delay_banked_sram_addr8\n')
    result = subprocess.run([interpreter, str(script)], capture_output=True, text=True)
    if failure != 'none':
        assert result.returncode != 0
        assert 'CREATE' not in result.stdout
    else:
        assert result.returncode == 0, result.stderr
        assert 'u_chip.u_sram.sram/A_ADDR[8] connect downstream' in result.stdout
        assert 'wire9161/X disconnect' not in result.stdout
        assert 'buffer setLocation 12000 20000' in result.stdout
        assert 'buffer/VDD connect rail' in result.stdout
