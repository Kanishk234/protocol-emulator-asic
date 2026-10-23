"""Bounded representative R1 PDN, placement and global-routing screen.

Frozen mapped logic, two predeclared widths, no synthesis or timing acceptance.
"""
import argparse
from decimal import Decimal, ROUND_CEILING
import json
import os
from pathlib import Path
import subprocess
import sys

from physical_preflight import TOP,sha
ROOT=Path(__file__).resolve().parents[2]
BUFFER_SHA='7b9526fcc9676d6f266e457344c6b71921eebea7e2600c3df489de1475c1f2e6'
NL_SHA='b743335546eb7cbecd98d9fd129a26855e900ca4f868caea2f5a43167faf6b1a'
RESERVE_COLUMNS=(154.08,164.64,154.08,154.08,164.64,154.08)


def reserve_geometry():
    # Round native three-decimal reports upward, then include the largest
    # observed reference routability inflation at unchanged 96% density.
    required=(Decimal('26853.447')+Decimal('225.661'))/(Decimal('.96')*Decimal('177.66'))+Decimal('5.76')
    width=(required/Decimal('.48')).to_integral_value(rounding=ROUND_CEILING)*Decimal('.48')
    return dict(width_um=str(width),required_width_um=str(required),
                column_widths=list(RESERVE_COLUMNS),macro_width_um=str(Decimal('137.28')+sum(map(lambda w:Decimal(str(w)),RESERVE_COLUMNS))),
                source_run='40014699181',pin_adjusted_area_upper_um2='26853.447',routing_inflation_upper_um2='225.661')


def power_phase(width,column=0,columns=None):
    width=Decimal(str(width));pitch=Decimal('109.92')
    if columns is not None:
        if tuple(columns)!=RESERVE_COLUMNS or width!=Decimal(str(columns[column])):
            raise ValueError('Only the measured primitive-reserve layout is declared')
        preceding=sum((Decimal(str(w)) for w in columns[:column]),Decimal(0))
    else:preceding=column*width
    center=(Decimal('12')-Decimal('68.64')-preceding)%pitch
    if center<0:center+=pitch
    return dict(center_um=str(center),core_offset_um=str(center-Decimal('2.88')),
                pitch_um=str(pitch),column=column)


def routing_policy(width,column=0,columns=None):
    if width not in (219.84,154.08) and not (width==164.64 and columns==RESERVE_COLUMNS):
        raise ValueError('Undeclared footprint')
    if column not in range(6):raise ValueError('Invalid interior column')
    phase=power_phase(width,column,columns)
    return dict(CLOCK_PERIOD=20,CLOCK_PORT=None,FP_SIZING='absolute',DIE_AREA=[0,0,width,185.22],
                BOTTOM_MARGIN_MULT=1,TOP_MARGIN_MULT=1,LEFT_MARGIN_MULT=6,RIGHT_MARGIN_MULT=6,
                VDD_NETS=['VPWR'],GND_NETS=['VGND'],
                IO_PIN_H_EXTENSION=0,IO_PIN_V_EXTENSION=0,ERRORS_ON_UNMATCHED_IO='both',
                RT_MIN_LAYER='Metal2',RT_MAX_LAYER='Metal4',
                PL_TARGET_DENSITY_PCT=96,PL_TIMING_DRIVEN=False,PL_ROUTABILITY_DRIVEN=True,
                DESIGN_REPAIR_REMOVE_BUFFERS=False,DESIGN_REPAIR_BUFFER_INPUT_PORTS=False,
                DESIGN_REPAIR_BUFFER_OUTPUT_PORTS=True,
                GRT_OVERFLOW_ITERS=50,GRT_ALLOW_CONGESTION=True,GRT_ADJUSTMENT=0.3,
                PDN_VERTICAL_LAYER='Metal4',PDN_HORIZONTAL_LAYER='TopMetal1',PDN_MULTILAYER=False,
                PDN_EXTEND_TO='boundary',PDN_VWIDTH=2.1,PDN_VSPACING=2.0,PDN_VPITCH=109.92,
                PDN_VOFFSET=float(phase['core_offset_um']),
                PDN_HWIDTH=2.0,PDN_HSPACING=4.0,PDN_HPITCH=50.0,PDN_HOFFSET=10.0,
                ROUTING_OBSTRUCTIONS=[[layer,*box] for layer in ('Metal1','Metal2','Metal3','Metal4','TopMetal1')
                    for box in ([0,-1,width,0],[0,185.22,width,186.22],[-1,0,0,185.22],[width,0,width+1,185.22])])


def check_power_boxes(boxes,width,column=0,columns=None):
    primary=Decimal(power_phase(width,column,columns)['center_um'])*1000
    centers={'VPWR':primary,'VGND':primary+4100}
    for net,expected in centers.items():
        found=[box for box in boxes if box['net']==net and box['layer']=='Metal4']
        if not found:raise ValueError('Missing Metal4 power pin: '+net)
        stripes={}
        for box in found:
            x0,y0,x1,y1=box['rect']
            if x1<=x0 or y1<=y0 or y0<0 or y1>185220:
                raise ValueError('Invalid power pin geometry')
            if (Decimal(x0+x1)/2-expected)%Decimal(109920)!=0:
                raise ValueError('Power stripe phase differs from global fabric grid')
            stripes.setdefault((x0,x1),[]).append((y0,y1))
        for spans in stripes.values():
            if (0,185220) not in spans:
                raise ValueError('Power pin does not span tile height')


