import copy
import json
import os
from pathlib import Path
import subprocess
import pytest
from post_antenna_fanout_audit import audit,validate_batch


def case():
    before='sg13cmos5l_buf_1 driver (.A(in), .X(source));\n'
    before+='\n'.join(f'sg13cmos5l_buf_1 sink{i} (.A(source), .X(out{i}));' for i in range(8))
    before+='\nsg13cmos5l_antennanp diode (.A(source));'
    groups=[];after=before
    sinks=[(f'sink{i}','A') for i in range(8)]+[('diode','A')]
    for index,start in enumerate(range(0,9,4)):
        name=f'tripwire_postant_0_{index}';net=name+'_net';selected=sinks[start:start+4]
        groups.append(dict(buffer=name,net=net,source_net='source',master='sg13cmos5l_buf_4',sinks=selected))
        for n,p in selected:after=after.replace(n+' (.A(source)',n+' (.A('+net+')')
        after+='\nsg13cmos5l_buf_4 '+name+' (.A(source), .X('+net+'));'
    return before,after,{'groups':groups}


def test_exact_batch_preserves_every_diode_and_original_cell():
    assert validate_batch(*case(),0)==3


@pytest.mark.parametrize('fault',['master','name','sink','incomplete','unplanned_cell','lost_diode','protected','not_overloaded'])
def test_batch_rejects_unreviewed_changes(fault):
    before,after,p=case();p=copy.deepcopy(p)
    if fault=='master':p['groups'][0]['master']='sg13cmos5l_inv_1'
    elif fault=='name':p['groups'][0]['buffer']='unreviewed'
    elif fault=='sink':p['groups'][0]['sinks'][0]=('other','A')
    elif fault=='incomplete':p['groups']=p['groups'][:-1]
    elif fault=='unplanned_cell':after+='sg13cmos5l_buf_1 other (.A(in), .X(out));'
    elif fault=='lost_diode':after=after.replace('sg13cmos5l_antennanp diode','sg13cmos5l_buf_1 diode')
    elif fault=='protected':before+='sg13cmos5l_dfrbpq_1 flop (.CLK(source), .D(d), .Q(q), .RESET_B(reset));'
    else:before=before.replace('sink0 (.A(source)','sink0 (.A(other)')
    with pytest.raises(ValueError):validate_batch(before,after,p,0)


def test_history_requires_convergence_and_checks_final_antenna_interval(tmp_path):
    before,after,p=case()
    (tmp_path/'postant_0.json').write_text(json.dumps(p))
    (tmp_path/'postant_0.before.nl.v').write_text(before)
    (tmp_path/'postant_0.after.nl.v').write_text(after)
    log='TRIPWIRE post-antenna fanout: batch 0 added 3 BUF4 cells\nTRIPWIRE post-antenna fanout: converged after 1 batches'
    result=audit(before,after,tmp_path,log)
    assert result['post_antenna_buffers']==3
    with pytest.raises(ValueError):audit(before,after,tmp_path,'missing')
    with pytest.raises(ValueError):audit(before,after.replace('.A(in)','.A(wrong)'),tmp_path,log)


def test_zero_batch_still_requires_convergence_and_identity_conservation(tmp_path):
    before,_,_=case()
    assert audit(before,before,tmp_path,'TRIPWIRE post-antenna fanout: converged after 0 batches')['post_antenna_buffers']==0
    with pytest.raises(ValueError):audit(before,before,tmp_path,'')


