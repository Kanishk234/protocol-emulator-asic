"""Frozen all-tile pin/core and actual assembled-neighbor geometry screen.

No synthesis, placement, routing, timing or whole-fabric physical acceptance.
"""
import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from physical_preflight import sha, IO_SHA, physical_pin_order, signal_names, check_pins

ROOT=Path(__file__).resolve().parents[2]
MAPPED={
'E_IO4':'5004aa345f81b7f127b84976cf6c69a558e674c35c462ee942b7be9295f6c5f4',
'LUT4x8_ha':'65ad88d47ac9186eb9210280d8d0ae8e3a80916a89f8b669ccf01683075c6c75',
'NE_term':'cef9312d952e984d539f41701b6662433ec3e4d5014fc33758824884143ccc9a',
'NW_term':'130dd572f42686021d177007559e9455523a9eba3c54a65de7de8476f4a67d58',
'N_IO':'7f7aede396fe72b436957905998c65a3fab0219f0b9fb6176e3feed893d1ad3f',
'PRIM2T2S':'8dbbb5a187251d323ece80a6abad473f00b2aaac041c9d89907b8519d6137f24',
'SE_term':'4fddedc2ef41209a1be411a830c9da0493b0c404544059f678b7a62f86f97c87',
'SW_term':'86be7391e410692af0aeb309fa2b0008d968ea99d54d9238d8df11a4ffbcc625',
'S_IO2':'0e3d308328ab4f40a41394fbf47277c6e3fe94383599a4fe48ead12793972566',
'W_IO4':'c5460edda74be71e891787af84ef29a2def60401b5f2b791af420e7a857bc4bc'}
WIDTHS=(219.84,154.08)


def footprint(tile,width):
    if tile not in MAPPED or width not in WIDTHS:raise ValueError('Undeclared footprint')
    border=tile[0] in 'EW' or tile[:2] in ('NE','NW','SE','SW')
    short=tile[0] in 'NS'
    return (68.64 if border else width,56.70 if short else 185.22)


def import_counts(actual,original):
    # Native import may materialize at most one driver for each literal net.
    clean=dict(actual)
    extra={}
    for master in ('sg13cmos5l_tiehi','sg13cmos5l_tielo'):
        n=clean.get(master,0)-original.get(master,0)
        if n not in (0,1):raise ValueError('Unexpected native literal driver count')
        if n:
            extra[master]=n
            clean[master]-=n
            if not clean[master]:del clean[master]
    if clean!=original:raise ValueError('Native cell inventory changed')
    return extra


def direct_port_aliases(text,ports):
    """Flatten output-to-output port aliases to the original input bit.

    This changes only Verilog spelling. Every replacement is checked against
    the frozen graph's identical port bit IDs; no cells or nets are inserted.
    """
    bits={}
    for name,port in ports.items():
        for i,bit in enumerate(port['bits']):
            bits[name if len(port['bits'])==1 else f'{name}[{i+port.get("offset",0)}]']=(bit,port['direction'])
    pattern=re.compile(r'^(\s*assign\s+)(\w+(?:\[\d+\])?)(\s*=\s*)(\w+(?:\[\d+\])?)(\s*;)$',re.M)
    aliases={}
    for match in pattern.finditer(text):
        if match[2] in bits and match[4] in bits:
            if bits[match[2]][0]!=bits[match[4]][0]:raise ValueError('Port alias differs from frozen graph')
            aliases[match[2]]=match[4]
    changed=[]
    def replace(match):
        lhs,rhs=match[2],match[4]
        if lhs not in aliases:return match[0]
        seen={lhs};root=rhs
        while root in aliases:
            if root in seen:raise ValueError('Cyclic top-level port aliases')
            seen.add(root);root=aliases[root]
        if root==rhs:return match[0]
        if bits[lhs][0]!=bits[root][0] or bits[lhs][1]!='output' or bits[root][1]!='input':
            raise ValueError('Alias rewrite is not an identical input/output port bit')
        changed.append(dict(output=lhs,old_source=rhs,input=root))
        return match[1]+lhs+match[3]+root+match[5]
    text=pattern.sub(replace,text)
    seen={}
    def deduplicate(match):
        lhs,rhs=match[2],match[4]
        if lhs not in aliases:return match[0]
        if lhs in seen:
            if seen[lhs]!=rhs:raise ValueError('Conflicting top-level port alias drivers')
            changed.append(dict(output=lhs,input=rhs,removed_duplicate=True))
            return ''
        seen[lhs]=rhs
        return match[0]
    return pattern.sub(deduplicate,text),changed


