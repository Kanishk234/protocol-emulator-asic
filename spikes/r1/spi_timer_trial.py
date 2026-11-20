"""Stage an isolated SPI free-running timer experiment; production sources unchanged."""
import argparse
import json
from pathlib import Path

from assembly_catalog import sha
ROOT=Path(__file__).resolve().parents[2]
SOURCE_SHA='35f296838f48145d37763ac37458ec116128ef00dd712c79589e8642b1ff8a56'


def variant(text):
    old='.en(timing), .tc(tick)';new=".en(1'b1), .tc(tick)"
    if text.count(old)!=1 or new in text:raise ValueError('Unexpected SPI timer source')
    return text.replace(old,new,1)


def prepare(out,mode,half):
    if mode not in range(4) or half not in (4,25):raise ValueError('Unsupported bounded proof configuration')
    out=Path(out).resolve();source=ROOT/'protocols/spi_ctrl/spi_ctrl_top.v'
    if sha(source)!=SOURCE_SHA:raise ValueError('Original protocol source changed')
    out.mkdir(parents=True,exist_ok=False)
    original=source.read_text();candidate=variant(original)
    if candidate.replace(".en(1'b1), .tc(tick)",'.en(timing), .tc(tick)',1)!=original:
        raise ValueError('Unexpected source delta')
    (out/'candidate').mkdir();(out/'candidate/spi_ctrl_top.v').write_text(candidate)
    (out/'spi_ctrl_free_timer_top.v').write_text(candidate.replace('module spi_ctrl_top #(','module spi_ctrl_free_timer_top #(',1))
    cpol,cpha=divmod(mode,2)
    lines=['`default_nettype none','module wp_spi_timer_equiv(',
        'input wire clk,rst_n,miso_i,h_wvalid,h_wlast,h_rready,input wire [7:0] h_wdata);']
    for index,module in enumerate(('spi_ctrl_top','spi_ctrl_free_timer_top')):
        n=str(index)
        lines += ['wire sck'+n+',mosi'+n+',cs'+n+',wr'+n+',rv'+n+';',
                  'wire [2:0] oe'+n+';wire [7:0] data'+n+',status'+n+';',
                  module+' #(.CPOL('+str(cpol)+'),.CPHA('+str(cpha)+'),.HALF('+str(half)+'),.PRIMS(1)) d'+n+'(',
                  '.clk(clk),.rst_n(rst_n),.miso_i(miso_i),.h_wdata(h_wdata),.h_wvalid(h_wvalid),',
                  '.h_wlast(h_wlast),.h_rready(h_rready),.sck_o(sck'+n+'),.mosi_o(mosi'+n+'),.cs_n_o(cs'+n+'),',
                  '.out_oe(oe'+n+'),.h_wready(wr'+n+'),.h_rvalid(rv'+n+'),.h_rdata(data'+n+'),.h_status(status'+n+'));']
    lines += ["reg past_valid=1'b0;",'always @(posedge clk) begin',
              'past_valid<=1; if (!past_valid) assume (!rst_n);',
              'if (past_valid) assert ({sck0,mosi0,cs0,oe0,wr0,rv0,data0,status0} ==',
              '{sck1,mosi1,cs1,oe1,wr1,rv1,data1,status1});','end','endmodule']
    (out/'miter.sv').write_text('\n'.join(lines)+'\n')
    files=[source,out/'spi_ctrl_free_timer_top.v',ROOT/'tools/compile/prims/warp_prims_sim.v',
           ROOT/'arch/prims/wp_timer.v',ROOT/'arch/prims/wp_shift.v',out/'miter.sv']
    (out/'equiv.sby').write_text('[options]\nmode prove\ndepth 32\n\n[engines]\nabc pdr\n\n[script]\nread -formal '+
        ' '.join(p.name for p in files)+'\nprep -top wp_spi_timer_equiv\n\n[files]\n'+
        '\n'.join(str(p) for p in files)+'\n')
    inputs=[Path(__file__).resolve(),*files,out/'candidate/spi_ctrl_top.v',out/'equiv.sby',
            ROOT/'protocols/spi_ctrl/test/test_spi_ctrl.py']
    (out/'plan.json').write_text(json.dumps(dict(mode=mode,half=half,inputs={str(p):sha(p) for p in inputs},
        adopted=False,timing_acceptance=False,scope='Only SPI user-program hard-timer enable changes to constant1; timer still reloads on accept. Idle timer activity may increase. Full binary pin/host equivalence after initial reset and independent protocol tests required; no fabric/hardware, native or timing acceptance.'),indent=2)+'\n')


def audit(out):
    from autonomy.check_xml import check_xml
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    if any(sha(p)!=h for p,h in plan['inputs'].items()):raise ValueError('Protocol proof input changed')
    if (out/'equiv/status').read_text().strip()!='PASS':raise ValueError('No unbounded equivalence pass')
    tests=check_xml(out/'results.xml',4)
    result=dict(equivalence_passed=True,scope='Unbounded binary RTL output equivalence of original and free-running-timer SPI for this mode/HALF, PRIMS1, initial synchronous reset; arbitrary subsequent host/MISO/reset inputs. Independent source protocol tests separately executed.',
        mode=plan['mode'],half=plan['half'],strict_source_tests=len(tests),native_functional_passed=False,
        extracted_timing_passed=False,adopted=False)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    x=sub.add_parser('prepare');x.add_argument('--out',type=Path,required=True);x.add_argument('--spi-mode',type=int,required=True);x.add_argument('--half',type=int,required=True)
    sub.add_parser('audit').add_argument('--out',type=Path,required=True)
    a=vars(p.parse_args());action=a.pop('mode')
    if action=='prepare':a['mode']=a.pop('spi_mode');prepare(**a)
    else:audit(**a)
