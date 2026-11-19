"""Qualify exported macro ports without modifying geometry or internal nets."""
import argparse
import json
import os
from pathlib import Path
import re
from decimal import Decimal

from assemble import NAME
from assembly_catalog import sha

SOURCE_RUN=44465623376
SOURCE_SHA='53240408475d03c229851fded0990e865cbc958b'
ARCHIVE_ID=14503110306
ARCHIVE_SHA='73c24f2ae6283f3d35ebfff76b50afa1678e1fa2d393f7c6508696173005d7cc'
SCRIPT_SHA='461bf51e4226c283de33361bad02f48d0335ad7ab05965cbba43e2677e040660'
GDS_SHA='21cdf462b8034b58b89a018ebd15cc295e3c3c44dec6e5cb1a86c357950877ad'
PNL_SHA='6639ad07e5b53486c06ac7cd83f9e225fe89645128bac410ce8facbd65042e71'


def spice_ports(text, master):
    lines=[]
    for line in text.splitlines():
        if line.startswith('+'):
            if not lines:raise ValueError('Orphan SPICE continuation')
            lines[-1]+=' '+line[1:].strip()
        else:lines.append(line.strip())
    rows=[r.split()[2:] for r in lines if re.match(r'^\.subckt\s+'+re.escape(master)+r'(?:\s|$)',r,re.I)]
    if len(rows)!=1 or len(rows[0])!=len(set(rows[0])):
        raise ValueError('Missing, duplicate or malformed extracted top subcircuit')
    return rows[0]


def strict_verdict(report, ports, expected):
    results=re.findall(r'^Final result:\s*(.+?)\s*$',report,re.M)
    if results!=['Circuits match uniquely.']:
        raise ValueError('Detailed LVS report does not match uniquely: '+str(results))
    if len(ports)!=len(expected) or set(ports)!=set(expected):
        raise ValueError('Extracted top-level port list differs from declared interface')
    return True


