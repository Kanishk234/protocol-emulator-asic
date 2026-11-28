"""Isolated native primitive D-buffer fit/routing probe; never timing acceptance."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from assembly_catalog import sha
from detailed_context import prepare as prepare_control
from detailed_leaf import OBSERVER
from global_support import NATIVE_SHA

MASTER='sg13cmos5l_buf_1'
FF='sg13cmos5l_dfrbpq_1'
PREFIX='wp_r1_hold_'


def records(text):
    cells={};terms={};interface=[]
    for line in text.splitlines():
        row=line.split('\t')
        if row[0]=='CELL':
            if row[1] in cells:raise ValueError('Duplicate physical cell')
            cells[row[1]]=row[2:]
        elif row[0]=='ITERM':
            key=tuple(row[1:3])
            if key in terms:raise ValueError('Duplicate physical terminal')
            terms[key]=row[3]
        elif row[0] in ('PORT','PBOX'):interface.append(row)
    return cells,terms,sorted(interface)


def check_branch_identity(before,after,targets):
    old,ot,op=records(before);new,nt,np=records(after)
    if len(set(targets))!=len(targets) or set(targets)!={n for n,c in old.items() if c[0]==FF}:
        raise ValueError('Incomplete or duplicate data-register census')
    additions={PREFIX+n for n in targets}
    if set(new)!=set(old)|additions or set(old)&additions:
        raise ValueError('Unexpected added or removed physical cells')
    if any(new[n]!=c for n,c in old.items()) or op!=np:
        raise ValueError('Original placement/master/interface changed')
    expected=dict(ot)
    for n in targets:
        buf=PREFIX+n;net=buf+'_net'
        if new[buf][0]!=MASTER or net in ot.values():raise ValueError('Wrong buffer or colliding branch net')
        expected[(n,'D')]=net
        # Pin names are checked against the actual cell master in the native script.
        expected.update({(buf,'A'):ot[(n,'D')],(buf,'X'):net,(buf,'VDD'):'VPWR',(buf,'VSS'):'VGND'})
    if nt!=expected:raise ValueError('Data branch, configuration or power connectivity changed')
    return dict(original_cells=len(old),added_data_buffers=len(targets),
                configuration_latches=sum(c[0]=='sg13cmos5l_dlhq_1' for c in old.values()),
                original_placement_and_interface_preserved=True,
                binary_buffer_collapsed_connectivity_equal=True)


def eco_script(odb,out,targets,buffered):
    for p in (odb,out):
        if any(c in str(p) for c in '{}\n\r'):raise ValueError('Unsafe native tool path')
    if any(not re.fullmatch(r'_[0-9]+_',n) for n in targets):raise ValueError('Unsafe native target')
    names=' '.join(targets)
    body=OBSERVER+f'\nread_db {{{odb}}}\ninventory {{{out/"before.txt"}}}\n'
    if buffered:
        body+=f'''
set block [ord::get_db_block]
set master [[ord::get_db] findMaster {MASTER}]
if {{$master eq "NULL"}} {{error "missing buffer master"}}
if {{[llength [$block getRows]]==0}} {{error "source has no placement rows"}}
set anchored [dict create]
foreach inst [$block getInsts] {{
 dict set anchored [$inst getName] [$inst getPlacementStatus]
 $inst setPlacementStatus FIRM
}}
foreach name {{{names}}} {{
 set ff [$block findInst $name]
 if {{$ff eq "NULL" || [[$ff getMaster] getName] ne "{FF}"}} {{error "wrong data register"}}
 set d [$ff findITerm D];set original [$d getNet]
 set name {PREFIX}$name
 if {{[$block findInst $name] ne "NULL" || [$block findNet ${{name}}_net] ne "NULL"}} {{error "ECO already exists"}}
 set buf [odb::dbInst_create $block $master $name]
 set branch [odb::dbNet_create $block ${{name}}_net]
 if {{$buf eq "NULL" || $branch eq "NULL"}} {{error "failed to create native buffer"}}
 [$buf findITerm A] connect $original
 [$buf findITerm X] connect $branch
 foreach pin {{VDD VSS}} rail {{VPWR VGND}} {{
  set term [$buf findITerm $pin];set net [$block findNet $rail]
  if {{$term eq "NULL" || $net eq "NULL"}} {{error "missing buffer supply"}}
  $term connect $net
 }}
 lassign [$ff getOrigin] x y
 $buf setLocation $x $y;$buf setOrient [$ff getOrient];$buf setPlacementStatus PLACED
 $d disconnect;$d connect $branch
}}
set_thread_count 4
detailed_placement
check_placement -verbose
dict for {{name status}} $anchored {{[$block findInst $name] setPlacementStatus $status}}
puts "R1_HOLD_ADDED {len(targets)}"
puts "R1_HOLD_AREA_UM2 [expr {{{len(targets)}*[$master getWidth]*[$master getHeight]/1000000.0}}]"
'''
    body+=f'''
inventory {{{out/'after.txt'}}}
write_db {{{out/'probe.odb'}}}
write_def {{{out/'probe.def'}}}
write_verilog {{{out/'probe.nl.v'}}}
puts "R1_HOLD_ECO_END"
'''
    return body


def prepare(capsule,native,out):
    capsule,native,out=map(lambda p:Path(p).resolve(),(capsule,native,out))
    model=native/'registered_native/all-native.json'
    if sha(model)!=NATIVE_SHA:raise ValueError('Frozen native model changed')
    m=json.loads(model.read_text())['modules']['PRIM2T2S']
    targets=sorted(n for n,c in m['cells'].items() if c['type']==FF)
    if len(targets)!=58 or sum(c['type']=='sg13cmos5l_dlhq_1' for c in m['cells'].values())!=334:
        raise ValueError('Native data/configuration census changed')
    out.mkdir(parents=True,exist_ok=False)
    prepare_control(capsule,'primitive1',out/'authenticated-source')
    source=json.loads((out/'authenticated-source/plan.json').read_text())
    odbs=[Path(p) for p in source['input_sha256'] if p.endswith('.odb')]
    if len(odbs)!=1:raise ValueError('Require one authenticated physical source')
    odb=odbs[0];folder=odb.parent.parent;native_root=folder.parent
    bound=[Path(__file__),Path(__file__).with_name('detailed_leaf.py'),Path(__file__).with_name('detailed_context.py'),
           model,out/'authenticated-source/plan.json',folder/'policy.json',odb.parent/'state_out.json']
    def relocate(value):
        if isinstance(value,dict):return {k:relocate(v) for k,v in value.items()}
        if isinstance(value,list):return [relocate(v) for v in value]
        if isinstance(value,str) and value.startswith('/home/runner/work/'):
            if '/build/r1_balanced_leaf/native/' in value:return str(native_root/value.split('/build/r1_balanced_leaf/native/',1)[1])
            if '/build/r1_balanced_source/input/' in value:return str(capsule/'mapped/input'/value.split('/build/r1_balanced_source/input/',1)[1])
            raise ValueError('Unrecognized frozen physical path')
        return value
    state=relocate(json.loads((odb.parent/'state_out.json').read_text()))
    config=relocate(json.loads((folder/'policy.json').read_text())['config'])
    if (config['CLOCK_PORT'] is not None or config['CLOCK_PERIOD']!=20 or config['GRT_OVERFLOW_ITERS']!=50 or config['GRT_ADJUSTMENT']!=0.3):
        raise ValueError('Physical control policy changed')
    for key,value in state.items():
        if key!='metrics' and isinstance(value,str):bound.append(Path(value))
    for key in ('VERILOG_FILES','IO_PIN_ORDER_CFG'):
        values=config[key] if isinstance(config[key],list) else [config[key]]
        bound.extend(Path(v) for v in values)
    plan=dict(targets=targets,inputs={str(p):sha(p) for p in bound},source_inputs=source['input_sha256'],
              source_odb=str(odb),config=config,state=state,
              scope='Primitive1 native fit/global-route screen only. Original CLOCK_PORT=null retained: no CTS, configured timing, DRC/LVS/antenna, full-chip or adoption acceptance.')
    scripts={}
    for case in ('control','buffered'):
        d=out/case;d.mkdir();p=d/'eco.tcl';p.write_text(eco_script(odb,d,targets,case=='buffered'));scripts[case]=sha(p)
    plan['scripts']=scripts
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')


def inside(out):
    from librelane.flows.classic import Classic
    from librelane.steps import OpenROAD
    from librelane.state import State,DesignFormat
    from cloud_fanout_grt import parse_congestion,require_zero_overflow
    from cloud_tile_harden import metric_json
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    if any(sha(p)!=h for p,h in {**plan['inputs'],**plan['source_inputs']}.items()):raise ValueError('Physical probe source changed')
    class Route(Classic):Steps=[OpenROAD.GlobalRouting]
    result=dict(passed=False,cases={},scope=plan['scope'],timing_acceptance=False,physical_acceptance=False,adopted=False)
    for case in ('control','buffered'):
        row=dict(passed=False);result['cases'][case]=row;d=out/case
        try:
            script=d/'eco.tcl'
            if sha(script)!=plan['scripts'][case]:raise ValueError('Physical probe script changed')
            with (d/'eco.log').open('w') as log:
                subprocess.run(['openroad','-exit',str(script)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
            text=(d/'eco.log').read_text()
            if text.splitlines().count('R1_HOLD_ECO_END')!=1:raise ValueError('Native ECO did not complete')
            before=(d/'before.txt').read_text();after=(d/'after.txt').read_text()
            if case=='control':
                if records(before)!=records(after):raise ValueError('Original control changed')
            else:
                row['branch_identity']=check_branch_identity(before,after,plan['targets'])
                areas=re.findall(r'^R1_HOLD_AREA_UM2 ([0-9.]+)$',text,re.M)
                if len(areas)!=1 or float(areas[0])<=0:raise ValueError('Missing added native cell area')
                row['added_cell_area_um2']=float(areas[0])
            initial=dict(plan['state']);initial['odb']=str(d/'probe.odb')
            initial['def']=str(d/'probe.def');initial['nl']=str(d/'probe.nl.v');initial['pnl']=None
            flow=Route(plan['config'],design_dir=str(out),pdk='ihp-sg13cmos5l',pdk_root=os.environ['PDK_ROOT'])
            final=flow.start(with_initial_state=State.load(initial),_force_run_dir=str(d/'route'))
            metrics=json.loads(json.dumps(final.metrics.to_raw_dict(),default=metric_json));row['metrics']=metrics
            logs=list((d/'route').glob('*-openroad-globalrouting/openroad-globalrouting.log'))
            if len(logs)!=1:raise ValueError('Missing native global route log')
            row['congestion']=parse_congestion(logs[0].read_text());require_zero_overflow(row['congestion'],metrics)
            obs=d/'observe.tcl';obs.write_text(OBSERVER+f'\nread_db {{{final[DesignFormat.ODB]}}}\ninventory {{{d/"routed.txt"}}}\n')
            with (d/'observe.log').open('w') as log:subprocess.run(['openroad','-exit',str(obs)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
            if case=='buffered':check_branch_identity(before,(d/'routed.txt').read_text(),plan['targets'])
            elif records(before)!=records((d/'routed.txt').read_text()):raise ValueError('Route changed original control')
            row.update(passed=True,odb_sha256=sha(str(final[DesignFormat.ODB])))
        except Exception as exc:row['error']=str(exc)
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        if case=='control' and not row['passed']:break
    result['passed']=set(result['cases'])=={'control','buffered'} and all(r['passed'] for r in result['cases'].values())
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    if not result['passed']:raise ValueError('Native primitive buffer fit/routing probe failed; retain evidence')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare')
    for n in ('capsule','native','out'):p.add_argument('--'+n,type=Path,required=True)
    sub.add_parser('inside').add_argument('--out',type=Path,required=True)
    args=vars(parser.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else inside)(**args)
