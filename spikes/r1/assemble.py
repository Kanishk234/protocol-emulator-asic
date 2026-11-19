"""Assemble the 40 frozen R1 leaves, then check macro geometry in hosted EDA."""
import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess

from assembly_catalog import prepare as prepare_catalog, sha
from assembly_contacts import inventory, prepare as prepare_contacts, scalar_connections
from detailed_leaf import OBSERVER
from gds_contexts import (labels, library, merge_contexts, record, records, text,
                          top_structure, translated_label)

NAME = 'warp_r1_candidate'
UNITS = bytes.fromhex('001403053e4189374bc6a7f03944b82fa09b5a54')
ROOT = Path(__file__).resolve().parents[2]
SCOPE = ('Assembled R1 macro geometry diagnostic only; no extracted timing, '
         'complete clock/power/shell integration, replacement or submission acceptance.')


def view(root, state, key):
    value = state[key]
    if not isinstance(value, str) or value.count('/build/leaf_finish/') != 1:
        raise ValueError('Unknown finished source view')
    path = Path(root)/value.split('/build/leaf_finish/', 1)[1]
    if not path.resolve().is_relative_to(Path(root).resolve()) or not path.is_file():
        raise ValueError('Finished view escapes authenticated artifact')
    return path


def rename_lef(source, original, renamed):
    patterns = [(rf'(?m)^MACRO {re.escape(original)}$', 'MACRO '+renamed),
                (rf'(?m)^(\s*FOREIGN) {re.escape(original)} ;$', rf'\g<1> {renamed} ;'),
                (rf'(?m)^END {re.escape(original)}$', 'END '+renamed)]
    for pattern, replacement in patterns:
        source, count = re.subn(pattern, replacement, source)
        if count != 1:
            raise ValueError('Unexpected leaf LEF master declarations')
    return source


def rename_netlist(source, original, renamed):
    source, count = re.subn(rf'(?m)^module {re.escape(original)} \(',
                            'module '+renamed+' (',source)
    if count != 1 or len(re.findall(r'(?m)^module ',source)) != 1:
        raise ValueError('Unexpected leaf netlist module declarations')
    return source


