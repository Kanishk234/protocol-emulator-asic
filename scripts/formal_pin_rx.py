#!/usr/bin/env python3
"""Prove native RX overrun preservation; reject scratch RTL fault controls."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from formal_channels import ROOT, run, sha

FILES=['src/trw_chan_prod.v','src/trw_pin_rx.v','src/trw_assert.vh','src/trw_defs.vh',
       'formal/props/pin_rx_overrun.sv','formal/pin_rx.sby']
MUTATIONS={
    'suppress_overrun':('src/trw_pin_rx.v','assign ovr_set = live && ((want && !rx_free) || (ev && emit) || smp_lost);',
                        'assign ovr_set = live && ((ev && emit) || smp_lost);'),
    'rx_requests_while_full':('src/trw_pin_rx.v','assign rx_load = live && want && rx_free;',
                             'assign rx_load = live && want;'),
    'erase_blocked_token':('src/trw_chan_prod.v','tok   <= tok_in;',
                           "tok   <= tok_in;\n        end else if (!free) begin\n            tok <= 18'd0;"),
    'lose_event_completion':('src/trw_pin_rx.v','wire want = ev || emit;','wire want = emit;'),
    'corrupt_accepted_token':('src/trw_chan_prod.v','tok   <= tok_in;',"tok   <= tok_in ^ 18'd1;"),
}


def prepare(root, scratch):
    for rel in FILES:
        target = scratch / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / rel, target)
    rx = (scratch / 'src/trw_pin_rx.v').read_text()
    if 'input  wire        b_rise,' in rx and 'input  wire        b_fall,' in rx:
        config = scratch / 'formal/pin_rx.sby'
        config.write_text(config.read_text().replace(
            'read -formal -sv', 'read -formal -sv -DTRW_RX_SHARED_EDGES', 1))


def main(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    for tool in ['sby','yosys','yosys-abc','z3']:
        if shutil.which(tool) is None:raise RuntimeError('Missing required tool: '+tool)
    before={p:sha(ROOT/p) for p in FILES}
    report={'scope':'Native pin RX + producer; symbolic configuration, synchronized pins, TX commands and release; initial reset then deasserted; overrun output not sticky unit flag',
            'hardware_changed':False,'source_sha256':before,'runner_sha256':sha(__file__),
            'shared_runner_sha256':sha(ROOT/'scripts/formal_channels.py'),'proofs':{},'mutation_controls':{},
            'tool_versions':{t:subprocess.check_output(args,text=True).strip() for t,args in {
                'yosys':['yosys','-V'],'sby':['sby','--version'],'z3':['z3','--version']}.items()}}
    scratch = output / 'native_sources'
    prepare(ROOT, scratch)
    for task,engine in [('safety','abc pdr'),('reachable','smtbmc z3')]:
        report['proofs'][task]=run('pin_rx.sby',scratch/'formal',task,output/task,'PASS',engine)
    for name,(file,old,new) in MUTATIONS.items():
        scratch=output/'mutation_sources'/name
        prepare(ROOT, scratch)
        target=scratch/file;text=target.read_text()
        if text.count(old)!=1:raise RuntimeError('Mutation anchor missing/ambiguous: '+name)
        target.write_text(text.replace(old,new))
        result=run('pin_rx.sby',scratch/'formal','safety',output/('mutation_'+name),'FAIL','abc pdr')
        result['changed_file']=file;result['mutated_source_sha256']=sha(target)
        report['mutation_controls'][name]=result
    assert before=={p:sha(ROOT/p) for p in FILES},'Native source changed during proof run'
    report['native_sources_unchanged']=True
    path=output/'result.json';path.write_text(json.dumps(report,indent=2)+'\n')
    print('Formal RX checks PASS; receipt:',path)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default=str(ROOT/'build/formal_pin_rx'))
    main(parser.parse_args().output)
