import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest
import yaml

from drop_leaf_hold import TARGETS, validate_drop_leaf_hold
from event_nor2_screen import promote_netlists


def fixture_netlists():
    before = ('sg13cmos5l_nor2_2 _27853_ (.A(a), .B(b), .Y(c));\n'
              'sg13cmos5l_nor2_2 _31567_ (.A(d), .B(e), .Y(f));\n')
    for sink, net, driver, master in TARGETS:
        before += f'{master} {driver} (.Y({net}));\n'
        before += f'sg13cmos5l_dfrbpq_1 {sink} (.D({net}), .Q(q{sink}), .CLK(clk), .RESET_B(reset));\n'
    after = before
    for sink, net, *_ in TARGETS:
        new_net = f'tripwire_drop_hold_net{sink}'
        after = after.replace(f'.D({net})', f'.D({new_net})')
        after += f'sg13cmos5l_buf_1 tripwire_drop_hold_buf{sink} (.A({net}), .X({new_net}));\n'
    return before, after


def test_exact_nine_buffers_only():
    before, after = fixture_netlists()
    validate_drop_leaf_hold(before, after)
    for bad in (before, after.replace('.CLK(clk)', '.CLK(wrong)', 1),
                after.replace('.RESET_B(reset)', '.RESET_B(wrong)', 1),
                after.replace('sg13cmos5l_buf_1', 'sg13cmos5l_buf_2', 1),
                after.replace('.A(_00384_)', '.A(wrong)'),
                after + '\nsg13cmos5l_inv_1 extra (.A(a), .Y(b));'):
        with pytest.raises(ValueError):
            validate_drop_leaf_hold(before, bad)
    with pytest.raises(ValueError):
        validate_drop_leaf_hold(before + '\nsg13cmos5l_inv_1 extra (.A(_00384_), .Y(z));', after)
    with pytest.raises(ValueError):
        validate_drop_leaf_hold(after, after)


def test_powered_views_and_source_baseline_required(tmp_path):
    before, after = fixture_netlists()
    source = tmp_path / 'original.v'
    source.write_text(before)
    state = tmp_path / 'state_out.json'
    state.write_text(json.dumps({'odb': str(tmp_path / 'chip.odb')}))
    (tmp_path / 'chip.baseline.nl.v').write_text(before)
    (tmp_path / 'chip.eco.nl.v').write_text(after)
    pnl = tmp_path / 'chip.eco.pnl.v'
    pnl.write_text(after)
    result = json.loads(promote_netlists(state, source, hold=True).read_text())
    assert all(result[k] is None for k in ('spef', 'sdf', 'lib'))
    pnl.write_text(before)
    with pytest.raises(ValueError, match='missing hold leaf'):
        promote_netlists(state, source, hold=True)


def test_inventory_and_workflow_are_frozen():
    helper = Path(__file__).with_name('drop_leaf_hold.tcl').read_text()
    rows = re.findall(r'\{(_\d+_) (_\d+_) (_\d+_) (sg13cmos5l_\w+)\}', helper)
    assert tuple(rows) == TARGETS
    root = Path(__file__).parents[2]
    job = yaml.safe_load((root / '.github/workflows/gds-drop-leaf-hold-screen.yaml').read_text())['jobs']['harden']
    assert job['env']['ECO_PROFILE'] == 'drop-hold'
    download = next(s for s in job['steps'] if s.get('uses', '').startswith('actions/download-artifact'))
    assert download['with']['run-id'] == 37803300460
    assert download['with']['name'] == 'gds-drop-event-37803300460'
    docker = (root / 'scripts/ci/Dockerfile.openroad-drop-hold').read_text()
    assert 'COPY drop_leaf_hold.tcl' in docker
    assert 'COPY drop_event_size.tcl' not in docker


