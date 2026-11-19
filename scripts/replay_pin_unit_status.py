#!/usr/bin/env python3
"""Replay an open BITSYNC status-collision diagnostic on unmodified RTL.
A reproduced assertion is an observed issue, not a passing functional test.
"""
import json
from pathlib import Path
import subprocess
from formal_channels import ROOT, sha

WIDTHS={'rst_n':1,'restart':1,'live':1,'pads':24,'tx_avail':1,'tx_tag':2,'tx_data':16,
        'rx_free':1,'clr_late':1,'clr_overrun':1,'idle_next':1,'sample_delta':25,
        'carrier_active':1,'bitsync_active':1}
SOURCES=['src/trw_pin_unit.v','src/trw_pin_io.v','src/trw_pin_rx.v','src/trw_pin_tx.v','src/trw_pin_bs.v']


def render(f,cfg):
    declarations='\n'.join(f'reg [{w-1}:0] {n};' for n,w in WIDTHS.items())
    ports=', '.join(f'.{n}({n})' for n in WIDTHS)
    assignments=[]
    for i,row in enumerate(f['cycles']):
        if i:assignments.append('@(negedge clk);')
        assignments.extend(f"{n} = {WIDTHS[n]}'d{v};" for n,v in zip(f['signals'],row))
    return f'''module testbench;
reg clk=0;
reg was_available=0, was_taken=0;
reg [17:0] held_token=0;
integer cycle=0;
always #5 clk=~clk;
{declarations}
trw_pin_unit #(.FULL(1),.USE_LEVEL_CACHE(1),.USE_SAMPLE_DELTA(1),.USE_BITSYNC_ACTIVE(1)) dut (
.clk(clk),.cfg(352'h{cfg:x}),{ports});
initial begin
{chr(10).join(assignments)}
@(posedge clk); #1; $display("REPLAY_COMPLETED"); $finish;
end
always @(posedge clk) begin
 if (rst_n && was_available && !was_taken && (!tx_avail || held_token != {{tx_tag,tx_data}})) $fatal(1,"PROTOCOL_INPUT_INVALID");
 if (rst_n && dut.tx_take) $display("ACCEPT cycle=%0d tag=%0d data=%04h",cycle,tx_tag,tx_data);
 was_available <= tx_avail; was_taken <= dut.tx_take; held_token <= {{tx_tag,tx_data}}; cycle <= cycle+1;
end
always @(posedge clk) if(rst_n && dut.g_bs.u_bs.st_clash)
$display("STATUS_COLLISION rb=%b sync=%b overrun=%b pending=%b free=%b cycle=%0d sample=%b boundary=%b start=%b join=%b",dut.g_bs.u_bs.rb_ev,dut.g_bs.u_bs.sync_ev,dut.ovr_set,dut.g_bs.u_bs.st_v,rx_free,cycle,dut.g_bs.u_bs.smp,dut.g_bs.u_bs.bnd,dut.g_bs.u_bs.o_start,dut.g_bs.u_bs.jn);
endmodule
'''


def main():
    fixture=ROOT/'formal/fixtures/pin_unit_status_collision.json'
    f=json.loads(fixture.read_text());out=ROOT/'build/pin_unit_status_replay';out.mkdir(parents=True,exist_ok=True)
    report={'scope':f['scope'],'fixture_sha256':sha(fixture),'runner_sha256':sha(__file__),
            'source_sha256':{p:sha(ROOT/p) for p in SOURCES+['src/trw_defs.vh','src/trw_assert.vh']},'cases':{},'hardware_changed':False}
    for label,idle in [('observed',1),('idle4_control',4),('minimized',1),('minimized_idle4_control',4)]:
        case_fixture=fixture if not label.startswith('minimized') else ROOT/'formal/fixtures/pin_unit_status_collision_minimized.json'
        f=json.loads(case_fixture.read_text())
        cfg=(int(f['cfg_hex'],16)&~(31<<264))|(idle<<264)
        tb=render(f,cfg)
        source=out/(label+'.v');source.write_text(tb);binary=out/(label+'.vvp')
        subprocess.run(['iverilog','-g2012','-DSIM_ASSERT','-Isrc','-s','testbench','-o',str(binary),str(source),*SOURCES],cwd=ROOT,check=True,timeout=30)
        result=subprocess.run(['vvp',str(binary)],cwd=ROOT,text=True,capture_output=True,timeout=30)
        log=out/(label+'.log');log.write_text(result.stdout+result.stderr)
        if idle==1:
            assert result.returncode!=0 and 'BITSYNC: two status EVENTs in one clock' in log.read_text()
            assert 'STATUS_COLLISION rb=1 sync=1 overrun=0' in log.read_text()
        else:assert result.returncode==0 and 'REPLAY_COMPLETED' in log.read_text()
        report['cases'][label]={'exit_code':result.returncode,'idle_bits':idle,'log_sha256':sha(log),'testbench_sha256':sha(source),'fixture_sha256':sha(case_fixture)}
        print(label,'native assertion reproduced' if idle==1 else 'finite control completed',flush=True)
    report['formal_gate_passed']=False
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
