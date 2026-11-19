#!/usr/bin/env python3
"""Check the scratch BITSYNC merge candidate; never modify qualified src/."""
import json
from pathlib import Path
import re
import shutil
import subprocess
from formal_channels import ROOT, sha
from replay_pin_unit_status import SOURCES, render

PATCH=ROOT/'spikes/phase3_status_merge/status_merge.patch'


def execute(out,name,tb,sources,expect_pass=True):
    v=out/(name+'.v');v.write_text(tb);binary=out/(name+'.vvp')
    c=subprocess.run(['iverilog','-g2012','-DSIM_ASSERT','-Isrc','-s','testbench','-o',str(binary),str(v),*map(str,sources)],cwd=ROOT,text=True,capture_output=True,timeout=30)
    if c.returncode:raise RuntimeError(c.stderr)
    r=subprocess.run(['vvp',str(binary)],cwd=ROOT,text=True,capture_output=True,timeout=30)
    log=out/(name+'.log');log.write_text(r.stdout+r.stderr)
    if expect_pass and r.returncode:raise RuntimeError(log.read_text())
    if not expect_pass and (r.returncode==0 or 'MATRIX' not in log.read_text()):
        raise RuntimeError('Fault did not fail the reference matrix: '+log.read_text())
    return {'exit_code':r.returncode,'log_sha256':sha(log),'testbench_sha256':sha(v)},r.stdout


def matrix(source):
    text=source.read_text()
    header=text[text.index('module trw_pin_bs'):].split(');',1)[0]
    inputs=re.findall(r'input\s+wire\s*(?:\[[^\]]+\]\s*)?(\w+)',header)
    values={'clk':'clk','rst_n':'rst_n','live':"1'b1",'active':"1'b1",'rx_free':'free'}
    ports=', '.join(f'.{n}({values.get(n,"\'0")})' for n in inputs)
    return '''module testbench;
reg clk=0, rst_n=0, free=0;
reg rb=0, sy=0, rf=0, frame=0;
wire load, overrun;
wire [1:0] tag;
wire [15:0] data;
trw_pin_bs dut (PORTS,.rx_load(load),.rx_tag(tag),.rx_data(data),.ovr_set(overrun));
integer old, mask, fr, avail, count, offset, cases=0;
reg [15:0] queue [0:3];
reg expected_load, expected_overrun;
reg [15:0] expected_data;
initial begin
 force dut.fr_want=frame; force dut.fr_tag=2'd0; force dut.fr_data=16'hbeef;
 force dut.rb_ev=rb; force dut.sync_ev=sy; force dut.ref_ev=rf;
 for(old=0;old<2;old=old+1) for(mask=0;mask<8;mask=mask+1)
 for(fr=0;fr<2;fr=fr+1) for(avail=0;avail<2;avail=avail+1) begin
  rst_n=0; rb=0;sy=0;rf=0;frame=0; #2;clk=1;#1;clk=0;#1;
  rst_n=1;dut.st_v=old;dut.st_d=16'h1234;
  rb=mask[0];sy=mask[1];rf=mask[2];frame=fr;free=avail;
  count=0;
  if(old) begin queue[count]=16'h1234;count=count+1;end
  if(rb) begin queue[count]=16'ha000;count=count+1;end
  if(sy) begin queue[count]=16'h9001;count=count+1;end
  if(rf) begin queue[count]=16'hc001;count=count+1;end
  offset=0;expected_load=0;expected_data=0;
  if(fr && avail) begin expected_load=1;expected_data=16'hbeef;end
  else if(!fr && avail && count>0) begin expected_load=1;expected_data=queue[0];offset=1;end
  expected_overrun=(fr && !avail) || (count-offset>1);
  #1;
  if(load !== expected_load || overrun !== expected_overrun) $fatal(1,"MATRIX control old=%0d mask=%0d frame=%0d free=%0d",old,mask,fr,avail);
  if(expected_load && (data !== expected_data || tag !== (fr ? 2'd0 : 2'd2))) $fatal(1,"MATRIX payload");
  clk=1;#1;clk=0;#1;
  if(dut.st_v !== (count-offset>0)) $fatal(1,"MATRIX pending valid");
  if(count-offset>0 && dut.st_d !== queue[offset]) $fatal(1,"MATRIX pending payload");
  cases=cases+1;
 end
 $display("MATRIX_PASS cases=%0d",cases);$finish;
end
endmodule
'''.replace('PORTS',ports)


def main():
    out=ROOT/'build/pin_unit_status_candidate';(out/'src').mkdir(parents=True,exist_ok=True)
    native=ROOT/'src/trw_pin_bs.v';before=sha(native);shutil.copyfile(native,out/'src/trw_pin_bs.v')
    subprocess.run(['patch','--batch','-p1','-i',str(PATCH)],cwd=out,check=True,capture_output=True)
    modified=out/'src/trw_pin_bs.v'
    sources=[modified if p=='src/trw_pin_bs.v' else ROOT/p for p in SOURCES]
    report={'source_sha256':{p:sha(ROOT/p) for p in SOURCES+['src/trw_defs.vh','src/trw_assert.vh']},'native_sha256':before,'candidate_sha256':sha(modified),'patch_sha256':sha(PATCH),'runner_sha256':sha(__file__),'replay_runner_sha256':sha(ROOT/'scripts/replay_pin_unit_status.py'),'cases':{},'adopted':False,'physical_qualification':False}
    for label,file in [('original','pin_unit_status_collision.json'),('minimized','pin_unit_status_collision_minimized.json')]:
        f=json.loads((ROOT/'formal/fixtures'/file).read_text());tb=render(f,int(f['cfg_hex'],16))
        result,log=execute(out,label,tb,sources)
        assert 'STATUS_COLLISION rb=1 sync=1 overrun=1' in log and 'REPLAY_COMPLETED' in log
        result['fixture_sha256']=sha(ROOT/'formal/fixtures'/file);report['cases'][label]=result
    result,log=execute(out,'matrix',matrix(modified),[modified]);assert 'MATRIX_PASS cases=64' in log
    report['cases']['matrix']=result
    report['mutation_controls']={}
    for name,old,new in [
        ('lose_second_pending','st_d <= st_wait_data;','st_d <= st_nd;'),
        ('suppress_loss_flag','|| st_overflow;','|| 1\'b0;'),
        ('ignore_older_pending','fr_want ? fr_data : st_v ? st_d : st_nd;','fr_want ? fr_data : st_nd;')]:
        text=modified.read_text();assert text.count(old)==1
        mutant=out/(name+'_rtl.v');mutant.write_text(text.replace(old,new))
        result,_=execute(out,name,matrix(mutant),[mutant],expect_pass=False)
        result['source_sha256']=sha(mutant);report['mutation_controls'][name]=result
    assert sha(native)==before
    report['native_source_unchanged']=True
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Candidate replays PASS; 64-case native merge matrix PASS; not adopted/physically qualified')


if __name__=='__main__':main()
