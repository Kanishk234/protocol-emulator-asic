"""Bind all 22 protocol cases to the exact clean extracted post-fill netlist."""
import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

from cache_final_route import (SOURCE_RUN, SOURCE_SHA, SOURCE_WORKFLOW, RUNNER_ROOT,
                               inspect_saved, local_view, extracted_failures)
from electrical_report import audit_corners
from event_nor2_screen import logical_cells, validate_antenna_only_changes
from extracted_timing import check_stock_report_uncertainty
from functional_setup_frontier import parse_report
from postgrt_timing import CORNERS
from sram_bank_clean_route import unique

ROUTE_RUN=44031468510
ROUTE_SHA='c5824b6ba259155a312a92a8fa545d8319e1e9a9'
ROUTE_WORKFLOW='.github/workflows/gds-cache-final-route-extracted.yaml'
ROUTED_ODB_SHA='357f01366aea053ca83db4b035625033424378aecc5ff17addaf4711421b00d4'
ROUTED_NL_SHA='1eb51e9e35f1006d3599b528d244d251e5fa495e1e0d821264707dbf35581867'
FINAL_NL_SHA='537f41adee4320df81a0b7e907f011510cc578ab3c2a17105e00a80e0bacbcc9'
SHARDS={
    'serial': ['uart_tx','uart_rx_framing','midi_tx','spi_controller','i2c_controller','spi_target','i2c_target'],
    'pulse': ['dmx_tx','ws2812_tx','dshot_tx','servo_pwm'],
    'debug': ['ps2_device_to_host','ps2_host_to_device','onewire_read_rom','jtag_idcode','smbus_word_pec','swd_dpidr_read_with_wait_retry'],
    'frames': ['i2s','hdlc_tx_loopback','lin_commander_publish_response','can_standard_frame_and_ack','ir_nec_repeat_rx'],
}
SHARDS={k:['test_l3_'+n for n in v] for k,v in SHARDS.items()}
ALL_TESTS={n for v in SHARDS.values() for n in v}


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def validate_route_metadata(run):
    expected=dict(id=ROUTE_RUN,head_sha=ROUTE_SHA,head_branch='main',conclusion='success',path=ROUTE_WORKFLOW)
    if any(run.get(k)!=v for k,v in expected.items()):raise ValueError('Wrong successful route/extraction workflow')