def top_netlist(top, places, powered=True):
    ports = top['ports']; names = list(ports)+(['VPWR','VGND'] if powered else [])
    if any(not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', p) for p in names):
        raise ValueError('Unexpected top port name')
    lines = ['module '+NAME+' ('+', '.join(names)+');']
    for name,p in ports.items():
        width=len(p['bits']); size='' if width==1 else f'[{width-1}:0] '
        if p.get('offset',0) or p.get('upto',0):
            raise ValueError('Unexpected top port indexing')
        lines.append(f'{p["direction"]} {size}{name};')
    if powered:lines.extend(('inout VPWR;','inout VGND;'))
    bits={bit for c in top['cells'].values() for bs in c['connections'].values() for bit in bs}
    if any(type(b) is not int for b in bits):
        raise ValueError('Unexpected top connection constant')
    lines.extend(f'wire n_{b};' for b in sorted(bits))
    for name,p in ports.items():
        for i,b in enumerate(p['bits']):
            pin=name if len(p['bits'])==1 else f'{name}[{i}]'
            if b not in bits or p['direction'] not in ('input','output'):
                raise ValueError('Unconnected or unsupported top port')
            lines.append(f'assign n_{b} = {pin};' if p['direction']=='input' else f'assign {pin} = n_{b};')
    for row in places:
        cell=top['cells'][row['instance']]
        conns=['.VPWR(VPWR)','.VGND(VGND)'] if powered else []
        for pin,bs in cell['connections'].items():
            value='n_'+str(bs[0]) if len(bs)==1 else '{'+', '.join('n_'+str(b) for b in reversed(bs))+'}'
            conns.append('.'+pin+'('+value+')')
        lines.append(row['planned_master']+' '+row['instance']+' ('+', '.join(conns)+');')
    return '\n'.join(lines+['endmodule',''])


def external_pins(top, plan, views):
    """Export only real outer-boundary signal access and all supply stripes."""
    endpoints = {}; physical = {}; width,height=plan['macro_size_dbu']
    for place in plan['instances']:
        name=place['instance']; ports,boxes=views[place['context']]
        ox,oy=place['origin_dbu']
        for pin,bit in scalar_connections(top['cells'][name]).items():
            endpoints.setdefault(bit,[]).append((place,pin))
        physical[name] = {p:[(layer,(x0+ox,y0+oy,x1+ox,y1+oy))
                             for layer,(x0,y0,x1,y1) in bs] for p,bs in boxes.items()}
    result = {}
    for name,port in top['ports'].items():
        for i,bit in enumerate(port['bits']):
            target=name if len(port['bits'])==1 else f'{name}[{i}]'; access=[]
            for place,pin in endpoints.get(bit,[]):
                boxes=[(layer,b) for layer,b in physical[place['instance']][pin]
                       if b[0]==0 or b[1]==0 or b[2]==width or b[3]==height]
                if boxes:
                    access.append(dict(instance=place['instance'],context=place['context'],
                                       pin=pin,origin_dbu=place['origin_dbu'],boxes=boxes))
            if not access:
                raise ValueError('No outer-boundary access for top signal '+target)
            result[target]=dict(direction=port['direction'].upper(),kind='SIGNAL',access=access)
    for pin,kind in [('VPWR','POWER'),('VGND','GROUND')]:
        access=[]
        for place in plan['instances']:
            boxes=physical[place['instance']].get(pin,[])
            if not boxes:
                raise ValueError('Missing leaf power access')
            access.append(dict(instance=place['instance'],context=place['context'],pin=pin,
                               origin_dbu=place['origin_dbu'],boxes=boxes))
        result[pin]=dict(direction='INOUT',kind=kind,access=access)
    return result


def prepare(capsule, sources, native, out):
    capsule,sources,native,out=(Path(p).resolve() for p in (capsule,sources,native,out))
    out.mkdir(parents=True,exist_ok=False)
    prepare_catalog(capsule,out/'catalog.json')
    contact=prepare_contacts(capsule,out/'catalog.json',sources,native,out/'contacts.json')
    if not contact['passed']:
        raise ValueError('Assembling would retain signal opens or shorts')
    plan=json.loads((out/'catalog.json').read_text());roots=json.loads(sources.read_text())
    top=json.loads((capsule/'mapped/input/connections.json').read_text())['modules']['eFPGA']
    views={};gds_inputs=[];paths=[];netlists=[];files={}
    for case,row in plan['contexts'].items():
        root=Path(roots[case]);state_path=root/'run/27-checker-lvs/state_out.json'
        state=json.loads(state_path.read_text());folder=out/'contexts'/case;folder.mkdir(parents=True)
        paths.extend((state_path,root/'final.txt'))
        views[case]=inventory((root/'final.txt').read_text())
        files[case]={}
        for kind in ('lef','nl','pnl','gds'):
            path=view(root,state,kind);paths.append(path)
            files[case][kind]=str(path)
            if kind=='gds':
                _,units,_=library(path.read_bytes())
                if units!=UNITS:
                    raise ValueError('GDS database units differ from 1nm physical catalog')
                gds_inputs.append((case,row['source_master'],row['planned_master'],path.read_bytes()))
            else:
                content=path.read_text()
                content=(rename_lef if kind=='lef' else rename_netlist)(content,row['source_master'],row['planned_master'])
                target=folder/(row['planned_master']+'.'+kind+('.v' if kind!='lef' else ''))
                target.write_text(content);files[case]['renamed_'+kind]=str(target)
                if kind=='pnl':netlists.append(content)
    header,cells,shared=merge_contexts(gds_inputs)
    pins=external_pins(top,plan,views);pin_labels=[]
    for target,row in pins.items():
        for access in row['access']:
            master=plan['contexts'][access['context']]['planned_master']
            found=[e for pin,e in labels(cells[master]) if pin==access['pin']]
            if not found:
                raise ValueError('Missing GDS label for exported pin')
            copied=0
            for element in found:
                xy=[r for k,d,r in records(b''.join(element)) if k==16]
                if len(xy)!=1:raise ValueError('Unexpected GDS pin label shape')
                x,y=struct.unpack('>ii',xy[0][4:]);ox,oy=access['origin_dbu']
                if any(b[0]<=x+ox<=b[2] and b[1]<=y+oy<=b[3] for layer,b in access['boxes']):
                    pin_labels.append(translated_label(element,target,access['origin_dbu']));copied+=1
            if not copied:
                raise ValueError('GDS label does not occupy exported pin access')
    top_gds=top_structure(NAME,plan['instances'],*plan['macro_size_dbu'],pin_labels)
    (out/(NAME+'.gds')).write_bytes(header+b''.join(cells.values())+top_gds+record(4))
    netlist=top_netlist(top,plan['instances'])
    (out/(NAME+'.v')).write_text(netlist)
    (out/(NAME+'.pnl.v')).write_text('\n'.join(netlists+[netlist]))
    (out/'pins.json').write_text(json.dumps(pins,indent=2)+'\n')
    (out/'views.json').write_text(json.dumps(files,indent=2)+'\n')
    (out/'top.json').write_text(json.dumps(top)+'\n')
    source_paths=list(contact['input_sha256'])+paths+[Path(__file__),
        Path(__file__).with_name('gds_contexts.py'),Path(__file__).with_name('detailed_leaf.py'),
        Path(__file__).with_name('assembly_catalog.py'),Path(__file__).with_name('assembly_fetch.py'),
        Path(__file__).with_name('assembly_sources.json'),Path(__file__).with_name('assembly_ports.py')]
    generated=[p for p in out.rglob('*') if p.is_file()]
    result=dict(materialized=True,scope=SCOPE,geometry_written=True,physical_acceptance=False,
                timing_acceptance=False,assembly_acceptance=False,leaf_contexts=26,grid_instances=40,
                unique_shared_gds_cells=len(shared),shared_gds_fingerprints=shared,
                top_signal_pins=len(pins)-2,exported_pin_labels=len(pin_labels),
                input_sha256={str(p):sha(p) for p in map(Path,source_paths)},
                generated_sha256={str(p):sha(p) for p in generated})
    (out/'plan.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def database_script(out, tech):
    out=Path(out).resolve()
    script=[f'read_lef {{{tech}}}']
    views=json.loads((out/'views.json').read_text())
    script.extend('read_lef {'+v['renamed_lef']+'}' for v in views.values())
    script.extend([f'read_verilog {{{out/(NAME+".v")}}}',f'link_design {NAME}',
                   'set block [ord::get_db_block]', 'set tech [ord::get_db_tech]',
                   'if {[$tech getDbUnitsPerMicron] != 1000} {error "wrong physical DBU"}',
                   '$block setDieArea [odb::new_Rect 0 0 1061760 669060]'])
    catalog=json.loads((out/'catalog.json').read_text())
    for p in catalog['instances']:
        script.extend([f'set inst [$block findInst {p["instance"]}]',
                       '$inst setOrient R0',f'$inst setOrigin {p["origin_dbu"][0]} {p["origin_dbu"][1]}',
                       '$inst setPlacementStatus FIRM'])
    for pin,row in json.loads((out/'pins.json').read_text()).items():
        script.extend([f'set term [$block findBTerm {{{pin}}}]',f'$term setSigType {row["kind"]}',
                       'set bp [odb::dbBPin_create $term]','$bp setPlacementStatus FIRM'])
        for access in row['access']:
            for layer,box in access['boxes']:
                script.append(f'odb::dbBox_create $bp [$tech findLayer {layer}] '+ ' '.join(map(str,box)))
    script.extend([f'inventory {{{out/"assembled.txt"}}}',
                   f'write_db {{{out/(NAME+".odb")}}}',f'write_def {{{out/(NAME+".def")}}}',
                   f'write_abstract_lef -bloat_occupied_layers {{{out/(NAME+".lef")}}}',
                   'puts "R1_ASSEMBLY_DB_END"'])
    return OBSERVER+'\n'+'\n'.join(script)+'\n'


def check_database(out):
    out=Path(out); catalog=json.loads((out/'catalog.json').read_text())
    rows=[r.split('\t') for r in (out/'assembled.txt').read_text().splitlines()]
    cells={r[1]:r for r in rows if r[0]=='CELL'}
    if set(cells)!={p['instance'] for p in catalog['instances']}:
        raise ValueError('Assembled database instance census changed')
    for p in catalog['instances']:
        r=cells[p['instance']]; c=catalog['contexts'][p['context']]; x,y=p['origin_dbu']
        if r[2:]!=[p['planned_master'],str(x),str(y),str(x+c['width_dbu']),str(y+c['height_dbu']),'R0','FIRM']:
            raise ValueError('Assembled database master/position/shape changed')
    ports,boxes=inventory((out/'assembled.txt').read_text())
    pins=json.loads((out/'pins.json').read_text())
    if set(ports)!=set(pins):raise ValueError('Assembled database port census changed')
    for p,v in pins.items():
        expected={(layer,tuple(box)) for access in v['access'] for layer,box in access['boxes']}
        if (ports[p]['direction']!=v['direction'] or ports[p]['kind']!=v['kind']
                or set(boxes[p])!=expected):
            raise ValueError('Assembled database pin access changed')
    top=json.loads((out/'top.json').read_text());expected={}
    for name,c in top['cells'].items():
        expected.update({(name,p):b for p,b in scalar_connections(c).items()})
    terms={};pg=0
    for r in rows:
        if r[0]!='ITERM':continue
        key=(r[1],r[2])
        if r[2] in ('VPWR','VGND'):
            if r[3]!=r[2]:raise ValueError('Wrong assembled supply binding')
            pg+=1
        else:
            if key in terms:raise ValueError('Duplicate assembled instance terminal')
            terms[key]=r[3]
    if set(terms)!=set(expected) or pg!=2*len(cells):
        raise ValueError('Assembled instance terminal census changed')
    logical_to_physical={};physical_to_logical={}
    def bind(bit,net):
        if (bit in logical_to_physical and logical_to_physical[bit]!=net or
                net in physical_to_logical and physical_to_logical[net]!=bit or net=='NC'):
            raise ValueError('Assembled database signal connectivity changed')
        logical_to_physical[bit]=net;physical_to_logical[net]=bit
    for key,bit in expected.items():bind(bit,terms[key])
    for pin,p in top['ports'].items():
        for i,bit in enumerate(p['bits']):
            name=pin if len(p['bits'])==1 else f'{pin}[{i}]'
            bind(bit,ports[name]['net'])
    return dict(instances=len(cells),top_signal_pins=len(ports)-2,power_pins=2,
                signal_instance_terminals=len(terms),power_instance_terminals=pg,
                distinct_logical_nets=len(logical_to_physical))


def inside(out):
    from librelane.flows.classic import Classic
    from librelane.state import State,DesignFormat
    from librelane.steps import Magic,KLayout,Netgen,Checker
    from cloud_tile_harden import metric_json
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    for p,d in {**plan['input_sha256'],**plan['generated_sha256']}.items():
        if sha(p)!=d:raise ValueError('Assembly source or generated view changed')
    class Geometry(Classic):
        Steps=[Magic.DRC,Checker.MagicDRC,KLayout.DRC,Checker.KLayoutDRC,
               Magic.SpiceExtraction,Checker.IllegalOverlap,Netgen.LVS,Checker.LVS]
    config=dict(DESIGN_NAME=NAME,VERILOG_FILES=[str(out/(NAME+'.v'))],
                CLOCK_PERIOD=20,CLOCK_PORT=None,PRIMARY_GDSII_STREAMOUT_TOOL='klayout',
                VDD_NETS=['VPWR'],GND_NETS=['VGND'],MAGIC_DRC_USE_GDS=True,
                MAGIC_EXT_USE_GDS=True,MAGIC_EXT_ABSTRACT=False,MAGIC_EXT_UNIQUE='all',
                LVS_IGNORE_CELLS=[],LVS_FLATTEN_CELLS=list(json.loads((out/'catalog.json').read_text())['contexts'][c]['planned_master']
                    for c in json.loads((out/'catalog.json').read_text())['contexts']))
    result=dict(passed=False,scope=SCOPE,physical_acceptance=False,timing_acceptance=False,assembly_acceptance=False)
    try:
        flow=Geometry(config,design_dir=str(out),pdk='ihp-sg13cmos5l',pdk_root=os.environ['PDK_ROOT'])
        (out/'resolved-config.json').write_text(flow.config.dumps()+'\n')
        tech=next(iter(flow.config['TECH_LEFS'].values()))
        (out/'database.tcl').write_text(database_script(out,tech))
        with (out/'database.log').open('w') as log:
            subprocess.run(['openroad','-exit',str(out/'database.tcl')],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        if 'R1_ASSEMBLY_DB_END' not in (out/'database.log').read_text():
            raise ValueError('Incomplete physical assembly database')
        result['database_inventory']=check_database(out)
        state=State.load({DesignFormat.GDS.id:str(out/(NAME+'.gds')),DesignFormat.DEF.id:str(out/(NAME+'.def')),
                     DesignFormat.NETLIST.id:str(out/(NAME+'.v')),DesignFormat.POWERED_NETLIST.id:str(out/(NAME+'.pnl.v'))})
        final=flow.start(with_initial_state=state,_force_run_dir=str(out/'run'))
        metrics=json.loads(json.dumps(final.metrics.to_raw_dict(),default=metric_json))
        gates=('magic__drc_error__count','klayout__drc_error__count','magic__illegal_overlap__count','design__lvs_error__count')
        result['physical_gate_metrics']={k:metrics.get(k) for k in gates}
        if any(type(metrics.get(k)) not in (int,float) or metrics[k]!=0 for k in gates):
            raise ValueError('Missing or nonzero assembled geometry gate')
        from assembly_ports import spice_ports,strict_verdict
        reports=list((out/'run').glob('*/reports/lvs.netgen.rpt'))
        extracted=list((out/'run').glob('*/'+NAME+'.spice'))
        if len(reports)!=1 or len(extracted)!=1:
            raise ValueError('Missing detailed assembly LVS evidence')
        strict_verdict(reports[0].read_text(),spice_ports(extracted[0].read_text(),NAME),
                       json.loads((out/'pins.json').read_text()))
        result['strict_lvs_verdict']='Circuits match uniquely.'
        result.update(passed=True,gds_sha256=sha(out/(NAME+'.gds')),pnl_sha256=sha(out/(NAME+'.pnl.v')))
    except Exception as exc:
        result['error']=str(exc)
        partial={}
        for path in sorted((out/'run').glob('*/state_out.json')):
            partial.update(json.loads(path.read_text()).get('metrics',{}))
        result['completed_stage_metrics']=partial
    if any(sha(p)!=d for p,d in {**plan['input_sha256'],**plan['generated_sha256']}.items()):
        result.update(passed=False,error='Assembly input changed during execution')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    if not result['passed']:raise SystemExit(result['error'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);subs=p.add_subparsers(dest='mode',required=True)
    prep=subs.add_parser('prepare')
    for name in ('capsule','sources','native','out'):prep.add_argument('--'+name,type=Path,required=True)
    subs.add_parser('inside').add_argument('--out',type=Path,required=True)
    args=vars(p.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else inside)(**args)
