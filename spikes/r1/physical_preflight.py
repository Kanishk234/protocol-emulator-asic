"""Exact R1 LUT-netlist floorplan/pin screen. No placement, route or timing proof."""
import argparse
from collections import Counter
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
TOP='LUT4x8_ha'
MAPPED_SHA='65ad88d47ac9186eb9210280d8d0ae8e3a80916a89f8b669ccf01683075c6c75'
IO_SHA='4517d4d40cfbadd7dfadc3d7415cd9ade794f3bbaefb21a5ce7bec9db4eefb32'
IMAGE='ghcr.io/librelane/librelane@sha256:d109140b8f17fc54f4fca998beb8124f4949404ec52e339eebd2250854a18b5a'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def signal_names(ports):
    result=set()
    for name,port in ports.items():
        if len(port['bits'])==1:result.add(name)
        else:result.update(f'{name}[{i}]' for i in range(port.get('offset',0),port.get('offset',0)+len(port['bits'])))
    return result


def physical_pin_order(generated,expected,disabled_user_clk):
    if set(generated)!={'X0Y0'}:
        raise ValueError('Expected one ordinary tile in pin-order output')
    sides={'NORTH':'N','EAST':'E','SOUTH':'S','WEST':'W'}
    legacy={};removed=[]
    for side,groups in generated['X0Y0'].items():
        legacy[sides[side]]=[]
        for group in groups:
            pins=[]
            for pattern in group['pins']:
                if disabled_user_clk and pattern in ('UserCLK','UserCLKo'):
                    if pattern in expected:raise ValueError('Disabled user clock exists in mapped ports')
                    removed.append(pattern)
                else:pins.append(pattern)
            if pins:
                legacy[sides[side]].append({**{k:v for k,v in group.items() if k not in ('max_distance','pins')},'pins':pins})
    patterns=[p for groups in legacy.values() for group in groups for p in group['pins']]
    if any(not any(re.fullmatch(pattern,name) for name in expected) for pattern in patterns):
        raise ValueError('Pin-order pattern names an absent port')
    if any(sum(bool(re.fullmatch(pattern,name)) for pattern in patterns)!=1 for name in expected):
        raise ValueError('Mapped port missing or multiply matched in pin policy')
    return legacy,sorted(removed)


def check_pins(inventory,expected):
    if set(inventory['pins'])!=set(expected):
        raise ValueError('Native signal-port inventory differs')
    x0,y0,x1,y1=inventory['die'];boxes=[]
    for name,port in inventory['pins'].items():
        if not port['boxes']:
            raise ValueError('Signal has no pin geometry')
        for layer,a,b,c,d in port['boxes']:
            if not (x0<=a<c<=x1 and y0<=b<d<=y1):
                raise ValueError('Signal rectangle outside die or degenerate: '+name)
            for other,other_layer,e,f,g,h in boxes:
                if name!=other and layer==other_layer and max(a,e)<min(c,g) and max(b,f)<min(d,h):
                    raise ValueError('Overlapping signal pin rectangles')
            boxes.append((name,layer,a,b,c,d))