@pytest.mark.parametrize('failure', ['none', 'last_leaf', 'fanout', 'master', 'power', 'duplicate', 'pins'])
def test_all_leaves_preflight_before_any_mutation(tmp_path, failure):
    interpreter = os.environ.get('TRIPWIRE_TCLSH', 'tclsh')
    if shutil.which(interpreter) is None:
        pytest.skip('Tcl interpreter unavailable')
    header = 'set masters {}\nset branches {}\nset nets {}\n'
    for sink, net, driver, master in TARGETS:
        header += f'dict set masters {sink} sg13cmos5l_dfrbpq_1\n'
        header += f'dict set masters {driver} {master}\n'
        header += f'dict set branches {net} {{{driver}/Y {sink}/D}}\n'
        header += f'dict set nets {driver}/Y {net}\ndict set nets {sink}/D {net}\n'
        for obj in (sink, driver):
            for pin in ('VDD', 'VSS'):
                header += f'dict set nets {obj}/{pin} rail{pin}\n'
    helper = Path(__file__).with_name('drop_leaf_hold.tcl').resolve()
    script = tmp_path / 'exercise.tcl'
    script.write_text(header + r'''
namespace eval ord {
 proc get_db_block {} {return block}
 proc get_db {} {return db}
}
proc alias_obj {obj} {if {![llength [info commands $obj]]} {interp alias {} $obj {} dispatch $obj}; return $obj}
namespace eval odb {
 proc dbInst_create {block master name} {puts "CREATE $name"; return [alias_obj $name]}
 proc dbNet_create {block name} {puts "CREATE $name"; return [alias_obj $name]}
}
proc dispatch {obj method args} {
 switch $method {
  findInst {
   set name [lindex $args 0]
   if {$::failure eq "last_leaf" && $name eq "_46519_"} {return NULL}
   if {[dict exists $::masters $name]} {return [alias_obj $name]}
   if {$::failure eq "duplicate"} {return [alias_obj $name]}
   return NULL
  }
  findNet {
   set name [lindex $args 0]
   if {[dict exists $::branches $name]} {return [alias_obj $name]}
   return NULL
  }
  findMaster {return [alias_obj buffer_master]}
  getMaster {return [alias_obj master_$obj]}
  getName {
   if {[string match master_* $obj]} {
    if {$::failure eq "master"} {return wrong}
    return [dict get $::masters [string range $obj 7 end]]
   }
   return $obj
  }
  getMTerms {
   foreach name {A X VDD VSS} {alias_obj $name}
   return [expr {$::failure eq "pins" ? "A X" : "A X VDD VSS"}]
  }
  getITerms {
   set result [dict get $::branches $obj]
   foreach name $result {alias_obj $name}
   if {$::failure eq "fanout"} {lappend result [alias_obj extra/A]}
   return $result
  }
  getBTerms {return {}}
  getInst {return [alias_obj [lindex [split $obj /] 0]]}
  getMTerm {return [alias_obj [lindex [split $obj /] 1]]}
  findITerm {return [alias_obj $obj/[lindex $args 0]]}
  getNet {
   if {$::failure eq "power" && [string match */VDD $obj]} {return NULL}
   return [dict get $::nets $obj]
  }
  getLocation {return {10000 20000}}
  getDbUnitsPerMicron {return 1000}
  connect {dict set ::nets $obj [lindex $args 0]; puts "$obj connect $args"}
  disconnect - setLocation - setPlacementStatus {puts "$obj $method $args"}
  default {error "Unexpected method"}
 }
}
alias_obj block
alias_obj db
''' + f'set failure {failure}\nsource {{{helper}}}\ntripwire_delay_drop_leaves\n')
    result = subprocess.run([interpreter, str(script)], capture_output=True, text=True)
    if failure == 'none':
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stdout.count('CREATE') == 18
        for sink, *_ in TARGETS:
            assert f'{sink}/D connect tripwire_drop_hold_net{sink}' in result.stdout
        assert '/CLK' not in result.stdout and '/RESET_B' not in result.stdout
        assert '/Y disconnect' not in result.stdout
    else:
        assert result.returncode != 0
        assert 'CREATE' not in result.stdout
        expected = {'last_leaf': 'Missing', 'fanout': 'connectivity changed',
                    'master': 'masters changed', 'power': 'supplies',
                    'duplicate': 'Duplicate', 'pins': 'buffer pins'}[failure]
        assert expected in result.stdout + result.stderr