MOCK=r'''
namespace eval ord {proc get_db_block {} {return block}}
namespace eval odb {}
set wiremap [dict create driver_X source rail_VDD power rail_VSS ground]
set created 0
proc block {method args} {
    if {$method eq "getNets"} {return {source}}
    if {$method in {findInst findNet}} {return NULL}
    error unexpected
}
proc source {method} {
    if {$method eq "getSigType"} {return SIGNAL}
    if {$method eq "getName"} {return source}
    if {$method eq "getBTerms"} {return {}}
    if {$method eq "getITerms"} {return [concat driver_X $::sinks]}
    error unexpected
}
proc inst {name method args} {
    if {$method eq "getName"} {return $name}
    if {$method eq "getMaster"} {return driver_master}
    if {$method eq "getLocation"} {return {0 0}}
    if {$method eq "getOrient"} {return R0}
    if {$method eq "findITerm"} {
        set pin [lindex $args 0]
        if {$name eq "driver" && $pin in {VDD VSS}} {return rail_$pin}
        set term ${name}_$pin
        if {![llength [info commands $term]]} {interp alias {} $term {} term $name $pin}
        return $term
    }
    if {$method in {setOrient setLocation setPlacementStatus}} {return}
    error unexpected
}
proc term {name pin method args} {
    if {$method eq "getMTerm"} {return pin_$pin}
    if {$method eq "getInst"} {return $name}
    if {$method eq "getNet"} {return [dict get $::wiremap ${name}_$pin]}
    if {$method eq "connect"} {dict set ::wiremap ${name}_$pin [lindex $args 0];return}
    if {$method eq "disconnect"} {dict set ::wiremap ${name}_$pin NULL;return}
    error unexpected
}
proc pin {name method} {return $name}
foreach p {A X VDD VSS CLK} {interp alias {} pin_$p {} pin $p}
proc driver_master {method} {return sg13cmos5l_buf_1}
proc buffer_master {method} {return {pin_A pin_X pin_VDD pin_VSS}}
proc database {method name} {return buffer_master}
proc ord::get_db {} {return database}
proc odb::dbInst_create {block master name} {incr ::created;interp alias {} $name {} inst $name;return $name}
proc newnet {name method args} {if {$method eq "getName"} {return $name};return}
proc odb::dbNet_create {block name} {interp alias {} $name {} newnet $name;return $name}
foreach name {driver rail} {interp alias {} $name {} inst $name}
interp alias {} driver_X {} term driver X
foreach p {VDD VSS} {interp alias {} rail_$p {} term rail $p}
set sinks {}
for {set i 0} {$i<9} {incr i} {
    set name sink$i;interp alias {} $name {} inst $name
    interp alias {} ${name}_A {} term $name A
    dict set wiremap ${name}_A source;lappend sinks ${name}_A
}
'''


