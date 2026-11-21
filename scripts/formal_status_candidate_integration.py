#!/usr/bin/env python3
"""Attempt full pin-unit proof on the scratch candidate; no source adoption."""
import json
import shutil
import subprocess
from formal_channels import ROOT, run, sha
from formal_pin_unit import FILES, prepare
from formal_status_queue import PATCH, verified_sources


def main():
    output=ROOT/'build/formal_status_candidate_integration';scratch=output/'native'
    before={p:sha(ROOT/p) for p in FILES}
    _, candidate = verified_sources(ROOT/'src/trw_pin_bs.v')
    cwd = prepare(scratch, bitsync_source=candidate)
    # The candidate can enqueue the second new status after directly loading the
    # first. Update the historical transition check; the independent list oracle
    # separately checks which token should remain, exact loss, and full priority.
    prop=cwd/'props/pin_bs_overrun.vh';text=prop.read_text();assert text.count('$past(st_nd)')==1
    prop.write_text(text.replace('$past(st_nd)','$past(st_wait_data)'))
    ref=ROOT/'formal/props/status_queue_reference.vh';shutil.copyfile(ref,cwd/'props'/ref.name)
    source=scratch/'src/trw_pin_bs.v';text=source.read_text();assert text.count('endmodule')==1
    source.write_text(text.replace('endmodule','`include "status_queue_reference.vh"\nendmodule'))
    config=cwd/'pin_unit.sby';text=config.read_text();text+='props/status_queue_reference.vh\n';config.write_text(text)
    report={'scope':'Actual candidate full pin unit with qualified cache parameters and explicit static interface premises; all native assertions and independent queue oracle enabled',
            'runner_sha256':sha(__file__),'source_sha256':before,'helper_sha256':{p:sha(ROOT/p) for p in ['scripts/formal_pin_unit.py','scripts/formal_channels.py','scripts/formal_status_queue.py']},'tool_versions':{t:subprocess.check_output(args,text=True).strip() for t,args in {'yosys':['yosys','-V'],'sby':['sby','--version'],'z3':['z3','--version']}.items()},'patch_sha256':sha(PATCH),'queue_oracle_sha256':sha(ref),
            'artifact_source_sha256':{str(p.relative_to(scratch)):sha(p) for p in sorted(scratch.rglob('*')) if p.is_file()},'proofs':{},'adopted':False}
    for task,engine in [('qualified','abc pdr'),('qualified_cover','smtbmc z3')]:
        try:report['proofs'][task]=run('pin_unit.sby',cwd,task,output/task,'PASS',engine)
        except RuntimeError as error:
            status=output/task/'status';report['proofs'][task]={'status':status.read_text().split()[0] if status.exists() else 'ERROR','error':str(error),'counts_as_pass':False}
            break
    report['all_pass']=len(report['proofs'])==2 and all(r['status']=='PASS' for r in report['proofs'].values())
    assert before=={p:sha(ROOT/p) for p in FILES},'Native sources changed during candidate proof'
    report['native_sources_unchanged']=True
    (output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Candidate full-unit result:',report['all_pass'],flush=True)
    if not report['all_pass']:raise SystemExit(1)


if __name__=='__main__':main()
