from pathlib import Path
import subprocess
import pytest


@pytest.mark.parametrize('change', ['none', 'location', 'orientation'])
def test_lock_boundary_and_restore(tmp_path, change):
    helper = Path(__file__).with_name('targeted_placement_lock.tcl').resolve()
    script = tmp_path / 'lock.tcl'
    script.write_text('''namespace eval ord {proc get_db_block {} {return block}}
proc block {method args} {return {keep move}}
set statuses [dict create keep PLACED move PLACED]
set changed none
proc dispatch {name method args} {
 switch $method {
  getName {return $name}
  getPlacementStatus {return [dict get $::statuses $name]}
  setPlacementStatus {dict set ::statuses $name [lindex $args 0]}
  getLocation {if {$name eq "keep" && $::changed eq "location"} {return {11 20}}; return {10 20}}
  getOrient {if {$name eq "keep" && $::changed eq "orientation"} {return MX}; return R0}
 }
}
interp alias {} keep {} dispatch keep
interp alias {} move {} dispatch move
''' + f'source {{{helper}}}\n' + '''set saved [tripwire_lock_outside {move}]
if {[dict get $statuses keep] ne "LOCKED" || [dict get $statuses move] ne "PLACED"} {error "Wrong boundary"}
''' + f'set changed {change}\n' + '''set rc [catch {tripwire_verify_restore_locked $saved} message]
if {[dict get $statuses keep] ne "PLACED"} {error "Status not restored"}
puts "RESULT $rc"
''')
    result = subprocess.run(['yosys', '-Q', '-T', '-c', str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f'RESULT {0 if change == "none" else 1}' in result.stdout
