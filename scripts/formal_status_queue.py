#!/usr/bin/env python3
"""Prove the candidate's source-extracted status cone, not the whole engine."""
import json
from pathlib import Path
import re
import shutil
import subprocess
from formal_channels import ROOT, run, sha

PATCH=ROOT/'spikes/phase3_status_merge/status_merge.patch'
PROPS=['formal/props/status_queue_reference.vh','formal/props/status_queue_harness.sv','formal/status_queue.sby']


def extract(source):
    # Copy the actual native producer region and status update block verbatim.
    # Reject future state writers outside the reviewed reset/update cone.
    assert len(re.findall(r'\bst_v\s*<=',source))==3
    assert len(re.findall(r'\bst_d\s*<=',source))==2
    first=source.index('    wire        st_new   =')
    last=source.index('\n',source.index('    assign ovr_set =',first))
    cone=source[first:last]
    begin=source.index('            if (st_hold && !st_keep) begin')
    end=source.index('\n\n',begin)
    update=source[begin:end]
    assert "if (!rst_n || restart || !active) begin" in source
    assert "st_v <= 1'b0;  st_d <= 16'd0;" in source
    return '''`include "trw_defs.vh"
module status_queue_native(input wire clk,rst_n,restart,active,live,rx_free,
input wire fr_want,rb_ev,sync_ev,ref_ev,a_in,
input wire [1:0] fr_tag,tmode,input wire [15:0] fr_data,input wire [10:0] lcnt);
wire rx_load,ovr_set;wire [1:0] rx_tag;wire [15:0] rx_data;
'''+cone+'''
always @(posedge clk) begin
 if(!rst_n || restart || !active) begin st_v<=0;st_d<=0;end
 else begin
'''+update+'''
 end
end
`include "status_queue_reference.vh"
endmodule
'''


def main():
    output=ROOT/'build/formal_status_queue';scratch=output/'native'
    (scratch/'src').mkdir(parents=True,exist_ok=True)
    for rel in ['src/trw_pin_bs.v','src/trw_defs.vh',*PROPS]:
        target=scratch/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,target)
    before=sha(ROOT/'src/trw_pin_bs.v')
    subprocess.run(['patch','--batch','-p1','-i',str(PATCH)],cwd=scratch,check=True,capture_output=True)
    source=(scratch/'src/trw_pin_bs.v').read_text();seam=scratch/'src/status_queue_native.v';seam.write_text(extract(source))
    report={'scope':'Source-extracted native candidate producer cone and status register, arbitrary boundary intents/data; not whole BITSYNC engine',
            'runner_sha256':sha(__file__),'shared_runner_sha256':sha(ROOT/'scripts/formal_channels.py'),'tool_versions':{t:subprocess.check_output(args,text=True).strip() for t,args in {'yosys':['yosys','-V'],'sby':['sby','--version'],'z3':['z3','--version']}.items()},'native_sha256':before,'candidate_sha256':sha(scratch/'src/trw_pin_bs.v'),
            'patch_sha256':sha(PATCH),'extracted_sha256':sha(seam),'property_sha256':{p:sha(ROOT/p) for p in PROPS},'proofs':{},'mutation_controls':{}}
    for task,engine in [('safety','abc pdr'),('reachable','smtbmc z3')]:
        report['proofs'][task]=run('status_queue.sby',scratch/'formal',task,output/task,'PASS',engine)
    seam.write_text(extract((ROOT/'src/trw_pin_bs.v').read_text()))
    report['baseline_control']=run('status_queue.sby',scratch/'formal','safety',output/'baseline_control','FAIL','abc pdr')
    for name,old,new in [
        ('lose_second_pending','st_d <= st_wait_data;','st_d <= st_nd;'),
        ('suppress_loss','|| st_overflow;','|| 1\'b0;'),
        ('ignore_old_pending','fr_want ? fr_data : st_v ? st_d : st_nd;','fr_want ? fr_data : st_nd;')]:
        assert source.count(old)==1
        seam.write_text(extract(source.replace(old,new)))
        report['mutation_controls'][name]=run('status_queue.sby',scratch/'formal','safety',output/name,'FAIL','abc pdr')
    seam.write_text(extract(source))
    assert sha(ROOT/'src/trw_pin_bs.v')==before
    report['native_source_unchanged']=True
    (output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Candidate queue unbounded proof, covers and three fault controls PASS')


if __name__=='__main__':main()