def prepare(evidence,io,out):
    import yaml
    from fabulous.fabulous_api import FABulous_API
    from fabulous.fabric_generator.code_generator.code_generator_Verilog import VerilogCodeGenerator
    evidence,io,out=(Path(p).resolve() for p in (evidence,io,out))
    model=evidence/'resource';mapped=evidence/'mapped-cost'/TOP/'mapped.json'
    if sha(mapped)!=MAPPED_SHA or sha(io)!=IO_SHA:
        raise ValueError('Unqualified mapped netlist or I/O adapter')
    record=json.loads((model/'resource-control.json').read_text())
    if record['radix']!='radix8_2' or record['physical_candidate'] is not False:
        raise ValueError('Require frozen third-profile model')
    def check_model():
        if any(sha(model/name)!=digest for name,digest in record['generated_sha256'].items()):
            raise ValueError('Model differs from its manifest')
    check_model()
    out.mkdir(parents=True,exist_ok=False)
    graph=json.loads(mapped.read_text());module=graph['modules'][TOP]
    counts=Counter(c['type'] for c in module['cells'].values())
    if counts['sg13cmos5l_dlhq_1']!=438 or sum(len(p['bits']) for p in module['ports'].values())!=210:
        raise ValueError('Frozen mapped cell/port census changed')
    connectivity=json.dumps([module['cells'],module['ports']],sort_keys=True)
    # Keep scalar carry pin spelling consistent with FABulous's pin-order API.
    # This changes only Verilog print metadata, never cells or connectivity.
    for net in module['netnames'].values():
        if len(net['bits'])==1:
            net.get('attributes',{}).pop('single_bit_vector',None)
    if json.dumps([module['cells'],module['ports']],sort_keys=True)!=connectivity:
        raise ValueError('Print normalization changed the mapped graph')
    normalized=out/'mapped-normalized.json'
    normalized.write_text(json.dumps(graph)+'\n')
    netlist=out/'tile.nl.v'
    script=out/'export.ys'
    script.write_text('read_json '+json.dumps(str(normalized))+'\nselect -clear\nselect '+TOP+
                      '\nwrite_verilog -selected -noattr -noexpr '+json.dumps(str(netlist))+'\n')
    with (out/'export.log').open('w') as log:
        subprocess.run(['yosys','-Q','-T','-s',str(script)],check=True,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    header=dict(module)
    header['cells']={name:cell for name,cell in module['cells'].items() if cell['type']!='$scopeinfo'}
    (out/'header.json').write_text(json.dumps(dict(modules={TOP:header}))+'\n')
    old_root=str(Path(yaml.safe_load((model/'arch.yaml').read_text())['macro']).parent)
    shutil.copytree(model/'library',out/'library')
    csv=out/'localized.csv'
    csv.write_text((model/'r1_resource_control.csv').read_text().replace(old_root,str(out)))
    api=FABulous_API(VerilogCodeGenerator());api.loadFabric(csv)
    api.gen_io_pin_order_config(api.getTile(TOP),out/'pins-generated.yaml')
    generated=yaml.safe_load((out/'pins-generated.yaml').read_text())
    legacy,removed=physical_pin_order(generated,signal_names(module['ports']),api.fabric.disableUserCLK)
    (out/'pins.yaml').write_text(yaml.safe_dump(legacy,sort_keys=False))
    check_model()
    shutil.copyfile(io,out/'io_place.py')
    (out/'ATTRIBUTION.md').write_text('I/O placement: pinned librelane_plugin_fabulous dcc038217472822330b33f61fadbc06e0c3cc96d, Apache-2.0; original header retained. WARP generated design: project Apache-2.0. PDK fetched separately at2bbec755dc67ca3db0261c3d6163e15735d66710.\n')
    manifest=dict(source_run='39696703659',source_revision='9768c77325ca34b93d408f526c0d8c902b62ce4a',
                  mapped_sha256=MAPPED_SHA,files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
                  removed_disabled_user_clock_ports=removed,
                  expected_cells=dict(counts),expected_ports=module['ports'],
                  widths=[219.84,154.08],height=185.22,physical_acceptance=False,timing_acceptance=False)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')


def inside(bundle,out):
    from librelane.common import Path as LLPath
    from librelane.flows import SequentialFlow
    from librelane.state import State,DesignFormat
    from librelane.steps import OpenROAD,Odb
    sys.path.insert(0,str(ROOT/'test_internal'))
    from cloud_tile_preflight import PIN_OBSERVER,parse_pin_inventory
    bundle,out=Path(bundle).resolve(),Path(out).resolve()
    m=json.loads((bundle/'manifest.json').read_text())
    if any(sha(bundle/name)!=digest for name,digest in m['files'].items()):
        raise ValueError('Changed prepared physical inputs')
    class TileIO(Odb.CustomIOPlacement):
        id='Odb.R1PhysicalPins'
        def get_script_path(self):return str(bundle/'io_place.py')
    class Preflight(SequentialFlow):
        Steps=[OpenROAD.Floorplan,Odb.SetPowerConnections,TileIO]
    out.mkdir(parents=True,exist_ok=False)
    observer=out/'observe.tcl'
    observer.write_text(PIN_OBSERVER.replace('[join [lsort $boxes] ;]','[join [lsort $boxes] {;}]')+'''
set counts [dict create]
foreach inst [$block getInsts] {
  dict incr counts [[$inst getMaster] getName]
}
puts "R1_CELLS\t$counts"
set core [$block getCoreArea]
puts "R1_CORE\t[$core xMin]\t[$core yMin]\t[$core xMax]\t[$core yMax]"
set cell_area 0
foreach inst [$block getInsts] {
  set master [$inst getMaster]
  set cell_area [expr {$cell_area + [$master getWidth]*[$master getHeight]}]
}
puts "R1_CELL_AREA\t$cell_area"
''')
    expected=signal_names(m['expected_ports'])
    result=dict(passed=False,stages={},source_run=m['source_run'],
                input_manifest_sha256=sha(bundle/'manifest.json'),
                synthesis_executed=False,physical_acceptance=False,timing_acceptance=False,
                scope='Exact mapped netlist import, floorplan and 210signal pin geometry only; no placement/PDN/routing/timing or whole-chip acceptance.')
    try:
        for width in m['widths']:
            name='width'+str(width).replace('.','_');run=out/name;run.mkdir()
            result['active_stage']=name
            config=dict(DESIGN_NAME=TOP,VERILOG_FILES=[str(bundle/'tile.nl.v')],
                        CLOCK_PERIOD=20,CLOCK_PORT=None,FP_SIZING='absolute',DIE_AREA=[0,0,width,m['height']],
                        BOTTOM_MARGIN_MULT=1,TOP_MARGIN_MULT=1,LEFT_MARGIN_MULT=6,RIGHT_MARGIN_MULT=6,
                        VDD_NETS=['VPWR'],GND_NETS=['VGND'],
                        IO_PIN_ORDER_CFG=str(bundle/'pins.yaml'),ERRORS_ON_UNMATCHED_IO='both',
                        RT_MIN_LAYER='Metal2',RT_MAX_LAYER='Metal4',
                        IO_PIN_H_EXTENSION=0,IO_PIN_V_EXTENSION=0)
            flow=Preflight(config,design_dir=str(bundle),pdk='ihp-sg13cmos5l',pdk_root=os.environ['PDK_ROOT'])
            state=flow.start(with_initial_state=State({DesignFormat.NETLIST:LLPath(str(bundle/'tile.nl.v')),
                       DesignFormat.JSON_HEADER:LLPath(str(bundle/'header.json'))}),_force_run_dir=str(run))
            odb=Path(str(state[DesignFormat.ODB]));log=out/(name+'.log')
            with log.open('w') as stream:
                subprocess.run(['openroad','-exit',str(observer)],stdout=stream,stderr=subprocess.STDOUT,
                               env=dict(os.environ,WARP_TILE_PIN_INPUT=str(odb)),check=True,timeout=120)
            text=log.read_text();pins=parse_pin_inventory(text)
            check_pins(pins,expected)
            counts_line=next(line for line in text.splitlines() if line.startswith('R1_CELLS\t')).split('\t',1)[1].split()
            counts=dict(zip(counts_line[::2],map(int,counts_line[1::2])))
            if counts.get('sg13cmos5l_dlhq_1')!=438:raise ValueError('Native configuration storage changed')
            original={name:count for name,count in m['expected_cells'].items() if name!='$scopeinfo'}
            if counts!=original:raise ValueError('Native mapped cell census changed during import')
            core=list(map(int,next(l for l in text.splitlines() if l.startswith('R1_CORE\t')).split('\t')[1:]))
            cell_area=int(next(l for l in text.splitlines() if l.startswith('R1_CELL_AREA\t')).split('\t')[1])
            core_area=(core[2]-core[0])*(core[3]-core[1])
            if core_area<=0 or cell_area>core_area:
                raise ValueError('Native cell area exceeds placeable core')
            (out/(name+'-pins.json')).write_text(json.dumps(pins,indent=2)+'\n')
            result['stages'][name]=dict(width=width,signal_pins=len(pins['pins']),configuration_latches=438,
                                       odb_sha256=sha(odb),cells=counts,core_record=[l for l in text.splitlines() if l.startswith('R1_CORE')])
            result['stages'][name].update(core_area_dbu2=core_area,cell_area_dbu2=cell_area)
        result['passed']=True
    except Exception as exc:
        result['error']=str(exc)
        raise
    finally:
        result.update(run=os.environ.get('GITHUB_RUN_ID'),attempt=os.environ.get('GITHUB_RUN_ATTEMPT'))
        (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('prepare','inside'))
    p.add_argument('--evidence',type=Path);p.add_argument('--io',type=Path);p.add_argument('--bundle',type=Path)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.mode=='prepare':prepare(a.evidence,a.io,a.out)
    else:inside(a.bundle,a.out)
