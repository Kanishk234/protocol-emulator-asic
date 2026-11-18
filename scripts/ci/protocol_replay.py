"""Replay the existing protocol suite on an official GDS submission, with exact coverage receipts."""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import xml.etree.ElementTree as ET

SHARDS={
    'serial': ['uart_tx','uart_rx_framing','midi_tx','spi_controller','i2c_controller','spi_target','i2c_target'],
    'pulse': ['dmx_tx','ws2812_tx','dshot_tx','servo_pwm'],
    'debug': ['ps2_device_to_host','ps2_host_to_device','onewire_read_rom','jtag_idcode','smbus_word_pec','swd_dpidr_read_with_wait_retry'],
    'frames': ['i2s','hdlc_tx_loopback','lin_commander_publish_response','can_standard_frame_and_ack','ir_nec_repeat_rx'],
}
SHARDS={k:['test_l3_'+n for n in v] for k,v in SHARDS.items()}
ALL_TESTS={n for v in SHARDS.values() for n in v}

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check_xml(path,shard):
    expected=set(SHARDS[shard]);seen={}
    for case in ET.parse(path).getroot().iter('testcase'):
        name=case.attrib['name'].rsplit('.',1)[-1]
        if case.get('classname')!='test_l3':raise ValueError('Wrong protocol module')
        if name not in ALL_TESTS or name in seen:raise ValueError('Unknown/duplicate replay case')
        seen[name]=case
        bad=case.find('failure') is not None or case.find('error') is not None
        skipped=case.find('skipped') is not None
        if bad or (name in expected and skipped) or (name not in expected and not skipped):
            raise ValueError('Failed/skipped selected case or unplanned execution: '+name)
    if any((not math.isfinite(float(seen[n].get('sim_time_ns','0'))) or float(seen[n].get('sim_time_ns','0'))<=0) for n in expected if n in seen):raise ValueError('Selected case did not simulate')
    if not expected.issubset(seen):raise ValueError('Missing selected protocol case')
    return dict(shard=shard,passed=sorted(expected),selected_count=len(expected),
                selected_failures=0,selected_skips=0,xml_sha256=digest(path),
                unselected_skips=sum(c.find('skipped') is not None for n,c in seen.items() if n not in expected))


def shell_filter(shard):
    # Cocotb 2.0.1 expands this variable unquoted into its shell recipe.
    # Keep shell quotes in the Make variable so the simulator receives the regex.
    pattern=r'^test_l3\.(?:'+'|'.join(map(re.escape,SHARDS[shard]))+r')$'
    return shlex.quote(pattern).replace("$", "$$")



def validate_metadata(run,commit):
    if (run.get('status')!='completed' or run.get('conclusion')!='success'
            or run.get('head_branch')!='main' or run.get('path')!='.github/workflows/gds.yaml'
            or run.get('head_sha')!=commit.get('commit')
            or not re.fullmatch(r'[0-9a-f]{40}',str(run.get('head_sha','')))):
        raise ValueError('Submission is not the selected successful official main run')
    if not str(commit.get('workflow_url','')).endswith('/runs/'+str(run['id'])):
        raise ValueError('Submission workflow identity differs')


