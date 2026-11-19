#!/usr/bin/env python3
"""Prove native channel composition and reject deliberate scratch RTL mutations.
Run with the project venv and OSS CAD Suite on PATH. Artifacts stay in build/.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
SOURCE_FILES=['src/trw_chan_prod.v','src/trw_chan_port.v','src/trw_fabric.v','src/trw_assert.vh',
              'formal/props/channel_composition.sv','formal/channel.sby']
TASKS=['blocking','ready','taps','blocking_cover','tap_cover']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(config,cwd,task,out,expect,engine=None):
    engine = engine or ('abc pdr' if task in ['blocking','ready','taps'] else 'smtbmc z3')
    log=out.with_suffix('.log');out.parent.mkdir(parents=True,exist_ok=True)
    begin=time.monotonic()
    with log.open('w') as stream:
        result=subprocess.run(['sby','-f','-d',str(out),str(config),task],cwd=cwd,
                              stdout=stream,stderr=subprocess.STDOUT,timeout=180)
    status=(out/'status').read_text().split()[0] if (out/'status').exists() else 'MISSING'
    if status!=expect or (expect=='PASS' and result.returncode!=0) or (expect=='FAIL' and result.returncode==0):
        raise RuntimeError(f'{task}: expected {expect}, got {status}/exit{result.returncode}; see {log}')
    text=log.read_text()
    witnesses=sorted(out.rglob('*.vcd'))
    if expect=='FAIL' and not witnesses:raise RuntimeError(f'Mutation has no actual counterexample: {log}')
    if engine=='abc pdr' and expect=='PASS' and 'Property proved.' not in text:
        raise RuntimeError('No unbounded PDR success: '+str(log))
    record={'status':status,'seconds':round(time.monotonic()-begin,3),'log_sha256':sha(log),
            'engine':engine,
            'cover_steps':list(map(int,re.findall(r'reached cover statement .* step (\d+)',text))),
            'witnesses_sha256':{str(p.relative_to(out)):sha(p) for p in witnesses}}
    print(task,expect,record['seconds'],'s',flush=True)
    return record


def mutations():
    # Change only ignored build copies, never src/. Each mutation must be a real
    # semantic FAIL with a counterexample, not ERROR/UNKNOWN or a parse failure.
    return {
      'consume_without_take':('src/trw_chan_port.v','wire took     = avail && take;', 'wire took     = avail;','blocking'),
      'overwrite_full_producer':('src/trw_chan_prod.v','assign load = load_req && free;','assign load = load_req;','blocking'),
      'ignore_one_blocking_subscriber':('src/trw_fabric.v',
          "assign all_taken[8] = (!blk[0] || (sel[3:0] != 4'd4) || (lseq[0] == p_seq[8]))",
          "assign all_taken[8] = 1'b1",'blocking'),
      'corrupt_token':('src/trw_chan_prod.v','tok   <= tok_in;',"tok   <= tok_in ^ 18'd1;",'blocking'),
      'tap_blocks_release':('src/trw_chan_port.v','assign blocking = en && !tap;','assign blocking = en;','taps'),
    }


def main(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    for tool in ['sby','yosys','yosys-abc','z3']:
        if shutil.which(tool) is None:raise RuntimeError('Missing required tool: '+tool)
    before={p:sha(ROOT/p) for p in SOURCE_FILES}
    report={'scope':'Actual native fabric+producer, one HOST_IN producer, four blocking consumers, static accept-all config; channel safety/order and conditional progress; tap noninterference',
            'hardware_changed':False,'source_sha256':before,'proofs':{},'mutation_controls':{},
            'tool_versions':{t:subprocess.check_output(args,text=True).strip() for t,args in {
               'yosys':['yosys','-V'],'sby':['sby','--version'],'z3':['z3','--version']}.items()}}
    for task in TASKS:
        report['proofs'][task]=run('channel.sby',ROOT/'formal',task,output/task,'PASS')
    for name,(file,old,new,task) in mutations().items():
        scratch=output/'mutation_sources'/name
        for rel in SOURCE_FILES:
            target=scratch/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,target)
        target=scratch/file;text=target.read_text()
        if text.count(old)!=1:raise RuntimeError('Mutation anchor missing/ambiguous: '+name)
        target.write_text(text.replace(old,new))
        result=run('channel.sby',scratch/'formal',task,output/('mutation_'+name),'FAIL')
        result['changed_file']=file;result['mutated_source_sha256']=sha(target)
        report['mutation_controls'][name]=result
    assert before=={p:sha(ROOT/p) for p in SOURCE_FILES},'Native source changed during proof run'
    report['native_sources_unchanged']=True
    path=output/'result.json';path.write_text(json.dumps(report,indent=2)+'\n')
    print('Formal channel checks PASS; receipt:',path)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default=str(ROOT/'build/formal_channels'))
    main(parser.parse_args().output)
