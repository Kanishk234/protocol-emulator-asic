"""Exercise branch connectivity and fail-closed guards independently of OpenDB."""
from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.mark.parametrize("changed", [False, True])
def test_branch_rewires_only_audited_loads(tmp_path, changed):
    if shutil.which("tclsh") is None:
        pytest.skip("Tcl interpreter unavailable")
    trial = Path(__file__).with_name("critical_branch.tcl").resolve()
    script = tmp_path / "exercise.tcl"
    script.write_text(r'''
namespace eval ord {
    proc get_db_block {} {return block}
    proc get_db {} {return db}
}
namespace eval odb {
    proc dbInst_create {args} {puts "CREATE buffer"; return buffer}
    proc dbNet_create {args} {puts "CREATE net"; return downstream}
}
proc dispatch {obj method args} {
    switch $method {
        findNet {return [expr {[lindex $args 0] eq "_19783_" ? "branch" : "NULL"}]}
        findInst {
            set name [lindex $args 0]
            if {$name eq "tripwire_branch_buf"} {return NULL}
            return $name
        }
        findMaster - getMaster {return master}
        getName {
            if {$obj eq "master"} {return sg13cmos5l_o21ai_1}
            return $obj
        }
        getITerms {
            if {$::changed} {return {_25365_/Y _25366_/B1 extra/A}}
            return {_25365_/Y _25366_/B1 rebuffer5871/A}
        }
        getBTerms {return {}}
        getInst {return [lindex [split $obj /] 0]}
        getMTerm {return [lindex [split $obj /] 1]}
        findITerm {return $obj/[lindex $args 0]}
        getNet {return rail}
        getDbUnitsPerMicron {return 1000}
        connect - disconnect - setLocation - setPlacementStatus {puts "$obj $method $args"}
        default {error "Unexpected method $obj $method"}
    }
}
foreach name {block db branch master buffer downstream rail _25365_ _25366_ rebuffer5871
              _25365_/Y _25366_/B1 rebuffer5871/A extra extra/A Y B1 A
              _25365_/VDD _25365_/VSS buffer/A buffer/X buffer/VDD buffer/VSS} {
    interp alias {} $name {} dispatch $name
}
set changed ''' + str(int(changed)) + '\nsource {' + str(trial) + r'''}
tripwire_split_critical_branch
''')
    out = subprocess.run(["tclsh", str(script)], capture_output=True, text=True)
    if changed:
        assert out.returncode != 0
        assert "Audited branch connectivity changed" in out.stderr
        assert "CREATE" not in out.stdout
    else:
        assert out.returncode == 0, out.stderr
        assert "_25366_/B1 connect downstream" in out.stdout
        assert "rebuffer5871/A connect downstream" in out.stdout
        assert "_25365_/Y disconnect" not in out.stdout
        assert "buffer setLocation 563520 570780" in out.stdout
        assert "buffer/VDD connect rail" in out.stdout
        assert "TRIPWIRE critical branch:" in out.stdout