def inside(bundle,buffers,out,widths=(219.84,154.08),primitive_column=None,primitive_reserve=False):
    from librelane.common import Path as LLPath
    from librelane.flows import SequentialFlow
    from librelane.state import State,DesignFormat
    from librelane.steps import OpenROAD,Odb
    from librelane.steps.openroad import get_psm_error_count
    sys.path.insert(0,str(ROOT/'test_internal'))
    from cloud_fanout_grt import parse_congestion,require_zero_overflow
    from cloud_tile_harden import metric_json
    bundle,buffers,out=(Path(p).resolve() for p in (bundle,buffers,out))
    manifest=json.loads((bundle/'manifest.json').read_text())
    columns=RESERVE_COLUMNS if primitive_reserve else None
    if primitive_reserve and (primitive_column not in (1,4) or widths!=(164.64,)):
        raise ValueError('Reserve screen requires one fixed derived width and an actual primitive column')
    if primitive_column is None:
        design=bundle;top=TOP;latches=438;nl_sha=NL_SHA;column=0;source_preflight='39996455894'
        expected_cells=manifest['expected_cells']
    else:
        if primitive_column not in (1,4):raise ValueError('Only actual primitive columns are declared')
        design=bundle/'PRIM2T2S';top='PRIM2T2S';latches=334;column=primitive_column;source_preflight='40013513454'
        nl_sha='c1e0504142bf07a8b2a4bd15f3d931e8d01ddc09b71e6705083e5e58ba6134b1'
        tile=manifest['tiles'][top]
        if tile['mapped_sha256']!='8dbbb5a187251d323ece80a6abad473f00b2aaac041c9d89907b8519d6137f24':
            raise ValueError('Changed primitive mapping provenance')
        expected_cells=tile['expected_cells']
    if sha(design/'tile.nl.v')!=nl_sha or sha(buffers)!=BUFFER_SHA:
        raise ValueError('Changed frozen netlist or pinned buffer adapter')
    if any(sha(bundle/name)!=digest for name,digest in manifest['files'].items()):
        raise ValueError('Prepared native inputs changed')
    class TileIO(Odb.CustomIOPlacement):
        id='Odb.R1PhysicalPins'
        def get_script_path(self):return str(bundle/'io_place.py')
    class OutputBuffers(OpenROAD.RepairDesignPostGPL):
        id='OpenROAD.R1OutputBuffers'
        def get_script_path(self):return str(buffers)
    class Route(SequentialFlow):
        Steps=[OpenROAD.Floorplan,Odb.SetPowerConnections,TileIO,
               OpenROAD.TapEndcapInsertion,OpenROAD.GeneratePDN,Odb.AddRoutingObstructions,
               OutputBuffers,Odb.SetPowerConnections,OpenROAD.GlobalPlacement,
               OpenROAD.DetailedPlacement,OpenROAD.GlobalRouting]
    out.mkdir(parents=True,exist_ok=False)
    observer=out/'observe.tcl'
    observer.write_text('''read_db $::env(R1_ODB)
set block [ord::get_db_block]
set counts [dict create]
set area 0
set power_terminals 0
foreach inst [$block getInsts] {
  set master [$inst getMaster]
  dict incr counts [$master getName]
  set area [expr {$area+[$master getWidth]*[$master getHeight]}]
  foreach pin [$inst getITerms] {
    set kind [[$pin getMTerm] getSigType]
    if {$kind ni {POWER GROUND}} {continue}
    set expected [expr {$kind eq "POWER" ? "VPWR" : "VGND"}]
    set net [$pin getNet]
    if {[catch {$net getName} actual] || $actual ne $expected} {
      error "Unconnected or wrong power terminal on [$inst getName]"
    }
    incr power_terminals
  }
}
puts "R1_CELLS\t$counts"
puts "R1_AREA\t$area"
puts "R1_POWER_TERMINALS\t$power_terminals"
foreach net {VPWR VGND} {
  set report $::env(R1_REPORT_DIR)/$net-final-grid-errors.rpt
  set stream [open $report w]; puts $stream ""; close $stream
  check_power_grid -net $net -error_file $report
}
foreach term [$block getBTerms] {
  if {[$term getName] ni {VPWR VGND}} {continue}
  foreach pin [$term getBPins] {
    foreach box [$pin getBoxes] {
      puts "R1_PG\t[$term getName]\t[[$box getTechLayer] getName]\t[$box xMin]\t[$box yMin]\t[$box xMax]\t[$box yMax]"
    }
  }
}
''')
    result=dict(passed=False,cases={},source_preflight=source_preflight,mapped_nl_sha256=nl_sha,tile=top,column=column,
                reserve_geometry=reserve_geometry() if primitive_reserve else None,
                input_manifest_sha256=sha(bundle/'manifest.json'),buffer_adapter_sha256=BUFFER_SHA,
                openroad_version=subprocess.check_output(['openroad','-version'],text=True).strip(),
                synthesis_executed=False,detailed_routing=False,physical_acceptance=False,timing_acceptance=False,
                scope='Representative tile/declared-column PDN/placement/global routing only. Null clock port; no configured timing, signoff or whole-chip acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    for width in widths:
        name='width'+str(width).replace('.','_');folder=out/name;folder.mkdir()
        row=dict(passed=False,policy=routing_policy(width,column,columns),power_phase=power_phase(width,column,columns))
        result['cases'][name]=row
        (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        config=dict(row['policy'],DESIGN_NAME=top,VERILOG_FILES=[str(design/'tile.nl.v')],
                    IO_PIN_ORDER_CFG=str(design/'pins.yaml'))
        try:
            flow=Route(config,design_dir=str(bundle),pdk='ihp-sg13cmos5l',pdk_root=os.environ['PDK_ROOT'])
            (folder/'policy.json').write_text(json.dumps(dict(config=config,steps=[s.id for s in flow.Steps]),indent=2)+'\n')
            state=flow.start(with_initial_state=State({DesignFormat.NETLIST:LLPath(str(design/'tile.nl.v')),
                       DesignFormat.JSON_HEADER:LLPath(str(design/'header.json'))}),_force_run_dir=str(folder))
            metrics=state.metrics.to_raw_dict();row['metrics']=metrics
            logs=list(folder.glob('*-openroad-globalrouting/openroad-globalrouting.log'))
            if len(logs)!=1:raise ValueError('Missing/ambiguous native global-route log')
            row['congestion']=parse_congestion(logs[0].read_text())
            row['overflow_metrics']=require_zero_overflow(row['congestion'],metrics)
            if metrics.get('design__power_grid_violation__count')!=0:
                raise ValueError('Power grid completeness not established')
            odb=Path(str(state[DesignFormat.ODB]));row['odb_sha256']=sha(odb)
            log=folder/'native-census.log'
            with log.open('w') as stream:
                subprocess.run(['openroad','-exit',str(observer)],
                               env=dict(os.environ,R1_ODB=str(odb),R1_REPORT_DIR=str(folder)),
                               stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=120)
            text=log.read_text();counts=next(l for l in text.splitlines() if l.startswith('R1_CELLS\t')).split('\t')[1].split()
            row['power_terminals_checked']=int(next(l for l in text.splitlines() if l.startswith('R1_POWER_TERMINALS\t')).split('\t')[1])
            if row['power_terminals_checked']<=0:raise ValueError('No native cell power terminals checked')
            row['final_power_grid_violations']={}
            for net in ('VPWR','VGND'):
                with (folder/(net+'-final-grid-errors.rpt')).open() as report:
                    row['final_power_grid_violations'][net]=get_psm_error_count(report)
            if any(row['final_power_grid_violations'].values()):
                raise ValueError('Final placed design power-grid check failed')
            row['native_cells']=dict(zip(counts[::2],map(int,counts[1::2])))
            if row['native_cells'].get('sg13cmos5l_dlhq_1')!=latches:
                raise ValueError('Configuration storage changed during physical flow')
            for master,count in expected_cells.items():
                if master=='$scopeinfo' or master.startswith('sg13cmos5l_buf_'):continue
                if row['native_cells'].get(master,0)!=count:
                    raise ValueError('Original mapped cell count changed: '+master)
            row['cell_area_dbu2']=int(next(l for l in text.splitlines() if l.startswith('R1_AREA\t')).split('\t')[1])
            pg=[]
            for line in text.splitlines():
                if line.startswith('R1_PG\t'):
                    _,net,layer,*coords=line.split('\t');pg.append(dict(net=net,layer=layer,rect=list(map(int,coords))))
            row['power_pins']=pg;check_power_boxes(pg,width,column,columns)
            row['passed']=True
        except Exception as exc:
            row['error']=str(exc)
            states=sorted(folder.glob('*/state_out.json'),key=lambda p:int(p.parent.name.split('-')[0]))
            if states:
                row['last_completed_state']=str(states[-1].relative_to(out))
        (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True,default=metric_json)+'\n')
    result.update(passed=all(row['passed'] for row in result['cases'].values()),
                  run=os.environ.get('GITHUB_RUN_ID'),attempt=os.environ.get('GITHUB_RUN_ATTEMPT'))
    (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True,default=metric_json)+'\n')
    if not result['passed']:raise RuntimeError('Representative routing gates failed; both outcomes retained')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('bundle','buffers','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--width',type=float,choices=(219.84,154.08))
    p.add_argument('--primitive-column',type=int,choices=(1,4))
    p.add_argument('--primitive-reserve',action='store_true')
    a=p.parse_args()
    if a.primitive_reserve and (a.width is not None or a.primitive_column is None):p.error('Reserve mode uses its one derived width and requires the actual primitive column')
    inside(a.bundle,a.buffers,a.out,(164.64,) if a.primitive_reserve else ((a.width,) if a.width else (219.84,154.08)),a.primitive_column,a.primitive_reserve)