def align_pin_orders(design,orders,port_names):
    """Derive common slot order for each facing-side family from actual nets."""
    parents={};families={}
    def find(table,a):
        table.setdefault(a,a)
        if table[a]!=a:table[a]=find(table,table[a])
        return table[a]
    def union(table,a,b):
        a,b=find(table,a),find(table,b)
        table[max(a,b)]=min(a,b)
    slots={};side_of={}
    for tile,order in orders.items():
        for side,groups in order.items():
            if not groups:continue
            if len(groups)!=1 or groups[0].get('reverse_result') or groups[0]['sort_mode']!='bus_major':
                raise ValueError('Unsupported pin side policy')
            names=[]
            for pattern in groups[0]['pins']:
                names+=sorted((n for n in port_names[tile] if re.fullmatch(pattern,n)),
                              key=lambda n:(n.split('[')[0],int(n.split('[')[1][:-1]) if '[' in n else -1))
            slots[tile,side]=names
            for name in names:side_of[tile,name]=side
    nets=defaultdict(list)
    for cell in design['cells'].values():
        for port,bits in cell['connections'].items():
            for i,bit in enumerate(bits):
                if isinstance(bit,int):nets[bit].append((cell['type'],port if len(bits)==1 else f'{port}[{i}]'))
    for ends in nets.values():
        if len(ends)<2:continue
        if len(ends)!=2:raise ValueError('Unexpected shared macro-interface net')
        a,b=ends;sa,sb=(a[0],side_of[a]),(b[0],side_of[b])
        if {sa[1],sb[1]} not in ({'N','S'},{'E','W'}):raise ValueError('Neighbor ports are not on opposite sides')
        union(parents,a,b);union(families,sa,sb)
    groups=defaultdict(list)
    for side in families:groups[find(families,side)].append(side)
    report=[]
    for sides in groups.values():
        # Preserve the proven LUT interface wherever it belongs to a family.
        anchor=min(sides,key=lambda s:(s[0]!='LUT4x8_ha',{'N':0,'E':1,'S':2,'W':3}[s[1]],s[0]))
        classes=[find(parents,(anchor[0],n)) for n in slots[anchor]]
        if len(set(classes))!=len(classes):raise ValueError('Aliased slots within one physical side')
        for tile,side in sides:
            by_class={find(parents,(tile,n)):n for n in slots[tile,side]}
            if set(by_class)!=set(classes) or len(by_class)!=len(slots[tile,side]):
                raise ValueError('Facing sides do not expose the same track classes')
            orders[tile][side][0]['pins']=[re.escape(by_class[c]) for c in classes]
        report.append(dict(anchor=list(anchor),slots=len(classes),sides=[list(s) for s in sorted(sides)]))
    return report