@pytest.mark.parametrize('fault',['none','clock','power'])
def test_tcl_batch_preflights_and_writes_auditable_branch_receipt(tmp_path,fault):
    helper=Path(__file__).with_name('post_antenna_fanout.tcl').resolve()
    electrical=Path(__file__).with_name('electrical_repair.tcl').resolve()
    # Define the mock source object after loading the Tcl helpers so it does not
    # shadow Tcl's builtin source while loading them.
    text=f'source {{{electrical}}}\nsource {{{helper}}}\n'+MOCK
    if fault=='clock':text+='interp alias {} sink0_A {} term sink0 CLK\n'
    if fault=='power':text+='dict set wiremap rail_VDD NULL\n'
    receipt=tmp_path/'batch.json'
    text+=f'set rc [catch {{set g [tripwire_post_antenna_groups 0];tripwire_post_antenna_apply $g {{{receipt}}}}} message]\nputs "RESULT $rc CREATED $created $message"\n'
    p=tmp_path/'batch.tcl';p.write_text(text)
    result=subprocess.run([os.environ.get('TRIPWIRE_TCLSH','tclsh'),str(p)],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    if fault=='none':
        assert 'RESULT 0 CREATED 3' in result.stdout
        groups=json.loads(receipt.read_text())['groups']
        assert [len(g['sinks']) for g in groups]==[4,4,1]
        assert len({tuple(s) for g in groups for s in g['sinks']})==9
    elif fault=='clock':
        assert 'RESULT 0 CREATED 0' in result.stdout
        assert json.loads(receipt.read_text())['groups']==[]
    else:assert 'RESULT 1 CREATED 0' in result.stdout


@pytest.mark.parametrize('iteration',[0,1])
def test_inherited_postant_cells_and_orphan_nets_are_preserved(tmp_path,iteration):
    helper=Path(__file__).with_name('post_antenna_fanout.tcl').resolve()
    electrical=Path(__file__).with_name('electrical_repair.tcl').resolve()
    text=f'source {{{electrical}}}\nsource {{{helper}}}\n'+MOCK
    text+=r'''
rename block original_block
proc block {method args} {
    if {$method eq "findInst" && [lindex $args 0] eq $::occupied_inst} {return inherited}
    if {$method eq "findNet" && [lindex $args 0] eq $::occupied_net} {return orphan}
    return [original_block $method {*}$args]
}
'''
    text+=f'set occupied_inst tripwire_postant_{iteration}_0\nset occupied_net tripwire_postant_{iteration}_1_net\n'
    receipt=tmp_path/'batch.json'
    text+=f'set rc [catch {{set g [tripwire_post_antenna_groups {iteration}];tripwire_post_antenna_apply $g {{{receipt}}}}} message]\nputs "RESULT $rc CREATED $created $message"\n'
    path=tmp_path/'inherited.tcl';path.write_text(text)
    result=subprocess.run([os.environ.get('TRIPWIRE_TCLSH','tclsh'),str(path)],capture_output=True,text=True)
    assert result.returncode==0 and 'RESULT 0 CREATED 3' in result.stdout,result.stdout+result.stderr
    groups=json.loads(receipt.read_text())['groups']
    assert [g['buffer'] for g in groups]==[f'tripwire_postant_{iteration}_{i}' for i in (2,3,4)]
    assert len({tuple(s) for g in groups for s in g['sinks']})==9


def test_wrapper_runs_post_antenna_repair_in_initialized_process(tmp_path):
    binary=tmp_path/'openroad';binary.write_text('#!/bin/bash\ncat "${@: -1}"\n');binary.chmod(0o755)
    source='source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl'
    p=tmp_path/'grt.tcl';p.write_text('read_current_odb\n'+source+'\nwrite_views\n')
    env=dict(os.environ,PATH=str(tmp_path)+os.pathsep+os.environ['PATH'],RUNNER_TEMP=str(tmp_path))
    r=subprocess.run(['bash',str(Path(__file__).with_name('openroad_postant_fanout_wrapper.sh')),str(p)],env=env,capture_output=True,text=True)
    assert r.returncode==0 and r.stdout.count(source)==1
    assert r.stdout.index(source)<r.stdout.index('log_cmd repair_antennas')<r.stdout.index('tripwire_post_antenna_finish')<r.stdout.index('write_views')


def test_workflow_and_controller_remain_source_bound_and_screen_only():
    import yaml
    from postant_screen import PROFILE
    from postant_screen_plan import BINDING
    assert BINDING['source_run']==38353731199 and BINDING['hold_count']==0
    assert PROFILE['post_antenna_audit'] is audit
    w=yaml.safe_load((Path(__file__).resolve().parents[2]/'.github/workflows/gds-postant-fanout-screen.yaml').read_text())
    d=next(s for s in w['jobs']['harden']['steps'] if 'download-artifact@' in s.get('uses',''))
    assert d['with']['name']=='gds-screen-fanout-finish-38353731199'
    assert d['with']['run-id']==38353731199


@pytest.mark.parametrize('converges',[True,False])
def test_tcl_loop_is_bounded_and_repairs_inside_incremental_routing(tmp_path,converges):
    helper=Path(__file__).with_name('post_antenna_fanout.tcl').resolve()
    dpl=tmp_path/'openroad/common';dpl.mkdir(parents=True)
    (dpl/'dpl.tcl').write_text('lappend trace dpl\n')
    text=f'source {{{helper}}}\nset ::env(STEP_DIR) {{{tmp_path}}}\nset ::env(SCRIPTS_DIR) {{{tmp_path}}}\nset converges {int(converges)}\n'
    text+='''
set trace {}
proc tripwire_post_antenna_groups {iteration} {
    if {$iteration>0 && $::converges} {return {}}
    return {group}
}
proc tripwire_post_antenna_apply {groups receipt} {lappend ::trace apply}
proc tripwire_freeze_existing_placement {} {lappend ::trace freeze;return saved}
proc tripwire_restore_placement_status {saved} {lappend ::trace restore}
proc global_route {args} {lappend ::trace [lindex $args 0]}
proc write_verilog {path} {return}
proc log_cmd {args} {lappend ::trace antenna}
set rc [catch {tripwire_post_antenna_finish {diode -iterations 3}} message]
puts "RESULT $rc TRACE $trace MESSAGE $message"
'''
    p=tmp_path/'loop.tcl';p.write_text(text)
    r=subprocess.run([os.environ.get('TRIPWIRE_TCLSH','tclsh'),str(p)],capture_output=True,text=True)
    assert r.returncode==0
    assert 'freeze -start_incremental apply dpl restore -end_incremental antenna' in r.stdout
    if converges:
        assert 'RESULT 0' in r.stdout and 'converged after 1 batches' in r.stdout
    else:
        assert 'RESULT 1' in r.stdout and 'did not converge within two batches' in r.stdout
        assert r.stdout.count('added 1 BUF4 cells')==2