def context_port_block(contexts):
    if len(contexts)!=26:raise ValueError('Incomplete context port metadata')
    lines=[]
    for master,row in sorted(contexts.items()):
        pins=row['pins']
        if (not re.fullmatch(r'wp_r1_[a-z0-9_]+',master) or len(pins)!=len(set(pins)) or not pins
                or any(not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(?:\[\d+\])?',p) for p in pins)):
            raise ValueError('Invalid native context interface')
        expected=' '.join('{'+p+'}' for p in sorted(pins))
        width=Decimal(row['width_dbu']+1000)/1000;height=Decimal(row['height_dbu']+1000)/1000
        lines.extend([f'load {master} -dereference',f'box values -1um -1um {width}um {height}um',
            'port makeall','set actual_ports {}',
            'for {set n [port first]} {$n >= 0} {set n [port $n next]} {lappend actual_ports [port $n name]}',
            f'set expected_ports {{{expected}}}',
            f'set pf [open $::env(STEP_DIR)/ports-{master}.txt w]',
            'puts $pf [join $actual_ports "\\n"]','close $pf',
            'if {[lsort -unique $actual_ports] ne [lsort -unique $expected_ports]} {',
            f' error "R1 native context port metadata differs: {master}"','}',
            f'puts "R1_CONTEXT_PORTS {master} [llength [lsort -unique $actual_ports]]"'])
    return '\n'.join(lines)+'\n'


def annotate_script(original,pins,contexts=None):
    anchor='load $::env(DESIGN_NAME) -dereference\n'
    if original.count(anchor)!=1 or len(pins)!=449 or set(pins)-{'VPWR','VGND'}==set():
        raise ValueError('Unexpected extraction script or macro port population')
    if any(not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(?:\[\d+\])?',p) for p in pins):
        raise ValueError('Unsafe macro port name')
    expected=' '.join('{'+p+'}' for p in sorted(pins))
    addition='''
# Only root labels are exported interface names. The GDS metal is unchanged.
box values -1um -1um 1062.76um 670.06um
port makeall
set actual_ports {}
for {set n [port first]} {$n >= 0} {set n [port $n next]} {
    lappend actual_ports [port $n name]
}
set port_file [open $::env(STEP_DIR)/r1-port-names.txt w]
puts $port_file [join $actual_ports "\n"]
close $port_file
set expected_ports {EXPECTED}
if {[lsort -unique $actual_ports] ne [lsort -unique $expected_ports]} {
    error "R1 root port metadata differs from the declared interface"
}
puts "R1_EXPORTED_PORTS [llength [lsort -unique $actual_ports]]"
'''.replace('EXPECTED',expected)
    prefix=context_port_block(contexts) if contexts is not None else ''
    return original.replace(anchor,prefix+anchor+addition)


def flat_spice_script(annotated):
    anchor='ext2spice -o $netlist $::env(DESIGN_NAME).ext'
    if annotated.count(anchor)!=1 or 'ext2spice hierarchy off' in annotated:
        raise ValueError('Unexpected SPICE export script')
    return annotated.replace(anchor,'ext2spice hierarchy off\n'+anchor)


def retain_original_script(original,out):
    original,out=Path(original),Path(out)
    content=original.read_bytes();digest=sha(original)
    (out/'original-extract-spice.tcl').write_bytes(content)
    (out/'script-provenance.json').write_text(json.dumps(dict(path=str(original),
        expected_sha256=SCRIPT_SHA,observed_sha256=digest,matched=digest==SCRIPT_SHA),indent=2)+'\n')
    if digest!=SCRIPT_SHA:
        raise ValueError('Pinned extraction script changed; original bytes retained for review')


def context_masters(catalog):
    masters=[v['planned_master'] for v in catalog['contexts'].values()]
    if len(set(masters))!=26 or len(masters)!=26 or any(not re.fullmatch(r'wp_r1_[a-z0-9_]+',m) for m in masters):
        raise ValueError('Unexpected context wrappers for original LVS flattening')
    return masters


def prepare(source,out,native_flat=None):
    source,out=(Path(p).resolve() for p in (source,out))
    result=json.loads((source/'result.json').read_text());metrics=result['completed_stage_metrics']
    if (result['passed'] is not False or metrics.get('design__lvs_error__count')!=402
            or any(metrics.get(k)!=0 for k in ['magic__drc_error__count','klayout__drc_error__count','magic__illegal_overlap__count'])
            or sha(source/(NAME+'.gds'))!=GDS_SHA or sha(source/(NAME+'.pnl.v'))!=PNL_SHA):
        raise ValueError('Original assembled failure or qualified geometry changed')
    pins=json.loads((source/'pins.json').read_text())
    if len(pins)!=449 or pins['VPWR']['kind']!='POWER' or pins['VGND']['kind']!='GROUND':
        raise ValueError('Wrong exported macro interface')
    out.mkdir(parents=True,exist_ok=False)
    paths=[Path(__file__),source/'result.json',source/'pins.json',source/'catalog.json',source/(NAME+'.gds'),
           source/(NAME+'.pnl.v'),source/(NAME+'.def'),source/(NAME+'.v')]
    contexts={}
    for case,c in json.loads((source/'catalog.json').read_text())['contexts'].items():
        lef=source/'contexts'/case/(c['planned_master']+'.lef');content=lef.read_text();paths.append(lef)
        names=re.findall(r'^\s*PIN (\S+)\s*$',content,re.M)
        sizes=re.findall(r'^\s*SIZE ([0-9.]+) BY ([0-9.]+) ;\s*$',content,re.M)
        if (len(sizes)!=1 or [int(Decimal(v)*1000) for v in sizes[0]]!=[c['width_dbu'],c['height_dbu']]
                or not names or len(names)!=len(set(names))):
            raise ValueError('Original context LEF interface differs')
        contexts[c['planned_master']]=dict(pins=names,width_dbu=c['width_dbu'],height_dbu=c['height_dbu'])
    context_port_block(contexts)
    native_inventory=None
    if native_flat is not None:
        native_flat=Path(native_flat).resolve()
        native_result=native_flat/'result.json';native_plan=native_flat/'plan.json'
        result=json.loads(native_result.read_text());flat_plan=json.loads(native_plan.read_text())
        expected=dict(import_passed=True,cells=45429,terminals=183701,ports=449,required_signal_nets_with_wires=26431)
        if (any(result.get('import_inventory',{}).get(k)!=v for k,v in expected.items())
                or flat_plan.get('source_assembly_gds_sha256')!=GDS_SHA):
            raise ValueError('Require the matching native flat import inventory')
        native_inventory=native_flat/'expected.json'
        paths.extend([native_inventory,native_result,native_plan,source/'top.json',
            Path(__file__).with_name('flat_topology.py'),Path(__file__).with_name('flat_reference.py')])
        for case,c in json.loads((source/'catalog.json').read_text())['contexts'].items():
            paths.append(source/'contexts'/case/(c['planned_master']+'.nl.v'))
    (out/'plan.json').write_text(json.dumps(dict(source=str(source),expected_ports=sorted(pins),context_ports=contexts,native_inventory=str(native_inventory) if native_inventory else None,
        input_sha256={str(p):sha(p) for p in paths},geometry_changed=False,
        scope='Exported macro interface LVS only. Multiple accesses of declared supply ports require connection by the enclosing power grid; no physical power-grid, clock, timing or submission acceptance.'),indent=2)+'\n')


def inside(out):
    from librelane.flows.classic import Classic
    from librelane.state import State,DesignFormat
    from librelane.steps import Magic,Netgen,Checker
    from cloud_tile_harden import metric_json
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text());source=Path(plan['source'])
    for p,d in plan['input_sha256'].items():
        if sha(p)!=d:raise ValueError('Original assembly view changed')
    original=Path(Magic.SpiceExtraction.get_script_path(None))
    retain_original_script(original,out)
    script=out/'extract_ports.tcl';script.write_text(annotate_script(original.read_text(),plan['expected_ports']))
    all_script=out/'extract_context_ports.tcl'
    all_script.write_text(annotate_script(original.read_text(),plan['expected_ports'],plan['context_ports']))
    flat_script=out/'extract_flat_spice.tcl';flat_script.write_text(flat_spice_script(all_script.read_text()))
    active_script=script
    class ExportPorts(Magic.SpiceExtraction):
        id='Magic.R1ExportPorts'
        def get_script_path(self):return str(active_script)
    class CheckPorts(Classic):
        Steps=[ExportPorts,Checker.IllegalOverlap,Netgen.LVS,Checker.LVS]
    cases={}
    experiments=[('strict_control','all',source/(NAME+'.pnl.v'),False,False),('declared_external_ports','notopports',source/(NAME+'.pnl.v'),False,False)]
    if plan.get('native_inventory'):
        from flat_reference import prepare_and_verify
        liberty=Path(os.environ['PDK_ROOT'])/'ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_slow_1p08V_125C.lib'
        flat_pnl=prepare_and_verify(source,plan['native_inventory'],liberty,out/'flat_reference')
        experiments.append(('flat_native_reference','notopports',flat_pnl,False,False))
        experiments.append(('complete_context_ports','notopports',flat_pnl,True,False))
        experiments.append(('flat_spice_reference','notopports',flat_pnl,True,True))
    for name,unique,pnl,complete,flat in experiments:
        active_script=flat_script if flat else (all_script if complete else script)
        masters=context_masters(json.loads((source/'catalog.json').read_text()))
        config=dict(DESIGN_NAME=NAME,VERILOG_FILES=[str(source/(NAME+'.v'))],
                    CLOCK_PERIOD=20,CLOCK_PORT=None,VDD_NETS=['VPWR'],GND_NETS=['VGND'],
                    PRIMARY_GDSII_STREAMOUT_TOOL='klayout',MAGIC_EXT_USE_GDS=True,
                    MAGIC_EXT_ABSTRACT=False,MAGIC_EXT_UNIQUE=unique,MAGIC_EXT_SHORT_RESISTOR=True,
                    LVS_IGNORE_CELLS=[],LVS_FLATTEN_CELLS=masters)
        row=dict(passed=False,extract_unique=unique,complete_context_ports=complete,flat_spice_export=flat,geometry_changed=False,reference_pnl_sha256=sha(pnl))
        folder=out/name;folder.mkdir(exist_ok=False)
        try:
            flow=CheckPorts(config,design_dir=str(out),pdk='ihp-sg13cmos5l',pdk_root=os.environ['PDK_ROOT'])
            state=State.load({DesignFormat.GDS.id:str(source/(NAME+'.gds')),DesignFormat.DEF.id:str(source/(NAME+'.def')),
                             DesignFormat.POWERED_NETLIST.id:str(pnl)})
            final=flow.start(with_initial_state=state,_force_run_dir=str(folder/'run'))
            row['metrics']=json.loads(json.dumps(final.metrics.to_raw_dict(),default=metric_json))
        except Exception as exc:row['flow_error']=str(exc)
        try:
            reports=list((folder/'run').glob('*/reports/lvs.netgen.rpt'))
            extracted=list((folder/'run').glob('*/'+NAME+'.spice'))
            if len(reports)!=1 or len(extracted)!=1:raise ValueError('Incomplete port extraction/LVS reports')
            portlist=spice_ports(extracted[0].read_text(),NAME)
            row['extracted_ports']=len(portlist)
            row['missing_ports']=sorted(set(plan['expected_ports'])-set(portlist))
            row['extra_ports']=sorted(set(portlist)-set(plan['expected_ports']))
            row['verdicts']=re.findall(r'^Final result:\s*(.+?)\s*$',reports[0].read_text(),re.M)
            strict_verdict(reports[0].read_text(),portlist,plan['expected_ports'])
            if 'flow_error' in row or row['metrics'].get('design__lvs_error__count')!=0:
                raise ValueError('Original LVS checker or metric did not pass')
            row['passed']=True
        except Exception as exc:row['strict_error']=str(exc)
        cases[name]=row
    if any(sha(p)!=d for p,d in plan['input_sha256'].items()):
        raise ValueError('Original assembly changed during extraction')
    chosen=next((n for n in cases if cases[n]['passed']),None)
    summary=dict(passed=chosen is not None,cases=cases,selected_interface_policy=chosen,
        source_gds_sha256=GDS_SHA,source_pnl_sha256=PNL_SHA,geometry_changed=False,
        extraction_script_sha256=sha(script),original_script_sha256=SCRIPT_SHA,
        complete_context_script_sha256=sha(all_script),
        flat_spice_script_sha256=sha(flat_script),
        physical_acceptance=False,timing_acceptance=False,scope=plan['scope'])
    (out/'result.json').write_text(json.dumps(summary,indent=2)+'\n')
    if chosen is None:raise SystemExit('No port extraction policy passed strict macro interface LVS')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--source',type=Path,required=True);prep.add_argument('--out',type=Path,required=True)
    prep.add_argument('--native-flat',type=Path)
    sub.add_parser('inside').add_argument('--out',type=Path,required=True)
    args=vars(p.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else inside)(**args)