def prepare(evidence,io,out):
    import yaml
    from fabulous.fabulous_api import FABulous_API
    from fabulous.fabric_definition.define import Side
    from fabulous.fabric_generator.code_generator.code_generator_Verilog import VerilogCodeGenerator
    evidence,io,out=(Path(p).resolve() for p in (evidence,io,out))
    if sha(io)!=IO_SHA:raise ValueError('I/O adapter differs from pinned source')
    model=evidence/'resource';record=json.loads((model/'resource-control.json').read_text())
    if record['radix']!='radix8_2' or record['physical_candidate'] is not False:raise ValueError('Wrong model')
    def guard():
        if any(sha(model/name)!=digest for name,digest in record['generated_sha256'].items()):
            raise ValueError('Model changed')
    guard();out.mkdir(parents=True,exist_ok=False)
    shutil.copytree(model/'library',out/'library')
    old=str(Path(yaml.safe_load((model/'arch.yaml').read_text())['macro']).parent)
    csv=out/'localized.csv';csv.write_text((model/'r1_resource_control.csv').read_text().replace(old,str(out)))
    api=FABulous_API(VerilogCodeGenerator());api.loadFabric(csv)
    shutil.copyfile(io,out/'io_place.py')
    shutil.copyfile(model/'fabric.v',out/'fabric.v')
    manifest=dict(source_run='39696703659',source_revision='9768c77325ca34b93d408f526c0d8c902b62ce4a',tiles={},
                  synthesis_executed=False,timing_acceptance=False,physical_acceptance=False)
    manifest['yosys_version']=subprocess.check_output(['yosys','-V'],text=True).strip()
    (out/'ATTRIBUTION.md').write_text('I/O placement: librelane_plugin_fabulous dcc038217472822330b33f61fadbc06e0c3cc96d, Apache-2.0; original notice retained. WARP generated design: project Apache-2.0. PDK separately pinned to2bbec755dc67ca3db0261c3d6163e15735d66710.\n')
    side_names={'N':'NORTH','S':'SOUTH','E':'EAST','W':'WEST'}
    orders={}
    for tile,digest in MAPPED.items():
        mapped=evidence/'mapped-cost'/tile/'mapped.json'
        if sha(mapped)!=digest:raise ValueError('Changed frozen map: '+tile)
        folder=out/tile;folder.mkdir()
        graph=json.loads(mapped.read_text());module=graph['modules'][tile]
        counts=Counter(c['type'] for c in module['cells'].values() if c['type']!='$scopeinfo')
        original=json.dumps([module['cells'],module['ports']],sort_keys=True)
        for net in module['netnames'].values():
            if len(net['bits'])==1:net.get('attributes',{}).pop('single_bit_vector',None)
        if original!=json.dumps([module['cells'],module['ports']],sort_keys=True):raise ValueError('Connectivity changed')
        normalized=folder/'mapped.json';normalized.write_text(json.dumps(graph)+'\n')
        script=folder/'export.ys';nl=folder/'tile.nl.v'
        script.write_text('read_json '+json.dumps(str(normalized))+'\nselect -clear\nselect '+tile+
                          '\nwrite_verilog -selected -noattr -noexpr '+json.dumps(str(nl))+'\n')
        with (folder/'export.log').open('w') as log:
            subprocess.run(['yosys','-Q','-T','-s',str(script)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
        text,alias_changes=direct_port_aliases(nl.read_text(),module['ports'])
        nl.write_text(text)
        header=dict(module);header['cells']={n:c for n,c in module['cells'].items() if c['type']!='$scopeinfo'}
        (folder/'header.json').write_text(json.dumps(dict(modules={tile:header}))+'\n')
        cfg=yaml.safe_load((out/'library/tiles/tiny'/tile/'config.yaml').read_text())
        external=cfg.get('FABULOUS_EXTERNAL_SIDE','S')
        api.gen_io_pin_order_config(api.getTile(tile),folder/'pins-generated.yaml',external_port_side=getattr(Side,side_names[external]))
        pins,removed=physical_pin_order(yaml.safe_load((folder/'pins-generated.yaml').read_text()),signal_names(module['ports']),api.fabric.disableUserCLK)
        (folder/'pins.yaml').write_text(yaml.safe_dump(pins,sort_keys=False))
        orders[tile]=pins
        manifest['tiles'][tile]=dict(mapped_sha256=digest,expected_cells=dict(counts),ports=module['ports'],
                                     configuration_latches=counts['sg13cmos5l_dlhq_1'],external_side=external,
                                     removed_disabled_clock_ports=removed,port_alias_normalization=alias_changes)
    # Preserve the actual generated fabric connectivity, using frozen macro headers.
    script=out/'connections.ys'
    script.write_text(''.join('read_verilog -lib '+json.dumps(str(out/t/'tile.nl.v'))+'\n' for t in MAPPED)+
                      'read_verilog '+json.dumps(str(out/'fabric.v'))+'\nhierarchy -check -top eFPGA\nwrite_json '+json.dumps(str(out/'connections.json'))+'\n')
    with (out/'connections.log').open('w') as log:
        subprocess.run(['yosys','-Q','-T','-s',str(script)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    alignment=align_pin_orders(json.loads((out/'connections.json').read_text())['modules']['eFPGA'],orders,
                               {t:signal_names(m['ports']) for t,m in manifest['tiles'].items()})
    for tile,pins in orders.items():
        shutil.copyfile(out/tile/'pins.yaml',out/tile/'pins-before-alignment.yaml')
        (out/tile/'pins.yaml').write_text(yaml.safe_dump(pins,sort_keys=False))
    (out/'pin-alignment.json').write_text(json.dumps(alignment,indent=2,sort_keys=True)+'\n')
    manifest['files']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and 'library' not in p.relative_to(out).parts}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');guard()


def check_neighbors(design,inventories,width):
    """Check actual adjacent cell nets, not inferred port-name pair lists."""
    for tile,inventory in inventories.items():
        w,h=footprint(tile,width)
        if inventory['die']!=[0,0,round(w*1000),round(h*1000)]:
            raise ValueError('Native tile dimensions differ from declared grid')
    nets=defaultdict(list);positions={}
    for name,cell in design['cells'].items():
        m=re.fullmatch(r'Tile_X(\d+)Y(\d+)_(.+)',name)
        if not m or cell['type'] not in MAPPED:raise ValueError('Unexpected fabric instance')
        x,y=int(m[1]),int(m[2]);tile=cell['type'];positions[name]=(x,y,tile)
        for port,bits in cell['connections'].items():
            for i,bit in enumerate(bits):
                if isinstance(bit,int):nets[bit].append((name,port if len(bits)==1 else f'{port}[{i}]'))
    if len(positions)!=40:raise ValueError('Incomplete assembled grid')
    checked=0;types=Counter();nonadjacent=[]
    for bit,ends in nets.items():
        for i,(a,pa) in enumerate(ends):
            for b,pb in ends[i+1:]:
                ax,ay,at=positions[a];bx,by,bt=positions[b]
                if a==b:continue
                if abs(ax-bx)+abs(ay-by)!=1:
                    nonadjacent.append([a,pa,b,pb]);continue
                ia=inventories[at];ib=inventories[bt]
                aa=ia['pins'][pa];bb=ib['pins'][pb]
                if sorted((aa['direction'],bb['direction']))!=['INPUT','OUTPUT']:
                    raise ValueError('Adjacent connection is not one driver and one sink')
                horizontal=ax!=bx
                def edge(box,side,die):
                    layer,x0,y0,x1,y1=box
                    if side=='E':return x1==die[2]
                    if side=='W':return x0==0
                    if side=='N':return y1==die[3]
                    return y0==0
                sa,sb=(('E','W') if ax<bx else ('W','E')) if horizontal else (('S','N') if ay<by else ('N','S'))
                # Row and column dimensions are uniform within each neighbor pair.
                matches=[]
                for ba in aa['boxes']:
                    for bz in bb['boxes']:
                        axis=(2,4) if horizontal else (1,3)
                        if ba[0]==bz[0] and sum(ba[k] for k in axis)==sum(bz[k] for k in axis) and edge(ba,sa,ia['die']) and edge(bz,sb,ib['die']):matches.append((ba,bz))
                if not matches:raise ValueError(f'Unaligned adjacent net {bit}: {a}.{pa} -> {b}.{pb}')
                checked+=1;types['/'.join(sorted((at,bt)))]+=1
    if nonadjacent:raise ValueError('Unexpected nonadjacent direct connections: '+str(nonadjacent[:3]))
    if not checked:raise ValueError('No adjacent connections checked')
    return dict(adjacent_bit_pairs=checked,type_pairs=dict(types),grid_instances=len(positions))


def inside(bundle,out):
    from librelane.common import Path as LLPath
    from librelane.flows import SequentialFlow
    from librelane.state import State,DesignFormat
    from librelane.steps import OpenROAD,Odb
    sys.path.insert(0,str(ROOT/'test_internal'))
    from cloud_tile_preflight import PIN_OBSERVER,parse_pin_inventory
    bundle,out=Path(bundle).resolve(),Path(out).resolve();manifest=json.loads((bundle/'manifest.json').read_text())
    if any(sha(bundle/p)!=d for p,d in manifest['files'].items()):raise ValueError('Prepared inputs changed')
    class TileIO(Odb.CustomIOPlacement):
        id='Odb.R1InterfacePins'
        def get_script_path(self):return str(bundle/'io_place.py')
    class Preflight(SequentialFlow):Steps=[OpenROAD.Floorplan,Odb.SetPowerConnections,TileIO]
    out.mkdir(parents=True,exist_ok=False)
    observer=out/'observe.tcl'
    observer.write_text(PIN_OBSERVER.replace('[join [lsort $boxes] ;]','[join [lsort $boxes] {;}]')+'''
set counts [dict create]
set area 0
foreach inst [$block getInsts] {
 set master [$inst getMaster]
 dict incr counts [$master getName]
 set area [expr {$area+[$master getWidth]*[$master getHeight]}]
 if {[$master getName] in {sg13cmos5l_tiehi sg13cmos5l_tielo}} {
  foreach pin [$inst getITerms] {
   if {[[$pin getMTerm] getIoType] eq "OUTPUT"} {
    puts "R1_TIE\t[$master getName]\t[[$pin getMTerm] getName]\t[[$pin getNet] getName]"
   }
  }
 }
}
set core [$block getCoreArea]
puts "R1_CELLS\t$counts"
puts "R1_AREA\t$area"
puts "R1_CORE\t[$core xMin]\t[$core yMin]\t[$core xMax]\t[$core yMax]"
''')
    result=dict(passed=False,cases={},neighbors={},run=os.environ.get('GITHUB_RUN_ID'),attempt=os.environ.get('GITHUB_RUN_ATTEMPT'),input_manifest_sha256=sha(bundle/'manifest.json'),timing_acceptance=False,physical_acceptance=False)
    for width in WIDTHS:
        inventories={}
        for tile,m in manifest['tiles'].items():
            key=tile+'-width'+str(width).replace('.','_');folder=out/key;folder.mkdir();row=dict(passed=False)
            result['cases'][key]=row
            w,h=footprint(tile,width)
            try:
                config=dict(DESIGN_NAME=tile,VERILOG_FILES=[str(bundle/tile/'tile.nl.v')],CLOCK_PERIOD=20,CLOCK_PORT=None,
                            FP_SIZING='absolute',DIE_AREA=[0,0,w,h],BOTTOM_MARGIN_MULT=1,TOP_MARGIN_MULT=1,LEFT_MARGIN_MULT=6,RIGHT_MARGIN_MULT=6,
                            VDD_NETS=['VPWR'],GND_NETS=['VGND'],IO_PIN_ORDER_CFG=str(bundle/tile/'pins.yaml'),ERRORS_ON_UNMATCHED_IO='both',RT_MIN_LAYER='Metal2',RT_MAX_LAYER='Metal4',IO_PIN_H_EXTENSION=0,IO_PIN_V_EXTENSION=0)
                flow=Preflight(config,design_dir=str(bundle),pdk='ihp-sg13cmos5l',pdk_root=os.environ['PDK_ROOT'])
                state=flow.start(with_initial_state=State({DesignFormat.NETLIST:LLPath(str(bundle/tile/'tile.nl.v')),DesignFormat.JSON_HEADER:LLPath(str(bundle/tile/'header.json'))}),_force_run_dir=str(folder))
                odb=Path(str(state[DesignFormat.ODB]));log=folder/'census.log'
                with log.open('w') as stream:
                    subprocess.run(['openroad','-exit',str(observer)],stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,WARP_TILE_PIN_INPUT=str(odb)),check=True,timeout=120)
                text=log.read_text();inv=parse_pin_inventory(text);check_pins(inv,signal_names(m['ports']))
                expected_dirs={pin:port['direction'].upper() for name,port in m['ports'].items() for pin in ([name] if len(port['bits'])==1 else [f'{name}[{i}]' for i in range(port.get('offset',0),port.get('offset',0)+len(port['bits']))])}
                if any(p['direction']!=expected_dirs[n] for n,p in inv['pins'].items()):raise ValueError('Native pin direction changed')
                counts=next(l for l in text.splitlines() if l.startswith('R1_CELLS\t')).split('\t')[1].split();counts=dict(zip(counts[::2],map(int,counts[1::2])))
                extra=import_counts(counts,m['expected_cells'])
                constants={tuple(l.split('\t')[1:]) for l in text.splitlines() if l.startswith('R1_TIE\t')}
                allowed={('sg13cmos5l_tiehi','L_HI','one_'),('sg13cmos5l_tielo','L_LO','zero_')}
                if constants!={c for c in allowed if c[0] in extra}:raise ValueError('Native literal driver binding differs')
                core=list(map(int,next(l for l in text.splitlines() if l.startswith('R1_CORE\t')).split('\t')[1:]))
                area=int(next(l for l in text.splitlines() if l.startswith('R1_AREA\t')).split('\t')[1]);capacity=(core[2]-core[0])*(core[3]-core[1])
                if capacity<=0 or area>capacity:raise ValueError('Mapped cells exceed native core')
                (folder/'pins.json').write_text(json.dumps(inv,indent=2)+'\n');inventories[tile]=inv
                row.update(passed=True,odb_sha256=sha(odb),signal_pins=len(inv['pins']),cells=counts,constant_drivers=extra,cell_area_dbu2=area,core_area_dbu2=capacity)
            except Exception as exc:row['error']=str(exc)
            (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        try:
            if set(inventories)!=set(MAPPED):raise ValueError('Missing admitted tile geometry')
            result['neighbors'][str(width)]=dict(passed=True,**check_neighbors(json.loads((bundle/'connections.json').read_text())['modules']['eFPGA'],inventories,width))
        except Exception as exc:result['neighbors'][str(width)]=dict(passed=False,error=str(exc))
    result['passed']=all(r['passed'] for r in result['cases'].values()) and all(r['passed'] for r in result['neighbors'].values())
    (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    if not result['passed']:raise RuntimeError('All-type pin/core/interface screen failed; outcomes retained')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('prepare','inside'))
    for name in ('evidence','io','bundle','out'):p.add_argument('--'+name,type=Path,required=name=='out')
    a=p.parse_args()
    if a.mode=='prepare':prepare(a.evidence,a.io,a.out)
    else:inside(a.bundle,a.out)
