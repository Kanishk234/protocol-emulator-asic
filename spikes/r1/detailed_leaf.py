"""One frozen primitive-leaf detailed-route diagnostic; no layout/timing sweep."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ODB_SHA='28dd8ebc4df4309e4a94999d95e0c4a49872195e3d8e4e900f5b490d4f33e7f3'
GUIDE_SHA='661fa61cd761a8215c6aa0019f83227df4a34e38d07a72d130e821ae71bd00ca'
SOURCE_SHA='00216eac8dcd14c03503afd17d303118a4d3440f'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


OBSERVER=r'''
proc inventory {filename} {
 set b [ord::get_db_block];set f [open $filename w];set pg 0
 foreach inst [$b getInsts] {
  set master [$inst getMaster];set box [$inst getBBox]
  puts $f [join [list CELL [$inst getName] [$master getName] [$box xMin] [$box yMin] [$box xMax] [$box yMax] [$inst getOrient] [$inst getPlacementStatus]] "	"]
  foreach term [$inst getITerms] {
   set mt [$term getMTerm];set net [$term getNet];set name NC
   catch {set name [$net getName]}
   puts $f [join [list ITERM [$inst getName] [$mt getName] $name] "	"]
   set type [$mt getSigType]
   if {$type in {POWER GROUND}} {
    set expected [expr {$type eq "POWER" ? "VPWR" : "VGND"}]
    if {$name ne $expected} {error "wrong or missing cell power connection"}
    incr pg
   }
  }
 }
 foreach term [$b getBTerms] {
  puts $f [join [list PORT [$term getName] [[$term getNet] getName] [$term getIoType] [$term getSigType]] "	"]
  foreach pin [$term getBPins] {foreach box [$pin getBoxes] {
   puts $f [join [list PBOX [$term getName] [[$box getTechLayer] getName] [$box xMin] [$box yMin] [$box xMax] [$box yMax]] "	"]
  }}
 }
 puts $f "PGTERMS	$pg"
 foreach net [$b getNets] {
  if {[$net getSigType] in {POWER GROUND}} {continue}
  if {[expr {[llength [$net getITerms]]+[llength [$net getBTerms]]}]<2} {continue}
  set wire [$net getWire];set wired 0
  if {$wire ne "NULL" && $wire ne ""} {
   if {[$wire getNet] ne $net} {error "route wire belongs to another net"}
   if {[$wire count]>0} {set wired 1}
  }
  puts $f "REQUIRED_NET	[$net getName]	$wired"
 }
 close $f
}
'''

def prepare(source,identity,out):
    source,identity,out=(Path(p).resolve() for p in (source,identity,out))
    producer=json.loads(identity.read_text());record=source/'result.json';data=json.loads(record.read_text())
    if (producer['id']!=40030916359 or producer['head_sha']!=SOURCE_SHA or producer['run_attempt']!=1 or
        producer['conclusion']!='success' or not data['passed'] or data['run']!='40030916359' or data['attempt']!='1' or
        data['balanced_case']['name']!='primitive1' or data['tile']!='PRIM2T2S'):
        raise ValueError('Require the authenticated primitive1 checkpoint')
    row=data['cases']['width164_64'];stage=source/'width164_64/11-openroad-globalrouting'
    odb=stage/'PRIM2T2S.odb';guide=stage/'after_grt.guide'
    if (not row['passed'] or row['odb_sha256']!=ODB_SHA or sha(odb)!=ODB_SHA or sha(guide)!=GUIDE_SHA or
        row['native_cells']['sg13cmos5l_dlhq_1']!=334 or sum(row['native_cells'].values())!=1453 or
        row['power_terminals_checked']!=2906 or row['power_phase']['center_um']!='30.24' or
        any(row['final_power_grid_violations'].values()) or
        any(c['total_overflow'] or c['max_h_overflow'] or c['max_v_overflow'] for c in row['congestion'])):
        raise ValueError('Frozen global-route gates or input identity differ')
    if any(c in str(out)+str(odb)+str(guide) for c in '{}\n\r'):raise ValueError('Unsafe tool path')
    out.mkdir(parents=True,exist_ok=False)
    tcl=OBSERVER+f'''
read_db {{{odb}}}
read_guides {{{guide}}}
inventory {{{out/'source.txt'}}}
set_thread_count 4
set_routing_layers -signal Metal2-Metal4
detailed_route -droute_end_iter 32 -drc_report_iter_step 1 -output_drc {{{out/'drc.rpt'}}} -output_maze {{{out/'maze.log'}}} -output_guide_coverage {{{out/'guide_coverage.rpt'}}}
puts "R1_DRT_VIOLATIONS [drt::detailed_route_num_drvs]"
inventory {{{out/'routed.txt'}}}
write_db {{{out/'PRIM2T2S.odb'}}}
write_def {{{out/'PRIM2T2S.def'}}}
puts "R1_DRT_END"
'''
    (out/'route.tcl').write_text(tcl)
    plan=dict(input_sha256={str(p):sha(p) for p in (Path(__file__),identity,record,odb,guide)},script_sha256=sha(out/'route.tcl'),
              source_run=40030916359,case='primitive1',droute_end_iter=32,threads=4,signal_layers='Metal2-Metal4',
              scope='One frozen leaf only; no placement/netlist change, synthesis, CTS or policy sweep. Router DRC/wire coverage are necessary diagnostics, not foundry signoff, LVS, extracted timing or assembled macro acceptance.')
    (out/'plan.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')


def check_inventories(before,after):
    prefixes=('CELL\t','ITERM\t','PORT\t','PBOX\t','PGTERMS\t')
    frozen=lambda text:sorted(line for line in text.splitlines() if line.startswith(prefixes))
    if frozen(before)!=frozen(after):raise ValueError('Detailed router changed cells, placement, pins or connectivity')
    cells=[line for line in after.splitlines() if line.startswith('CELL\t')]
    if len(cells)!=1453 or sum('\tsg13cmos5l_dlhq_1\t' in line for line in cells)!=334 or 'PGTERMS\t2906' not in after.splitlines():
        raise ValueError('Detailed-route resource/power census differs')
    required=[line.split('\t') for line in after.splitlines() if line.startswith('REQUIRED_NET\t')]
    original=[line.split('\t') for line in before.splitlines() if line.startswith('REQUIRED_NET\t')]
    if not original or any(len(row)!=3 or row[2]!='0' for row in original):
        raise ValueError('Frozen unrouted control incorrectly reports route wires')
    if not required or any(len(row)!=3 or row[2]!='1' for row in required):raise ValueError('Required signal net lacks a route wire')
    if len({row[1] for row in required})!=len(required):raise ValueError('Duplicate routed-net census')
    if {row[1] for row in required}!={row[1] for row in original}:raise ValueError('Required route-net population changed')
    return dict(cells=1453,configuration_latches=334,power_terminals=2906,required_signal_nets_with_wires=len(required))


def audit(out):
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    result=dict(passed=False,run=os.environ.get('GITHUB_RUN_ID'),attempt=os.environ.get('GITHUB_RUN_ATTEMPT'),
                source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),scope=plan['scope'],
                physical_acceptance=False,timing_acceptance=False)
    try:
        exit_file=out/'exit-code.txt'
        if exit_file.exists():result['tool_exit_code']=int(exit_file.read_text().strip())
        for path,digest in plan['input_sha256'].items():
            if sha(path)!=digest:raise ValueError('Detailed-route input changed')
        if sha(out/'route.tcl')!=plan['script_sha256']:raise ValueError('Detailed-route policy changed')
        text=(out/'route.log').read_text();matches=re.findall(r'^R1_DRT_VIOLATIONS (\d+)$',text,re.M)
        if not re.search(r'^R1_DRT_END$',text,re.M) or len(matches)!=1:raise ValueError('Detailed route did not complete')
        result['router_violations']=int(matches[0])
        result.update(check_inventories((out/'source.txt').read_text(),(out/'routed.txt').read_text()))
        result['routed_odb_sha256']=sha(out/'PRIM2T2S.odb')
        result['passed']=result['router_violations']==0
        if not result['passed']:result.update(failure_kind='router_drc',error='Detailed-route violations remain')
    except Exception as exc:
        kind='wall_timeout' if result.get('tool_exit_code')==124 else 'incomplete_or_invariant_failure'
        result.update(failure_kind=kind,error=str(exc))
    (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    if not result['passed']:raise ValueError(result['error'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare')
    for name in ('source','identity','out'):p.add_argument('--'+name,type=Path,required=True)
    sub.add_parser('audit').add_argument('--out',type=Path,required=True)
    args=vars(parser.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else audit)(**args)
