"""Preserve finished leaf routes in a flat extraction view; requires geometry XOR."""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import re
import os
import subprocess

from assemble import NAME, view
from assembly_catalog import sha
from assembly_contacts import Union,inventory,scalar_connections
from detailed_leaf import OBSERVER


def section(source,name,optional=False):
    matches=list(re.finditer(rf'(?ms)^{name} (\d+) ;\n(.*?)^END {name}\s*$',source))
    if not matches and optional:return []
    if len(matches)!=1:raise ValueError('Missing or duplicate DEF section '+name)
    match=matches[0];parts=[p.strip() for p in match[2].split(';') if p.strip()]
    if len(parts)!=int(match[1]) or any(not p.startswith('- ') for p in parts):
        raise ValueError('Malformed DEF section '+name)
    return [p[2:].strip() for p in parts]


def translate_routes(source,origin):
    """Shift absolute route points; preserve wildcards/extensions/relative RECTs."""
    def point(match):
        values=match[1].split();before=source[:match.start()].rstrip().split()[-1]
        if before=='RECT':
            if len(values)!=4 or any(not re.fullmatch(r'-?\d+',v) for v in values):
                raise ValueError('Malformed relative DEF route rectangle')
            return match[0]
        if len(values) not in (2,3) or any(v!='*' and not re.fullmatch(r'-?\d+',v) for v in values):
            raise ValueError('Unexpected absolute DEF route point')
        for i in range(2):
            if values[i]!='*':values[i]=str(int(values[i])+origin[i])
        return '( '+' '.join(values)+' )'
    if source and not re.match(r'^\+ ROUTED\s',source):
        raise ValueError('Unsupported DEF routing policy')
    return re.sub(r'\(\s*([^()]*)\s*\)',point,source)


def net_record(source):
    match=re.fullmatch(r'(\S+)\s*((?:\(\s*\S+\s+\S+\s*\)\s*)*)'
                       r'\+ USE (SIGNAL|CLOCK|POWER|GROUND)\s*(.*)',source,re.S)
    if match is None:raise ValueError('Unsupported DEF net record')
    conns=[tuple(m.split()) for m in re.findall(r'\(\s*([^()]*)\s*\)',match[2])]
    return match[1],conns,match[3],match[4].strip()


def component(source,tile,origin):
    match=re.match(r'^(\S+)\s+(\S+)\s',source)
    if match is None:raise ValueError('Unsupported DEF component record')
    old=match[1];new=tile+'/'+old
    body=new+source[len(old):]
    def shift(m):
        return m[1]+f'( {int(m[2])+origin[0]} {int(m[3])+origin[1]} )'
    body,count=re.subn(r'(\+ (?:PLACED|FIXED|COVER) )\(\s*(-?\d+)\s+(-?\d+)\s*\)',shift,body)
    if count!=1:raise ValueError('Missing or duplicate DEF component placement')
    return body


def emit_section(name,rows):
    return f'{name} {len(rows)} ;\n'+'\n'.join('    - '+r+' ;' for r in rows)+f'\nEND {name}\n'