def prepare(candidate,submission,run,pdk_root,work):
    import yaml
    candidate,submission,pdk_root,work=map(Path,(candidate,submission,pdk_root,work))
    package=submission/'tt_submission'
    commit=json.loads((package/'commit_id.json').read_text())
    validate_metadata(run,commit)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=candidate,text=True).strip()
    if head!=run['head_sha']:raise ValueError('Candidate software differs from official source revision')
    pdk=json.loads((package/'pdk.json').read_text())
    if pdk.get('PDK')!='ihp-sg13cmos5l':raise ValueError('Wrong submission PDK')
    suite=candidate/'test_internal/chip/test_l3.py'
    names={n.name for n in ast.parse(suite.read_text()).body if isinstance(n,ast.AsyncFunctionDef) and any(isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and d.func.attr=='test' for d in n.decorator_list)}
    if names!=ALL_TESTS:raise ValueError('Update reviewed protocol coverage/shards for changed test suite')
    spec=yaml.safe_load((candidate/'spec/tripwire.yaml').read_text())
    if spec['fabric']['lanes']!=2 or spec['fabric']['units']!=4:raise ValueError('Unreviewed resource profile')
    cells=pdk_root/'ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/verilog'
    macro=candidate/'macro/RM_IHPSG13_1P_512x16_c2_bm_bist'
    models=[cells/'sg13cmos5l_stdcell.v',cells/'sg13cmos5l_udp.v',macro/'RM_IHPSG13_1P_core_behavioral_bm_bist.v',macro/'RM_IHPSG13_1P_512x16_c2_bm_bist.v']
    netlist=package/'tt_um_tripwire.v'
    if run['id']==44189196098 and digest(netlist)!='537f41adee4320df81a0b7e907f011510cc578ab3c2a17105e00a80e0bacbcc9':raise ValueError('Golden netlist hash mismatch')
    masters=set(re.findall(r'\b(sg13cmos5l_\w+|RM_IHPSG13_\w+)\s+\\?\S+\s*\(',netlist.read_text()))
    definitions={n for p in models for n in re.findall(r'\b(?:module|primitive)\s+(\w+)',p.read_text())}
    if not masters or masters-definitions:raise ValueError('Missing gate-level cell models')
    identity=dict(official_run=run['id'],source_sha=head,netlist_sha256=digest(netlist),pdk=pdk,
                  model_hashes={p.name:digest(p) for p in models},suite_sha256=digest(suite),
                  software_tables_sha256=digest(candidate/'tools/tripwire_spec.py'),
                  simulator='Tiny Tapeout Icarus 13',sigrok_required=True,sdf_annotated=False)
    work.mkdir(parents=True,exist_ok=True)
    (work/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
    sources=[*models,netlist,candidate/'test_internal/chip/tb_chip_gl.v']
    (work/'compile.json').write_text(json.dumps({'verilog_sources':[str(p.resolve()) for p in sources]},indent=2)+'\n')
    return identity


def aggregate(results,output):
    results,output=Path(results),Path(output);seen=set();identities=[]
    combined=ET.Element('testsuite',name='full-routed-protocol-suite',tests='22',failures='0',errors='0',skipped='0')
    for shard in SHARDS:
        xmls=list(results.rglob('results_'+shard+'.xml'));receipts=list(results.rglob('receipt_'+shard+'.json'))
        if len(xmls)!=1 or len(receipts)!=1:raise ValueError('Missing/duplicate shard results')
        row=check_xml(xmls[0],shard);receipt=json.loads(receipts[0].read_text())
        if row!=receipt['results']:raise ValueError('Receipt/XML mismatch')
        identity=receipt['identity']
        if identity.get('sigrok_required') is not True or identity.get('simulator')!='Tiny Tapeout Icarus 13' or len(identity.get('model_hashes',{}))!=4:
            raise ValueError('Missing replay environment provenance')
        identities.append(identity)
        for case in ET.parse(xmls[0]).getroot().iter('testcase'):
            name=case.get('name','').rsplit('.',1)[-1]
            if name in SHARDS[shard]:
                if name in seen:raise ValueError('Repeated execution')
                seen.add(name);combined.append(case)
    if seen!=ALL_TESTS or any(i!=identities[0] for i in identities):raise ValueError('Coverage/input identity differs')
    output.mkdir(parents=True,exist_ok=True)
    ET.ElementTree(combined).write(output/'results.xml',encoding='unicode')
    row=dict(passed=22,failed=0,skipped=0,identity=identities[0],functional_gate_level_only=True)
    (output/'summary.json').write_text(json.dumps(row,indent=2)+'\n')
    return row


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['filter','prepare','receipt','aggregate'])
    p.add_argument('--shard',choices=tuple(SHARDS));p.add_argument('--candidate',default='candidate');p.add_argument('--submission',default='submission')
    p.add_argument('--pdk-root');p.add_argument('--metadata',default='build/protocol-replay/source-run.json')
    args=p.parse_args();work=Path('build/protocol-replay')
    if args.stage=='filter':
        if not args.shard:p.error('--shard required')
        print(shell_filter(args.shard));return
    if args.stage=='prepare':
        if not args.pdk_root:p.error('--pdk-root required')
        print(json.dumps(prepare(args.candidate,args.submission,json.loads(Path(args.metadata).read_text()),args.pdk_root,work),indent=2));return
    if args.stage=='aggregate':print(json.dumps(aggregate('build/shard-results',work/'full-suite'),indent=2));return
    if not args.shard:p.error('--shard required')
    import os
    if not shutil.which('sigrok-cli') or os.environ.get('TRIPWIRE_SKIP_SIGROK')=='1':raise ValueError('Independent decoding must remain enabled')
    identity=json.loads((work/'identity.json').read_text());result=check_xml(work/f'results_{args.shard}.xml',args.shard)
    (work/f'receipt_{args.shard}.json').write_text(json.dumps({'identity':identity,'results':result},indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
