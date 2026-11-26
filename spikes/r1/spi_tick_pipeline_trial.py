"""Stage an isolated registered SPI tick experiment; production sources unchanged."""
import argparse
import json
import re
from pathlib import Path

from assembly_catalog import sha
ROOT=Path(__file__).resolve().parents[2]
SOURCE_SHA='35f296838f48145d37763ac37458ec116128ef00dd712c79589e8642b1ff8a56'


TIMER_OLD = """            WP_TIMER #(.RELOAD(RELOAD), .ONESHOT(1'b0)) u_timer (
                .clk(clk), .rst(!rst_n), .load(accept), .half(1'b0), .en(timing), .tc(tick));"""
TIMER_NEW = """            reg tick_q;
            wire tick_early;
            assign tick = tick_q;
            always @(posedge clk) begin
                if (!rst_n) tick_q <= 1'b0;
                else if (accept || !timing) tick_q <= 1'b0;
                else tick_q <= tick_early && !tick_q;
            end
            WP_TIMER #(.RELOAD(RELOAD), .ONESHOT(1'b1)) u_timer (
                .clk(clk), .rst(!rst_n), .load(accept || tick_q), .half(1'b0), .en(timing), .tc(tick_early));"""
RELOAD_OLD = 'localparam integer RELOAD_I = HALF - 1;'
RELOAD_NEW = 'localparam integer RELOAD_I = HALF - 2;'
TIMER_NEW_UNGATED = TIMER_NEW.replace('.en(timing)',".en(1'b1)")


def variant(text,ungated_timer=False):
    if type(ungated_timer) is not bool:raise ValueError('Explicit Boolean timer mode required')
    if text.count(TIMER_OLD) != 1 or text.count(RELOAD_OLD) != 1 or 'tick_q' in text:
        raise ValueError('Unexpected original SPI timer source')
    return text.replace(TIMER_OLD, TIMER_NEW_UNGATED if ungated_timer else TIMER_NEW, 1).replace(RELOAD_OLD, RELOAD_NEW, 1)


def restore(text,ungated_timer=False):
    if type(ungated_timer) is not bool:raise ValueError('Explicit Boolean timer mode required')
    timer=TIMER_NEW_UNGATED if ungated_timer else TIMER_NEW
    if text.count(timer) != 1 or text.count(RELOAD_NEW) != 1:
        raise ValueError('Unexpected registered-tick SPI candidate')
    return text.replace(timer, TIMER_OLD, 1).replace(RELOAD_NEW, RELOAD_OLD, 1)


def prepare(out,mode,half,ungated_timer=False):
    if mode not in range(4) or half not in (4,25):raise ValueError('Unsupported bounded proof configuration')
    out=Path(out).resolve();source=ROOT/'protocols/spi_ctrl/spi_ctrl_top.v'
    if sha(source)!=SOURCE_SHA:raise ValueError('Original protocol source changed')
    out.mkdir(parents=True,exist_ok=False)
    original=source.read_text();candidate=variant(original,ungated_timer)
    if restore(candidate,ungated_timer)!=original:
        raise ValueError('Unexpected source delta')
    (out/'candidate').mkdir();(out/'candidate/spi_ctrl_top.v').write_text(candidate)
    (out/'spi_ctrl_registered_tick_top.v').write_text(candidate.replace('module spi_ctrl_top #(','module spi_ctrl_registered_tick_top #(',1))
    cpol,cpha=divmod(mode,2)
    lines=['`default_nettype none','module wp_spi_timer_equiv(',
        'input wire clk,rst_n,miso_i,h_wvalid,h_wlast,h_rready,input wire [7:0] h_wdata);']
    for index,module in enumerate(('spi_ctrl_top','spi_ctrl_registered_tick_top')):
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
    files=[source,out/'spi_ctrl_registered_tick_top.v',ROOT/'tools/compile/prims/warp_prims_sim.v',
           ROOT/'arch/prims/wp_timer.v',ROOT/'arch/prims/wp_shift.v',out/'miter.sv']
    (out/'equiv.sby').write_text('[options]\nmode prove\ndepth 32\n\n[engines]\nabc pdr\n\n[script]\nread -formal '+
        ' '.join(p.name for p in files)+'\nprep -top wp_spi_timer_equiv\n\n[files]\n'+
        '\n'.join(str(p) for p in files)+'\n')
    inputs=[Path(__file__).resolve(),*files,out/'candidate/spi_ctrl_top.v',out/'equiv.sby',
            ROOT/'protocols/spi_ctrl/test/test_spi_ctrl.py']
    (out/'plan.json').write_text(json.dumps(dict(mode=mode,half=half,ungated_timer=ungated_timer,inputs={str(p):sha(p) for p in inputs},
        adopted=False,timing_acceptance=False,scope='Register the existing hard timer terminal pulse; use one-shot HALF-2 and reload on accept or registered pulse. '+('Keep timer en high; the registered pulse remains qualified by original timing state. ' if ungated_timer else '')+'Preserve original pins/cycle timing only if full equivalence and source tests pass. No production, fabric, native or timing adoption.'),indent=2)+'\n')



def admit_status(status,proof_log):
    if (not re.fullmatch(r'PASS(?: \d+){0,2}',status.strip()) or
            proof_log.count('DONE (PASS, rc=0)')!=1 or
            'engine_0 (abc pdr) returned PASS' not in proof_log):
        raise ValueError('No completed unbounded PDR equivalence pass')


def audit(out):
    from autonomy.check_xml import check_xml
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    if any(sha(p)!=h for p,h in plan['inputs'].items()):raise ValueError('Protocol proof input changed')
    admit_status((out/'equiv/status').read_text(),(out/'proof.log').read_text())
    tests=check_xml(out/'results.xml',4)
    result=dict(equivalence_passed=True,ungated_timer=plan.get('ungated_timer',False),scope='Unbounded binary RTL output equivalence of original and registered-tick'+('/ungated-timer' if plan.get('ungated_timer',False) else '')+' SPI for this mode/HALF, PRIMS1, initial synchronous reset; arbitrary subsequent host/MISO/reset inputs. Independent source protocol tests separately executed.',
        mode=plan['mode'],half=plan['half'],strict_source_tests=len(tests),native_functional_passed=False,
        extracted_timing_passed=False,adopted=False)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    x=sub.add_parser('prepare');x.add_argument('--out',type=Path,required=True);x.add_argument('--spi-mode',type=int,required=True);x.add_argument('--half',type=int,required=True)
    x.add_argument('--ungated-timer',action='store_true')
    sub.add_parser('audit').add_argument('--out',type=Path,required=True)
    a=vars(p.parse_args());action=a.pop('mode')
    if action=='prepare':a['mode']=a.pop('spi_mode');prepare(**a)
    else:audit(**a)
