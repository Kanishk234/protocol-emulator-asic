from pathlib import Path
import shutil
import subprocess
import pytest


@pytest.mark.parametrize("target", ["none", "lane", "sram", "unknown"])
@pytest.mark.parametrize("changed", [False, True])
def test_split_is_guarded_and_moves_exact_loads(tmp_path, target, changed):
    if not shutil.which("tclsh"):
        pytest.skip("Tcl required")
    script = r"""
namespace eval ord {
    proc get_db_block {} {return block}
    proc get_db {} {return db}
}
namespace eval odb {
    proc dbInst_create {args} {puts "CREATE buffer"; return buffer}
    proc dbNet_create {args} {puts "CREATE net"; return downstream}
}
proc unknown {obj method args} {
    switch -- $method {
        findNet {
            if {[lindex $args 0] in {_07896_ _04725_}} {return original}
            return NULL
        }
        findInst {
            if {[string match tripwire* [lindex $args 0]]} {return NULL}
            return [lindex $args 0]
        }
        getMaster {return nor_master}
        findMaster {return buf_master}
        getName {
            if {$obj eq "nor_master"} {return sg13cmos5l_nor4_1}
            return $obj
        }
        getITerms {
            if {$::changed} {return {wrong/Y wrong/A}}
            if {$::env(TRIPWIRE_SLEW_TARGET) eq "lane"} {
                return {_33713_/Y _34060_/B _34059_/B _33936_/B place7396/A place7402/A}
            }
            return {_30323_/Y _30324_/A2}
        }
        getBTerms {return {}}
        getInst {return [lindex [split $obj /] 0]}
        getMTerm {return [lindex [split $obj /] 1]}
        findITerm {return $obj/[lindex $args 0]}
        getNet {return rail}
        getDbUnitsPerMicron {return 1000}
        connect - disconnect - setLocation - setPlacementStatus {puts "$obj $method $args"}
        default {error "Unexpected method $method"}
    }
}
"""
    trial = Path(__file__).with_name("slew_split.tcl").resolve()
    script += f"\nset env(TRIPWIRE_SLEW_TARGET) {target}\nset changed {int(changed)}\nsource {{{trial}}}\ntripwire_split_critical_branch\n"
    p = tmp_path / "run.tcl"
    p.write_text(script)
    out = subprocess.run(["tclsh", str(p)], capture_output=True, text=True)
    if target == "unknown" or (changed and target != "none"):
        assert out.returncode != 0
        assert "CREATE" not in out.stdout
    else:
        assert out.returncode == 0, out.stderr
        if target == "none":
            assert "CREATE" not in out.stdout
        else:
            assert out.stdout.count("CREATE buffer") == 1
            expected = ["_34060_/B", "_34059_/B", "_33936_/B", "place7396/A", "place7402/A"] if target == "lane" else ["_30324_/A2"]
            for load in expected:
                assert f"{load} disconnect" in out.stdout
                assert f"{load} connect downstream" in out.stdout
            assert out.stdout.count(" disconnect") == len(expected)
            assert "buffer/A connect original" in out.stdout
            assert "buffer/X connect downstream" in out.stdout
            assert "setPlacementStatus PLACED" in out.stdout
