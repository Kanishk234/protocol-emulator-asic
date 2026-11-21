#!/usr/bin/env python3
"""Instrument ignored native RTL copies and check pin-unit sticky integration.
Default: lean proofs/covers and fault controls. --full also attempts the open
full/BITSYNC proofs; timeout or failure is not accepted as proof.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from formal_channels import ROOT, run, sha

FILES=['src/trw_defs.vh','src/trw_assert.vh','src/trw_pin_unit.v','src/trw_pin_io.v',
       'src/trw_pin_rx.v','src/trw_pin_tx.v','src/trw_pin_bs.v','formal/pin_unit.sby',
       'formal/props/pin_unit_flags.vh','formal/props/pin_bs_overrun.vh']
INSERTIONS={'src/trw_pin_unit.v':'pin_unit_flags.vh','src/trw_pin_bs.v':'pin_bs_overrun.vh'}
MUTATIONS={
 'clear_beats_set':('overrun <= ovr_set || (overrun && !clr_overrun);','overrun <= (ovr_set || overrun) && !clr_overrun;'),
 'forget_sticky_overrun':('overrun <= ovr_set || (overrun && !clr_overrun);','overrun <= ovr_set;'),
 'ignore_overrun_clear':('overrun <= ovr_set || (overrun && !clr_overrun);','overrun <= ovr_set || overrun;'),
 'ignore_restart':('if (!rst_n || restart) begin','if (!rst_n) begin'),
 'corrupt_rx_merge':('assign rx_data = load_h ? data_h : data_b;',"assign rx_data = (load_h ? data_h : data_b) ^ 16'd1;"),
}


def prepare(path, *, bitsync_source=None):
    for rel in FILES:
        target=path/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,target)
    if bitsync_source is not None:
        (path/'src/trw_pin_bs.v').write_bytes(bitsync_source)
    for rel,include in INSERTIONS.items():
        target=path/rel;text=target.read_text()
        if text.count('endmodule')!=1:raise RuntimeError('Unexpected module shape: '+rel)
        updated=text.replace('endmodule',f'`include "{include}"\nendmodule')
        assert updated.replace(f'`include "{include}"\n','')==text
        target.write_text(updated)
    return path/'formal'


def main(output,full):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    for tool in ['sby','yosys','yosys-abc','z3']:
        if shutil.which(tool) is None:raise RuntimeError('Missing required tool: '+tool)
    before={p:sha(ROOT/p) for p in FILES}
    cwd=prepare(output/'native')
    report={'scope':'Native lean pin-unit sticky flags and RX merge; static cfg, legal period, monotonic live, stable pending TX; full/BITSYNC proof open',
            'hardware_changed':False,'source_sha256':before,'runner_sha256':sha(__file__),
            'shared_runner_sha256':sha(ROOT/'scripts/formal_channels.py'),'proofs':{},'mutation_controls':{},
            'tool_versions':{t:subprocess.check_output(args,text=True).strip() for t,args in {
                'yosys':['yosys','-V'],'sby':['sby','--version'],'z3':['z3','--version']}.items()}}
    tasks=[('lean','abc pdr'),('lean_qualified','abc pdr'),('lean_cover','smtbmc z3'),('lean_qualified_cover','smtbmc z3')]
    if full:tasks += [('full','abc pdr'),('qualified','abc pdr'),('full_cover','smtbmc z3'),('qualified_cover','smtbmc z3')]
    for task,engine in tasks:
        report['proofs'][task]=run('pin_unit.sby',cwd,task,output/task,'PASS',engine)
    for name,(old,new) in MUTATIONS.items():
        scratch=output/'mutation_sources'/name;mcwd=prepare(scratch)
        target=scratch/'src/trw_pin_unit.v';text=target.read_text()
        if text.count(old)!=1:raise RuntimeError('Mutation anchor missing/ambiguous: '+name)
        target.write_text(text.replace(old,new))
        result=run('pin_unit.sby',mcwd,'lean',output/('mutation_'+name),'FAIL','abc pdr')
        if 'pin_unit_flags.vh' not in (output/('mutation_'+name+'.log')).read_text():
            raise RuntimeError('Missing targeted integration assertion evidence')
        result['mutated_source_sha256']=sha(target);report['mutation_controls'][name]=result
    assert before=={p:sha(ROOT/p) for p in FILES},'Native source changed during proof run'
    report['native_sources_unchanged']=True
    path=output/'result.json';path.write_text(json.dumps(report,indent=2)+'\n')
    print('Pin-unit scoped checks PASS; receipt:',path)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default=str(ROOT/'build/formal_pin_unit'))
    parser.add_argument('--full',action='store_true')
    main(**vars(parser.parse_args()))
