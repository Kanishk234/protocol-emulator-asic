"""Qualify exported macro ports without modifying geometry or internal nets."""
import argparse
import json
import os
from pathlib import Path
import re

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


def annotate_script(original,pins):
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
    return original.replace(anchor,anchor+addition)


def retain_original_script(original,out):
    original,out=Path(original),Path(out)
    content=original.read_bytes();digest=sha(original)
    (out/'original-extract-spice.tcl').write_bytes(content)
    (out/'script-provenance.json').write_text(json.dumps(dict(path=str(original),
        expected_sha256=SCRIPT_SHA,observed_sha256=digest,matched=digest==SCRIPT_SHA),indent=2)+'\n')
    if digest!=SCRIPT_SHA:
        raise ValueError('Pinned extraction script changed; original bytes retained for review')


def prepare(source,out):
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
    paths=[Path(__file__),source/'result.json',source/'pins.json',source/(NAME+'.gds'),
           source/(NAME+'.pnl.v'),source/(NAME+'.def'),source/(NAME+'.v')]
    (out/'plan.json').write_text(json.dumps(dict(source=str(source),expected_ports=sorted(pins),
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
    class ExportPorts(Magic.SpiceExtraction):
        id='Magic.R1ExportPorts'
        def get_script_path(self):return str(script)
    class CheckPorts(Classic):
        Steps=[ExportPorts,Checker.IllegalOverlap,Netgen.LVS,Checker.LVS]
    cases={}
    for name,unique in [('strict_control','all'),('declared_external_ports','notopports')]:
        config=dict(DESIGN_NAME=NAME,VERILOG_FILES=[str(source/(NAME+'.v'))],
                    CLOCK_PERIOD=20,CLOCK_PORT=None,VDD_NETS=['VPWR'],GND_NETS=['VGND'],
                    PRIMARY_GDSII_STREAMOUT_TOOL='klayout',MAGIC_EXT_USE_GDS=True,
                    MAGIC_EXT_ABSTRACT=False,MAGIC_EXT_UNIQUE=unique,MAGIC_EXT_SHORT_RESISTOR=True,
                    LVS_IGNORE_CELLS=[])
        row=dict(passed=False,extract_unique=unique,geometry_changed=False)
        folder=out/name;folder.mkdir(exist_ok=False)
        try:
            flow=CheckPorts(config,design_dir=str(out),pdk='ihp-sg13cmos5l',pdk_root=os.environ['PDK_ROOT'])
            state=State.load({DesignFormat.GDS.id:str(source/(NAME+'.gds')),DesignFormat.DEF.id:str(source/(NAME+'.def')),
                             DesignFormat.POWERED_NETLIST.id:str(source/(NAME+'.pnl.v'))})
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
    chosen=next((n for n in ('strict_control','declared_external_ports') if cases[n]['passed']),None)
    summary=dict(passed=chosen is not None,cases=cases,selected_interface_policy=chosen,
        source_gds_sha256=GDS_SHA,source_pnl_sha256=PNL_SHA,geometry_changed=False,
        extraction_script_sha256=sha(script),original_script_sha256=SCRIPT_SHA,
        physical_acceptance=False,timing_acceptance=False,scope=plan['scope'])
    (out/'result.json').write_text(json.dumps(summary,indent=2)+'\n')
    if chosen is None:raise SystemExit('No port extraction policy passed strict macro interface LVS')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--source',type=Path,required=True);prep.add_argument('--out',type=Path,required=True)
    sub.add_parser('inside').add_argument('--out',type=Path,required=True)
    args=vars(p.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else inside)(**args)