def validate_artifacts(source,route,extracted,run):
    source,route,extracted=map(Path,(source,route,extracted))
    validate_route_metadata(run);inspect_saved(source)
    drt=unique(route/'runs/cache-final-route','*-openroad-detailedrouting/state_out.json')
    state=json.loads(drt.read_text());completion=json.loads((drt.parent.parent/'route_completion.json').read_text())
    if (completion.get('completed') is not True or completion.get('route_drc_errors')!=0
            or completion.get('source_run')!=SOURCE_RUN or completion.get('source_sha')!=SOURCE_SHA
            or completion.get('workflow_run_id')!=str(ROUTE_RUN)):
        raise ValueError('Wrong completed-route identity')
    odb,nl=local_view(route,state['odb']),local_view(route,state['nl'])
    if digest(odb)!=ROUTED_ODB_SHA or digest(nl)!=ROUTED_NL_SHA:
        raise ValueError('Changed independently reviewed routed DB/netlist')
    if completion.get('routed_odb_sha256')!=ROUTED_ODB_SHA or completion.get('routed_nl_sha256')!=ROUTED_NL_SHA:
        raise ValueError('Route completion hash mismatch')
    raw=json.loads((drt.parent/'or_metrics_out.json').read_text())
    if any(type(v) is not int or v!=0 for v in (state['metrics'].get('route__drc_errors'),raw.get('route__drc_errors'))):
        raise ValueError('Route lacks fresh DRC0')
    gates=json.loads((source/'runs/stock-corner-audit/screen_qualification.json').read_text())
    srcstate=json.loads(local_view(source,gates['source_state']).read_text())
    validate_antenna_only_changes(local_view(source,srcstate['nl']).read_text(),nl.read_text())
    root=extracted/'runs/extracted-timing'
    sta=unique(root,'*-openroad-stapostpnr/state_out.json')
    finalstate=json.loads(sta.read_text())
    final=local_view(extracted,finalstate['nl'])
    if digest(final)!=FINAL_NL_SHA or logical_cells(nl.read_text())!=logical_cells(final.read_text()):
        raise ValueError('Final extracted netlist differs from reviewed routed logic')
    initial=json.loads(unique(root,'*-odb-removeroutingobstructions/state_in.json').read_text())
    if initial['odb']!=state['odb']:raise ValueError('Extraction uses a different routed database')
    summary=json.loads((root/'corner_summary.json').read_text())
    functional={}
    for c in CORNERS:
        d=sta.parent/c
        for name in ('max.rpt','min.rpt'):check_stock_report_uncertainty((d/name).read_text())
        functional[c]=parse_report((d/'functional_setup_frontier.rpt').read_text(),c)
        for kind,suffix in (('setup','max'),('hold','min')):
            report=(d/f'ws.{suffix}.rpt').read_text()
            values=re.findall(r'^'+re.escape(c)+r':\s*(\S+)\s*$',report,re.M)
            key=f'timing__{kind}__ws__corner:{c}'
            if len(values)!=1 or not math.isfinite(float(values[0])) or abs(float(values[0])-summary[key])>1e-12:
                raise ValueError('Extracted worst-slack summary/report mismatch')
    if functional!=json.loads((root/'functional_setup.json').read_text()):raise ValueError('Functional summary differs from reports')
    if any(finalstate['metrics'].get(k)!=v for k,v in summary.items()):raise ValueError('Timing metrics differ from final STA')
    electrical=audit_corners(sta.parent,CORNERS)
    if electrical!=json.loads((root/'electrical_summary.json').read_text()):raise ValueError('Electrical summary differs from reports')
    antenna=json.loads(unique(root,'*-openroad-checkantennas/or_metrics_out.json').read_text())
    expected={c:r['endpoint_inventory'] for c,r in gates['functional_setup'].items()}
    failures=extracted_failures(summary,functional,electrical,antenna,expected)
    passed=json.loads((extracted/'runs/cache-final-extracted-gates.json').read_text())
    if failures or passed.get('qualified') is not True or passed.get('failures')!=[]:
        raise ValueError('Independent extracted gates fail: '+str(failures))
    if (passed['extracted_timing']!=summary or passed['functional_setup']!=functional
            or passed['electrical']!=electrical or passed['antenna']!=antenna):
        raise ValueError('Extracted qualification differs from raw evidence')
    identity=json.loads((root/'constraint_identity.json').read_text())
    effective=root/'effective-stock-signoff.sdc'
    if (identity.get('policy')!='stock-native-base-sdc' or identity.get('clock_uncertainty_ns')!=.25
            or identity.get('legacy_source_sdc_used') is not False or digest(effective)!=identity['sha256']
            or effective.read_text()!='source $::env(SCRIPTS_DIR)/base.sdc\n'):
        raise ValueError('Stock extraction constraint identity fails')
    return dict(source_run=SOURCE_RUN,route_run=ROUTE_RUN,netlist=str(final.resolve()),
                netlist_sha256=FINAL_NL_SHA,routed_odb_sha256=ROUTED_ODB_SHA,
                extracted_gates_independently_verified=True,full_protocol_replay_complete=False,
                official_gds_signoff=False)


def suite_names(path):
    tree=ast.parse(Path(path).read_text())
    names={n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
           and any(isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and d.func.attr=='test' for d in n.decorator_list)}
    if names!=ALL_TESTS or sum(map(len,SHARDS.values()))!=22:raise ValueError('Protocol suite/shard coverage changed')
    if digest(path)!='bfd414a15fb5094b7ae2e2fc383c2dd770b409026681404f5a4d012415ef3339':
        raise ValueError('Protocol test implementation changed without review')
    return names


