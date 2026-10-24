"""Analysis-only, configured R1 cell-delay probe; no extracted timing acceptance.

Prepare in the project venv, run the emitted Yosys/OpenSTA scripts in the pinned
EDA environment, then audit in the venv. Chip netlists are never specialized.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess

from configured_smoke import complete_native_exports

ROOT=Path(__file__).resolve().parents[2]
LIB_SHA='3ee222c580ba33acb2131ac2bf224ff8ee9700751835b73aaec72b670bb31d3c'
SNAPSHOT_SHA='0491a427285f53b27db8166c875d76536fe237c4e619277be297d8791ed94ba7'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def quoted(value):
    value=str(value)
    if any(c in value for c in '{}\r\n'):raise ValueError('Unsafe Tcl path/name')
    return '{'+value+'}'


def topology(module):
    groups=defaultdict(list)
    for name,port in module['ports'].items():
        for index,bit in enumerate(port['bits']):groups[bit].append(f'port:{name}:{index}')
    for name,cell in module['cells'].items():
        for pin,bits in cell['connections'].items():
            for index,bit in enumerate(bits):groups[bit].append(f'cell:{name}:{pin}:{index}')
    for bit in ('0','1','x','z'):groups[bit].append('constant:'+bit)
    return {tuple(sorted(anchors)) for anchors in groups.values()}


def same_topology(original,converted):
    if set(original['ports'])!=set(converted['ports']) or set(original['cells'])!=set(converted['cells']):
        raise ValueError('Structural conversion changed ports/cells')
    for name,port in original['ports'].items():
        other=converted['ports'][name]
        if port['direction']!=other['direction'] or len(port['bits'])!=len(other['bits']):
            raise ValueError('Structural conversion changed a port')
    for name,cell in original['cells'].items():
        if cell['type']!=converted['cells'][name]['type']:raise ValueError('Structural conversion changed a master')
    if topology(original)!=topology(converted):raise ValueError('Structural conversion changed connectivity')


def prepare(model,baseline,native_audit,functional,liberty,out):
    model,baseline,native_audit,functional,liberty,out=(Path(p).resolve() for p in (model,baseline,native_audit,functional,liberty,out))
    proof_path=functional/'configured-smoke.json';proof=json.loads(proof_path.read_text())
    snapshot=functional/'configuration-state.json';boundary=functional/'tb.v'
    if (not proof['passed'] or proof['postphysical_tile_instances_tested']!=40 or not proof['user_restart_probe_tested'] or
        proof['management_spi_shell_tested'] or proof['quiescence']['policy']!='unused-padded-GND-only' or
        proof['configuration_snapshot']['sha256']!=SNAPSHOT_SHA or sha(snapshot)!=SNAPSHOT_SHA):
        raise ValueError('Require the authenticated quiescent direct-primary state')
    expected=proof['input_sha256']
    for path,suffix in [(boundary,'/tb.v'),(model/'fabric.v','/resource/fabric.v')]:
        matches=[digest for name,digest in expected.items() if name.endswith(suffix)]
        if matches!=[sha(path)]:raise ValueError('Functional source binding changed')
    if sha(liberty)!=LIB_SHA:raise ValueError('Changed pinned slow-corner library')
    exports=complete_native_exports(native_audit)
    if any(sha(path) not in expected.values() for path in exports.values()):raise ValueError('Native exports differ from loaded proof')
    frozen=json.loads((baseline/'connections.json').read_text())['modules']['eFPGA']
    census=json.loads((baseline/'manifest.json').read_text())['tiles']
    state=json.loads(snapshot.read_text())['tiles']
    if set(state)!=set(frozen['cells']) or len(state)!=40:raise ValueError('Incomplete tile state')
    config=[]
    for tile,row in state.items():
        kind=frozen['cells'][tile]['type']
        if row['tile_type']!=kind or len(row['q'])!=census[kind]['configuration_latches']:raise ValueError('State census changed')
        for cell,value in row['q'].items():
            if not re.fullmatch(r'_\d+_',cell) or value not in ('0','1'):raise ValueError('Invalid observed configuration')
            config.append((tile+'/'+cell,value))
    if len(config)!=8736:raise ValueError('Configuration coverage changed')
    zero=re.findall(r"\.(Tile_\w+)\(1'b0\)",boundary.read_text())
    if len(set(zero))!=27 or any(frozen['ports'][p]['direction']!='input' for p in zero):raise ValueError('Changed verified input boundary')
    out.mkdir(parents=True,exist_ok=False)
    paths=[Path(__file__),ROOT/'spikes/r1/configured_smoke.py',proof_path,snapshot,boundary,liberty,native_audit,
           baseline/'connections.json',baseline/'manifest.json',model/'fabric.v',*exports.values()]
    yosys=[f'read_verilog -lib {quoted(path)}' for path in exports.values()]
    # Yosys strings use double quotes; reject quotes rather than interpreting input.
    if any('"' in str(path) for path in paths):raise ValueError('Unsafe tool path')
    yosys=[line.replace('{','"').replace('}','"') for line in yosys]
    yosys += [f'read_verilog "{model/"fabric.v"}"','hierarchy -check -top eFPGA',
              f'write_json "{out/"top.json"}"',f'write_verilog -noattr "{out/"fabric_structural.v"}"']
    (out/'elaborate.ys').write_text('\n'.join(yosys)+'\n')
    common=[f'read_liberty {quoted(liberty)}',*[f'read_verilog {quoted(path)}' for path in exports.values()],
            f'read_verilog {quoted(out/"fabric_structural.v")}','link_design eFPGA','set observed 0']
    for name,value in config:
        common += [f'set p [get_pins -quiet {quoted(name+"/Q")}]',
                   'if {[llength $p]!=1} {error "missing configuration pin"}',f'set_case_analysis {value} $p','incr observed']
    common += ['if {$observed!=8736} {error "configuration census"}','set frames [get_ports {FrameData* FrameStrobe*}]',
               'if {[llength $frames]!=320} {error "frame census"}','set_case_analysis 0 $frames',
               'set_case_analysis 1 [get_ports Tile_X1Y4_B_OUT_top]','set_case_analysis 0 [get_ports Tile_X0Y4_SYS_RESET_RESET_top]']
    common += [f'set_case_analysis 0 [get_ports {quoted(port)}]' for port in zero]
    common += ['create_clock -name run -period 20 [get_ports Tile_X1Y4_A_OUT_top]',
               'set_input_transition 0.2 [all_inputs]','set_load 0.01 [all_outputs]',
               'foreach p [all_inputs] {if {[get_full_name $p]!="Tile_X1Y4_A_OUT_top"} {set_input_delay 0 -clock run $p}}',
               'set_output_delay 0 -clock run [all_outputs]',
               'report_checks -path_delay max -group_path_count 3 -fields {slew cap fanout} -digits 4',
               'set closed 0']
    for name,value in config:
        common += [f'if {{[sta::pin_sim_logic_value [lindex [get_pins {quoted(name+"/GATE")}] 0]]!="0" || [sta::pin_sim_logic_value [lindex [get_pins {quoted(name+"/Q")}] 0]]!="{value}"}} {{error "configuration case/gate mismatch"}}','incr closed']
    common += ['puts "RUNSTA_CONFIGURATION $observed"','puts "RUNSTA_CLOSED $closed"',
               'set observables [dict create]',
               'foreach p [concat [all_outputs] [all_registers -edge_triggered -data_pins] [all_registers -edge_triggered -clock_pins] [all_registers -edge_triggered -async_pins]] {dict set observables [get_full_name $p] 1}',
               'set clocked [dict create]',
               'foreach r [all_registers -edge_triggered -clock run] {dict set clocked [get_full_name $r] 1}',
               '''foreach r [all_registers -edge_triggered] {
set name [get_full_name $r]
set c [get_pins -quiet ${name}/CLK];set d [get_pins -quiet ${name}/D];set q [get_pins -quiet ${name}/Q]
if {[llength $c]!=1 || [llength $d]!=1 || [llength $q]!=1} {error "unexpected edge-register schema"}
set endpoints [get_fanout -from $q -flat -endpoints_only -trace_arcs timing];set names {}
foreach p $endpoints {set e [get_full_name $p];if {[dict exists $observables $e]} {lappend names $e}}
puts "RUNSTA_FF\t$name\t[sta::pin_sim_logic_value [lindex $c 0]]\t[dict exists $clocked $name]\t[join $names ,]\t[sta::pin_sim_logic_value [lindex $d 0]]"
}''',
               'set paths [find_timing_paths -from [concat [all_inputs] [all_registers -edge_triggered -clock_pins]] -to [concat [all_outputs] [all_registers -edge_triggered -data_pins]] -path_delay max -group_path_count 10000]',
               'foreach p $paths {puts "RUNSTA_ENDPOINT\t[get_full_name [get_property $p endpoint]]\t[get_property $p slack]"}',
               'check_setup -loops -verbose','puts "RUNSTA_END"']
    for name,mode in [('static',0),('dynamic',1)]:
        (out/(name+'.tcl')).write_text(f'set sta_dynamic_loop_breaking {mode}\n'+'\n'.join(common)+'\n')
    rendered=[out/'elaborate.ys',out/'static.tcl',out/'dynamic.tcl']
    plan=dict(input_sha256={str(p):sha(p) for p in paths},rendered_sha256={p.name:sha(p) for p in rendered},baseline=str(baseline),
              functional_run=proof['run'],functional_source=proof['source'],clock_period_ns=20,
              scope='One primary RUN image, verified spare inputs fixed to zero; cell delays/loads only, ideal clock, no shell, placement RC, SPEF or SDF. Structural loop cuts remain reported; compare both loop policies. No physical/configured timing acceptance.')
    (out/'plan.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')


def parse_log(text):
    if not text.endswith('RUNSTA_END\n') or re.search(r'^Error:',text,re.M):raise ValueError('Incomplete timing execution')
    counts={};ffs={};endpoints={}
    for line in text.splitlines():
        if line.startswith('RUNSTA_CONFIGURATION ') or line.startswith('RUNSTA_CLOSED '):
            key,value=line.split();
            if key in counts:raise ValueError('Duplicate configuration census')
            counts[key]=int(value)
        elif line.startswith('RUNSTA_FF\t'):
            _,name,clock,clocked,fanout,data=line.split('\t')
            if name in ffs or clocked not in ('0','1'):raise ValueError('Invalid register coverage')
            ffs[name]=dict(clock=clock,clocked=clocked=='1',fanout=fanout,data=data)
        elif line.startswith('RUNSTA_ENDPOINT\t'):
            _,name,value=line.split('\t');slack=float(value)
            if name in endpoints or not math.isfinite(slack):raise ValueError('Invalid endpoint coverage')
            endpoints[name]=slack
    if counts!={'RUNSTA_CONFIGURATION':8736,'RUNSTA_CLOSED':8736}:raise ValueError('Incomplete case constraints')
    return dict(ffs=ffs,endpoints=endpoints,structural_loops=sum(map(int,re.findall(r'There (?:are|is) (\d+) combinational loop',text))))


def compare(first,second,expected_registers=370):
    if first['ffs']!=second['ffs'] or len(first['ffs'])!=expected_registers:raise ValueError('Register coverage differs')
    a,b=first['endpoints'],second['endpoints']
    if not a or set(a)!=set(b):raise ValueError('Loop policy changes endpoint coverage')
    differences=[dict(endpoint=n,static_slack_ns=a[n],dynamic_slack_ns=b[n],difference_ns=a[n]-b[n])
                 for n in sorted(a) if abs(a[n]-b[n])>1e-6]
    inactive=constant=timed=0
    for name,row in first['ffs'].items():
        if not row['clocked']:
            if row['clock']!='0' or row['fanout']:raise ValueError('Uncovered observable or nonconstant clock')
            inactive+=1
        elif name+'/D' in a:timed+=1
        elif row['data'] in ('0','1'):constant+=1
        else:raise ValueError('Active register data has no timing coverage')
    envelope={n:min(a[n],b[n]) for n in a}
    return dict(edge_registers=len(first['ffs']),inactive_unobservable=inactive,clocked_timed=timed,clocked_constant_data=constant,
                endpoints=len(a),worst_slack_ns=min(envelope.values()),worst_endpoint=min(envelope,key=envelope.get),
                structural_loops=first['structural_loops'],loop_policy_sensitive=bool(differences),loop_policy_differences=differences)


def audit(out):
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    result=dict(passed=False,run=os.environ.get('GITHUB_RUN_ID'),attempt=os.environ.get('GITHUB_RUN_ATTEMPT'),
                source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                physical_acceptance=False,timing_acceptance=False,scope=plan['scope'])
    try:
        for path,digest in plan['input_sha256'].items():
            if sha(path)!=digest:raise ValueError('Analysis input changed')
        for name,digest in plan['rendered_sha256'].items():
            if sha(out/name)!=digest:raise ValueError('Analysis constraints changed')
        old=json.loads((Path(plan['baseline'])/'connections.json').read_text())['modules']['eFPGA']
        new=json.loads((out/'top.json').read_text())['modules']['eFPGA'];same_topology(old,new)
        result.update(compare(*(parse_log((out/(name+'.log')).read_text()) for name in ('static','dynamic'))))
        result['cell_only_setup_nonnegative']=result['worst_slack_ns']>=0
        result['passed']=result['cell_only_setup_nonnegative'] and not result['loop_policy_sensitive']
        if result['loop_policy_sensitive']:
            result['failure_kind']='loop_policy_sensitive';result['error']='Loop policy changes endpoint timing; configured timing remains unqualified'
        elif not result['passed']:
            result['failure_kind']='cell_only_setup';result['error']='Necessary cell-only setup screen failed'
    except Exception as exc:result.update(failure_kind='analysis_error',error=str(exc))
    (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    if not result['passed']:raise ValueError(result['error'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare')
    for name in ('model','baseline','native-audit','functional','liberty','out'):p.add_argument('--'+name,type=Path,required=True)
    sub.add_parser('audit').add_argument('--out',type=Path,required=True)
    args=vars(parser.parse_args());mode=args.pop('mode')
    (prepare if mode=='prepare' else audit)(**args)
