from pathlib import Path
import shutil
import subprocess
import pytest
from native_stock_screen import configure as base_configure
from native_post_antenna_screen import configure as prior_configure
from native_wire150_screen import configure


def test_trial_changes_only_wire_limit_and_hold_repair_target():
    source=base_configure(dict(CLOCK_PERIOD=20,PL_TARGET_DENSITY_PCT=56),
        'AREA 1',Path('src/signoff.sdc'),hold_target=.10,clock_cluster=8)
    before=prior_configure(source);after=configure(source)
    assert {k for k in before if before[k]!=after[k]}=={
        'GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH','GRT_RESIZER_HOLD_SLACK_MARGIN'}
    assert after['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH']==150
    assert after['GRT_RESIZER_HOLD_SLACK_MARGIN']==.125
    assert after['CLOCK_PERIOD']==20 and after['GRT_ALLOW_CONGESTION'] is False
    assert after['GRT_ANTENNA_REPAIR_MARGIN']==50
    assert before['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH']==100


def test_readonly_capture_probe_selects_ff_inputs_and_retains_base_audit(tmp_path):
    tcl=shutil.which('tclsh') or '/tmp/tripwire-tcl-runtime/bin/tclsh'
    if not Path(tcl).exists():pytest.skip('Tcl interpreter unavailable')
    probe=Path(__file__).with_name('native_timing_headroom_audit.tcl').resolve()
    script='''
rename source real_source
proc source {path} {
    if {[file tail $path] ne "native_post_antenna_audit.tcl"} {error "Wrong base audit"}
    puts "BASE_AUDIT"
}
proc all_registers {args} {
    if {$args ne "-edge_triggered -data_pins"} {error "Wrong capture selection"}
    return {ff0/D ff1/D}
}
proc report_checks {args} {
    set idx [lsearch -exact $args -to]
    if {[lindex $args [expr {$idx+1}]] ne "ff0/D ff1/D"} {error "Wrong capture pins"}
    puts "REPORT $args"
}
set corner_name nom_slow_1p08V_125C
set ::env(STEP_DIR) {%s}
real_source {%s}
'''%(tmp_path,probe)
    driver=tmp_path/'driver.tcl';driver.write_text(script)
    result=subprocess.run([tcl,str(driver)],text=True,capture_output=True,check=True)
    assert 'BASE_AUDIT' in result.stdout
    assert 'capture_setup.rpt' in result.stdout and 'capture_hold.rpt' in result.stdout
    assert result.stdout.count('REPORT ')==2
    assert not result.stderr


def test_workflow_stops_before_drt_and_retains_strict_receipts():
    import yaml
    p=Path(__file__).resolve().parents[2]/'.github/workflows/gds-native-wire150-hold125-screen.yaml'
    w=yaml.safe_load(p.read_text());steps=w['jobs']['harden']['steps']
    commands='\n'.join(s.get('run','') for s in steps)
    assert 'native_wire150_screen.py' in commands
    assert 'from librelane.flows.classic import Classic' in commands
    early=next(s for s in steps if s['name']=='Upload early gate evidence')['with']['path']
    assert 'capture_setup.rpt' in early and 'capture_hold.rpt' in early
    assert 'gates.json' in early