def prepare_replay(root,source,destination):
    """Generate software/encoding tables from an isolated 2/4 spec; never alter frozen RTL."""
    root,source,destination=map(Path,(root,source,destination))
    if destination.exists():raise ValueError('Replay tree already exists')
    destination.mkdir(parents=True)
    files=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
    exact={'spec/tripwire.yaml','docs/design/ISA.md','docs/design/ARCHITECTURE.md'}
    for name in files:
        if name and (name.startswith(('tools/','programs/','test_internal/chip/')) or name in exact):
            target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,target)
    import yaml
    p=destination/'spec/tripwire.yaml';spec=yaml.safe_load(p.read_text())
    spec['fabric'].update(lanes=2,units=4)
    spec['pin_config']['units']=[['pulse','carrier','bitsync'],[],[],[]]
    counts={'unit_flags':4,'ports':9,'dropped':9,'pin_cfg':128,'lanes':64}
    for entry in spec['host_map']['entries']:
        if entry['name'] in counts:entry['count']=counts[entry['name']]
    p.write_text(yaml.safe_dump(spec,sort_keys=False,allow_unicode=True))
    subprocess.run([sys.executable,str(destination/'tools/gen/gen.py')],check=True)
    for name in ('trw_defs.vh','trw_fabric.v'):
        if (destination/'src'/name).read_bytes()!=(source/'src'/name).read_bytes():
            raise ValueError('Generated replay encodings do not match screened RTL: '+name)
    suite_names(destination/'test_internal/chip/test_l3.py')
    return dict(lanes=2,units=4,full_units=[0],spec_sha256=digest(p),
                python_tables_sha256=digest(destination/'tools/tripwire_spec.py'),
                protocol_suite_sha256=digest(destination/'test_internal/chip/test_l3.py'),
                expected_tests=22,rtl_regenerated_for_simulation=False)


def check_xml(path,shard):
    expected=set(SHARDS[shard]);seen={}
    for case in ET.parse(path).getroot().iter('testcase'):
        name=case.attrib['name'].rsplit('.',1)[-1]
        if name not in ALL_TESTS or name in seen:raise ValueError('Unknown/duplicate replay case')
        seen[name]=case
        bad=case.find('failure') is not None or case.find('error') is not None
        skipped=case.find('skipped') is not None
        if bad or (name in expected and skipped) or (name not in expected and not skipped):
            raise ValueError('Failed/skipped selected case or unplanned execution: '+name)
    if not expected.issubset(seen):raise ValueError('Missing selected protocol case')
    return dict(shard=shard,passed=sorted(expected),selected_count=len(expected),
                selected_failures=0,selected_skips=0,xml_sha256=digest(path),
                unselected_skips=sum(c.find('skipped') is not None for n,c in seen.items() if n not in expected))


def aggregate(results,output):
    results,output=Path(results),Path(output);output.mkdir(parents=True,exist_ok=True)
    combined=ET.Element('testsuite',name='full-routed-protocol-suite',tests='22',failures='0',errors='0',skipped='0')
    seen=set();identities=[]
    for shard in SHARDS:
        xmls=list(results.rglob('results_'+shard+'.xml'))
        receipts=list(results.rglob('receipt_'+shard+'.json'))
        if len(xmls)!=1 or len(receipts)!=1:raise ValueError('Missing/duplicate shard results')
        row=check_xml(xmls[0],shard);receipt=json.loads(receipts[0].read_text())
        if receipt['results']!=row:raise ValueError('Shard receipt differs from XML')
        identity=receipt['identity']
        if identity['netlist_sha256']!=FINAL_NL_SHA or identity['route_run']!=ROUTE_RUN:raise ValueError('Wrong replay netlist identity')
        if (identity.get('sigrok_required') is not True or identity.get('simulator')!='Icarus Verilog 13'
                or identity.get('model_pdk_revision')!='89d42ee6d2fd9b50b86a1aada6fee6673c3e6008'
                or len(identity.get('model_hashes',{}))!=4
                or identity.get('replay',{}).get('expected_tests')!=22):
            raise ValueError('Missing exact replay environment provenance')
        identities.append(identity)
        for c in ET.parse(xmls[0]).getroot().iter('testcase'):
            name=c.attrib['name'].rsplit('.',1)[-1]
            if name in SHARDS[shard]:
                if name in seen:raise ValueError('Duplicate selected execution across shards')
                seen.add(name);combined.append(c)
    if seen!=ALL_TESTS or any(i!=identities[0] for i in identities):raise ValueError('Incomplete coverage or mismatched shard inputs')
    ET.ElementTree(combined).write(output/'results_full_suite.xml',encoding='unicode')
    result=dict(passed=22,failed=0,unexecuted=0,selected_skips=0,identity=identities[0],
                full_protocol_replay_complete=True,functional_gate_level_only=True,
                sdf_annotated_simulation=False,official_gds_signoff=False)
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