def prepare(assembly,sources,out):
    assembly,sources,out=(Path(p).resolve() for p in (assembly,sources,out))
    plan=json.loads((assembly/'plan.json').read_text())
    for path,digest in {**plan['input_sha256'],**plan['generated_sha256']}.items():
        if sha(path)!=digest:raise ValueError('Authenticated assembly input changed')
    catalog=json.loads((assembly/'catalog.json').read_text());top=json.loads((assembly/'top.json').read_text())
    roots=json.loads(sources.read_text());union=Union();data={}
    paths=[Path(__file__),sources,assembly/'plan.json',assembly/'catalog.json',assembly/'top.json',
           assembly/'pins.json',assembly/(NAME+'.gds'),Path(__file__).with_name('geometry_xor.py')]
    for p in catalog['instances']:
        tile=p['instance'];root=Path(roots[p['context']]);state=root/'run/27-checker-lvs/state_out.json'
        definition=view(root,json.loads(state.read_text()),'def');paths.extend([state,definition,root/'final.txt'])
        ports,boxes=inventory((root/'final.txt').read_text());source=definition.read_text()
        if 'UNITS DISTANCE MICRONS 1000 ;' not in source:
            raise ValueError('Flat extraction DEF units changed')
        for pin,bit in scalar_connections(top['cells'][tile]).items():
            union.join((tile,ports[pin]['net']),('top',bit))
        for pin in ('VPWR','VGND'):
            union.join((tile,ports[pin]['net']),('power',pin))
        data[tile]=(source,ports,boxes)
    groups=defaultdict(list)
    for node in list(union.parent):groups[union.find(node)].append(node)
    canonical={}
    for root,nodes in groups.items():
        power=[n[1] for n in nodes if n[0]=='power'];bits=[n[1] for n in nodes if n[0]=='top']
        if len(power)>1 or power and bits:raise ValueError('Conflicting power/signal aliases')
        canonical[root]=power[0] if power else 'r1_net_'+str(min(bits))
    def net(tile,name):
        node=(tile,name)
        return canonical[union.find(node)] if node in union.parent else tile+'/'+name
    vias={};components=[];connections=defaultdict(set);routes=defaultdict(list);kinds={};cells=[];terms=[]
    def add_route(name,body):
        if body:
            routes[name].append(body if not routes[name] else re.sub(r'^\+ ROUTED\s+','NEW ',body,count=1))
    for p in catalog['instances']:
        tile=p['instance'];source,ports,boxes=data[tile];origin=p['origin_dbu']
        for row in section(source,'VIAS',optional=True):
            name=row.split()[0];normalized=' '.join(row.split())
            if name in vias and vias[name]!=normalized:raise ValueError('Inconsistent shared DEF via geometry')
            vias[name]=normalized
        components.extend(component(row,tile,origin) for row in section(source,'COMPONENTS'))
        for category in ('NETS','SPECIALNETS'):
            for row in section(source,category):
                local,conns,kind,body=net_record(row);name=net(tile,local)
                if name in kinds and kinds[name]!=kind:raise ValueError('Conflicting DEF net kinds')
                kinds[name]=kind
                for cell,pin in conns:
                    if cell=='PIN':continue
                    if cell=='*':
                        if kind not in ('POWER','GROUND'):raise ValueError('Wildcard signal connection')
                        connections[name].add((cell,pin))
                    else:connections[name].add((tile+'/'+cell,pin))
                add_route(name,translate_routes(body,origin))
        # A leaf BPin's access metal is real GDS geometry. Retain it as a route
        # rectangle when its internal boundary port disappears during flattening.
        for pin,bs in boxes.items():
            if ports[pin]['kind'] in ('POWER','GROUND'):continue
            name=net(tile,ports[pin]['net'])
            for layer,(x0,y0,x1,y1) in bs:
                x,y=(x0+x1)//2,(y0+y1)//2
                rect=f'+ ROUTED {layer} ( {x+origin[0]} {y+origin[1]} ) RECT ( {x0-x} {y0-y} {x1-x} {y1-y} )'
                add_route(name,rect)
        for row in (Path(roots[p['context']])/'final.txt').read_text().splitlines():
            r=row.split('\t')
            if r[0]=='CELL':
                cells.append([tile+'/'+r[1],r[2],int(r[3])+origin[0],int(r[4])+origin[1],
                              int(r[5])+origin[0],int(r[6])+origin[1],*r[7:]])
            elif r[0]=='ITERM':terms.append([tile+'/'+r[1],r[2],net(tile,r[3])])
    pins=[];pin_plan=json.loads((assembly/'pins.json').read_text());port_net={}
    for pname,p in top['ports'].items():
        for i,bit in enumerate(p['bits']):
            port_net[pname if len(p['bits'])==1 else f'{pname}[{i}]']=canonical[union.find(('top',bit))]
    port_net.update(VPWR='VPWR',VGND='VGND')
    for pin,row in pin_plan.items():
        name=port_net[pin];connections[name].add(('PIN',pin));kinds.setdefault(name,row['kind'])
        boxes=sorted({(layer,*box) for a in row['access'] for layer,box in a['boxes']})
        body=f'{pin} + NET {name} + DIRECTION {row["direction"]} + USE {row["kind"]}'
        for layer,x0,y0,x1,y1 in boxes:
            body+=f'\n      + PORT + LAYER {layer} ( {x0} {y0} ) ( {x1} {y1} ) + FIXED ( 0 0 ) N'
        pins.append(body)
    nets=[];special=[]
    for name,kind in sorted(kinds.items()):
        row=name+' '+''.join(f'( {c} {p} ) ' for c,p in sorted(connections[name]))+'+ USE '+kind
        if routes[name]:row+='\n      '+'\n      '.join(routes[name])
        (special if kind in ('POWER','GROUND') else nets).append(row)
    header=f'VERSION 5.8 ;\nDIVIDERCHAR "/" ;\nBUSBITCHARS "[]" ;\nDESIGN {NAME} ;\nUNITS DISTANCE MICRONS 1000 ;\nDIEAREA ( 0 0 ) ( 1061760 669060 ) ;\n'
    output=header+emit_section('VIAS',list(vias.values()))+emit_section('COMPONENTS',components)
    output+=emit_section('PINS',pins)+emit_section('SPECIALNETS',special)+emit_section('NETS',nets)+'END DESIGN\n'
    out.mkdir(parents=True,exist_ok=False);(out/(NAME+'.def')).write_text(output)
    (out/'expected.json').write_text(json.dumps(dict(cells=cells,terms=terms,ports=port_net))+'\n')
    result=dict(prepared=True,geometry_xor_passed=False,physical_acceptance=False,timing_acceptance=False,
        cells=len(cells),terminals=len(terms),signal_nets=len(nets),power_nets=len(special),pins=len(pins),
        source_assembly=str(assembly),source_assembly_gds_sha256=sha(assembly/(NAME+'.gds')),
        input_sha256={str(p):sha(p) for p in paths},
        generated_sha256={str(p):sha(p) for p in out.iterdir() if p.is_file()},
        scope='Flat route view preparation only; native import, exact inventories, independent all-layer geometry XOR and real RC extraction are required before timing use.')
    (out/'plan.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def import_script(out,tech_lef,cell_lef):
    out=Path(out).resolve()
    return OBSERVER+f'''
read_lef {{{tech_lef}}}
read_lef {{{cell_lef}}}
read_def {{{out/(NAME+'.def')}}}
set b [ord::get_db_block]
if {{[[$b getTech] getDbUnitsPerMicron] != 1000}} {{error "wrong extraction DBU"}}
inventory {{{out/'imported.txt'}}}
write_db {{{out/(NAME+'.odb')}}}
write_def {{{out/'imported.def'}}}
write_verilog {{{out/(NAME+'.nl.v')}}}
puts "R1_FLAT_IMPORT_END"
'''


def check_import(out):
    out=Path(out);expected=json.loads((out/'expected.json').read_text())
    rows=[r.split('\t') for r in (out/'imported.txt').read_text().splitlines()]
    cells=[[r[1],r[2],*map(int,r[3:7]),*r[7:]] for r in rows if r[0]=='CELL']
    terms=[r[1:] for r in rows if r[0]=='ITERM']
    ports={r[1]:r[2] for r in rows if r[0]=='PORT'}
    if (sorted(cells)!=sorted(expected['cells']) or sorted(terms)!=sorted(expected['terms'])
            or ports!=expected['ports']):
        raise ValueError('Flat extraction import changed cells, placement, terminals or ports')
    wires=[r for r in rows if r[0]=='REQUIRED_NET']
    counts=Counter(n for cell,pin,n in expected['terms'] if n not in ('VPWR','VGND'))
    counts.update(n for p,n in expected['ports'].items() if p not in ('VPWR','VGND'))
    required={n for n,count in counts.items() if count>=2}
    if len(wires)!=len(required) or {r[1] for r in wires}!=required or any(r[2]!='1' for r in wires):
        raise ValueError('Flat extraction import has an unwired required signal net')
    result=dict(import_passed=True,cells=len(cells),terminals=len(terms),ports=len(ports),
                required_signal_nets_with_wires=len(wires),geometry_xor_passed=False,
                physical_acceptance=False,timing_acceptance=False)
    (out/'import-result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def inside(out):
    from librelane.flows.classic import Classic
    from librelane.state import State,DesignFormat
    from librelane.steps import KLayout,OpenROAD
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    source=Path(plan['source_assembly'])
    frozen={**plan['input_sha256'],**plan['generated_sha256']}
    if any(sha(p)!=d for p,d in frozen.items()):raise ValueError('Flat extraction input changed')
    config=dict(DESIGN_NAME=NAME,VERILOG_FILES=[str(source/(NAME+'.v'))],CLOCK_PERIOD=20,CLOCK_PORT=None,
                VDD_NETS=['VPWR'],GND_NETS=['VGND'],PRIMARY_GDSII_STREAMOUT_TOOL='klayout',STA_THREADS=2)
    class Stream(Classic):Steps=[KLayout.StreamOut]
    class Extract(Classic):Steps=[OpenROAD.RCX]
    result=dict(passed=False,physical_acceptance=False,timing_acceptance=False,
        scope='Route-preserving flat geometry comparison and full-macro RC extraction only. Active annotation, configured setup/hold/corners, shell, physical power and submission remain unqualified.')
    try:
        flow=Stream(config,design_dir=str(out),pdk='ihp-sg13cmos5l',pdk_root=os.environ['PDK_ROOT'])
        tech=next(iter(flow.config['TECH_LEFS'].values()));cell_lefs=flow.config['CELL_LEFS']
        if len(cell_lefs)!=1:raise ValueError('Unexpected standard-cell LEF population')
        script=out/'import.tcl';script.write_text(import_script(out,tech,cell_lefs[0]))
        with (out/'import.log').open('w') as log:
            subprocess.run(['openroad','-exit',str(script)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        if 'R1_FLAT_IMPORT_END' not in (out/'import.log').read_text():raise ValueError('Incomplete flat import')
        result['import_inventory']=check_import(out)
        state=State.load({DesignFormat.DEF.id:str(out/'imported.def'),DesignFormat.ODB.id:str(out/(NAME+'.odb')),
                          DesignFormat.NETLIST.id:str(out/(NAME+'.nl.v'))})
        streamed=flow.start(with_initial_state=state,_force_run_dir=str(out/'stream'))
        candidate=str(streamed[DesignFormat.GDS]);comparison=out/'geometry-xor.json'
        with (out/'geometry-xor.log').open('w') as log:
            subprocess.run(['klayout','-b','-r',str(Path(__file__).with_name('geometry_xor.py')),
                '-rd','reference='+str(source/(NAME+'.gds')),'-rd','candidate='+candidate,
                '-rd','top_name='+NAME,'-rd','out='+str(comparison)],
                stdout=log,stderr=subprocess.STDOUT,check=True,timeout=900)
        xor=json.loads(comparison.read_text());result['geometry_xor']=xor
        if xor.get('passed') is not True or xor.get('negative_control_detected') is not True:
            raise ValueError('Flat geometry differs or XOR negative control failed')
        extract=Extract(config,design_dir=str(out),pdk='ihp-sg13cmos5l',pdk_root=os.environ['PDK_ROOT'])
        final=extract.start(with_initial_state=state,_force_run_dir=str(out/'extract'))
        spefs=final[DesignFormat.SPEF]
        if not isinstance(spefs,dict) or not spefs:raise ValueError('No full-macro SPEF views')
        result['spef_views']={}
        for corner,path in spefs.items():
            p=Path(str(path));content=p.read_text()
            if '*DESIGN "'+NAME+'"' not in content or content.count('*D_NET ')==0:
                raise ValueError('Missing or empty full-macro SPEF')
            result['spef_views'][corner]=dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,
                                            extracted_net_records=content.count('*D_NET '))
        result['passed']=True
    except Exception as exc:result['error']=str(exc)
    if any(sha(p)!=d for p,d in frozen.items()):result.update(passed=False,error='Flat extraction inputs changed during execution')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    if not result['passed']:raise SystemExit(result['error'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    prep=sub.add_parser('prepare')
    for name in ('assembly','sources','out'):prep.add_argument('--'+name,type=Path,required=True)
    sub.add_parser('inside').add_argument('--out',type=Path,required=True)
    args=vars(p.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else inside)(**args)