def prepare_models(root,pdk,identity):
    root,pdk=Path(root),Path(pdk)
    if pdk.name!='89d42ee6d2fd9b50b86a1aada6fee6673c3e6008':raise ValueError('Wrong model PDK revision')
    cells=pdk/'ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/verilog'
    macro=root/'macro/RM_IHPSG13_1P_512x16_c2_bm_bist'
    models=[cells/'sg13cmos5l_stdcell.v',cells/'sg13cmos5l_udp.v',
            macro/'RM_IHPSG13_1P_core_behavioral_bm_bist.v',macro/'RM_IHPSG13_1P_512x16_c2_bm_bist.v']
    if any(not p.is_file() for p in models):raise ValueError('Missing exact PDK/SRAM functional models')
    definitions={name for p in models for name in re.findall(r'\b(?:module|primitive)\s+(\w+)',p.read_text())}
    nl=Path(identity['netlist'])
    if digest(nl)!=FINAL_NL_SHA:raise ValueError('Changed replay netlist')
    masters=set(re.findall(r'\b(sg13cmos5l_\w+|RM_IHPSG13_\w+)\s+\\?\S+\s*\(',nl.read_text()))
    if not masters or masters-definitions:raise ValueError('Unmodeled routed cells: '+str(sorted(masters-definitions)))
    identity.update(model_pdk_revision=pdk.name,model_hashes={p.name:digest(p) for p in models},
                    sigrok_required=True,simulator='Icarus Verilog 13',functional_gate_level_only=True,
                    sdf_annotated_simulation=False)
    identity.pop('full_protocol_replay_complete',None)
    sources=[*models,nl,root/'replay/test_internal/chip/tb_chip_gl.v']
    (root/'replay_compile.json').write_text(json.dumps({'verilog_sources':[str(p.resolve()) for p in sources]},indent=2)+'\n')
    return identity


def main():
    import argparse
    import os
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=('admit','models','filter','receipt','aggregate'))
    parser.add_argument('--shard',choices=tuple(SHARDS))
    args=parser.parse_args()
    root=Path.cwd()
    identity_path=root/'native-gl-identity.json'
    if args.stage=='admit':
        from cache_final_route import validate_metadata
        validate_metadata(json.loads(Path('official-dev4-source-run.json').read_text()))
        row=validate_artifacts(root,Path('route-artifact'),Path('extracted-artifact'),
                               json.loads(Path('route-source-run.json').read_text()))
        row['replay']=prepare_replay(root,root,root/'replay')
        identity_path.write_text(json.dumps(row,indent=2)+'\n')
        print(json.dumps(row,indent=2))
    elif args.stage=='models':
        from cache_final_route import verify_source,bootstrap
        source,config=verify_source()
        pdk=bootstrap(config,source,'cache-final-gl-pdk')
        row=prepare_models(root,pdk,json.loads(identity_path.read_text()))
        identity_path.write_text(json.dumps(row,indent=2)+'\n')
        print(json.dumps(row,indent=2))
    elif args.stage=='filter':
        if args.shard is None:raise ValueError('Missing shard')
        print(r'^test_l3\.(?:'+'|'.join(map(re.escape,SHARDS[args.shard]))+r')$')
    elif args.stage=='receipt':
        if args.shard is None:raise ValueError('Missing shard')
        if os.environ.get('TRIPWIRE_SKIP_SIGROK')=='1' or shutil.which('sigrok-cli') is None:
            raise ValueError('Independent sigrok decoding must remain enabled')
        row=check_xml(root/f'results_{args.shard}.xml',args.shard)
        identity=json.loads(identity_path.read_text())
        if not identity.get('sigrok_required') or identity.get('model_pdk_revision')!='89d42ee6d2fd9b50b86a1aada6fee6673c3e6008':
            raise ValueError('Missing simulator/model provenance')
        (root/f'receipt_{args.shard}.json').write_text(json.dumps({'results':row,'identity':identity},indent=2)+'\n')
        print(json.dumps(row,indent=2))
    else:aggregate(root/'shard-results',root/'full-suite-results')


if __name__=='__main__':main()
