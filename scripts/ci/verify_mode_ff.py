"""Reproduce phase/inductive checks for the bound TXMODE/RXMODE configuration flops."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from apply_mode_ff import apply
from verify_cfg_staging import wrapper

ROOT = Path(__file__).resolve().parents[2]


def verify_exhaustive(out):
    bench=ROOT/'spikes/phase2_stock_flow/mode_ff/tb_mode_ff.v'
    results=[]
    for full in (0,1):
     exe=out/f'exhaustive{full}.vvp'
     subprocess.run(['iverilog','-g2005','-Isrc','-s','tb_mode_ff',f'-Ptb_mode_ff.FULL={full}','-o',str(exe),'gold.v','gate.v',str(bench)],cwd=out,check=True)
     log=subprocess.check_output(['vvp',str(exe)],cwd=out,text=True,timeout=90)
     (out/f'exhaustive{full}.log').write_text(log)
     assert f'PASS full={full} cycles=133152 phase_checks=665760' in log
     results.append(dict(full=full,cycles=133152,phase_checks=665760,all_word0_values_per_reset_polarity=65536,all_module_outputs_compared=True))
    original=(out/'gate.v').read_text()
    old="if (dec) q <= rst_n ? wdata[b] : 1'b0;"
    new="if ((16*w + b) == `TRW_PC_IDLE_LSB) begin if (dec) q <= rst_n ? wdata[b] : 1'b0; end else if (!rst_n) q <= 1'b0; else if (dec) q <= wdata[b];"
    assert original.count(old)==1
    (out/'mutant.v').write_text(original.replace(old,new))
    exe=out/'wrong_reset.vvp'
    subprocess.run(['iverilog','-g2005','-Isrc','-s','tb_mode_ff','-Ptb_mode_ff.FULL=1','-o',str(exe),'gold.v','mutant.v',str(bench)],cwd=out,check=True)
    r=subprocess.run(['vvp',str(exe)],cwd=out,text=True,capture_output=True,timeout=90)
    (out/'wrong_reset.log').write_text(r.stdout+r.stderr)
    assert r.returncode and 'Configuration staging changes observable phase behavior' in r.stdout
    return dict(results=results,wrong_reset_mutant_rejected=True)


def generic_cost(output, yosys):
    results = {}
    for full in (0, 1):
        rows = {}
        for kind in ('gold', 'gate'):
            script = output / f'generic_{kind}_{full}.ys'
            script.write_text(f'read_verilog -DSYNTHESIS -Isrc {kind}.v\n'
                f'chparam -set FULL {full} trw_pin_cfg_{kind}\n'
                f'hierarchy -top trw_pin_cfg_{kind}\nproc\nopt\n'
                f'tee -o generic_{kind}_{full}.json stat -json\n')
            with (output / f'generic_{kind}_{full}.log').open('w') as log:
                subprocess.run([yosys, '-Q', '-s', str(script)], cwd=output,
                    stdout=log, stderr=subprocess.STDOUT, check=True, timeout=60)
            rows[kind] = json.loads((output / f'generic_{kind}_{full}.json').read_text())['modules'][f'\\trw_pin_cfg_{kind}']['num_cells_by_type']
        results[full] = rows
    return dict(scope='Generic cell-count delta only; not mapped or physical area', results=results)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--includes',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--yosys',default='yosys')
    args=parser.parse_args()
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    shutil.copytree(args.includes,output/'src')
    reference=args.reference.read_text()
    (output/'src/trw_pin_cfg.v').write_text(reference)
    receipt=apply(output,ROOT/'spikes/phase2_stock_flow/mode_ff')
    trial=(output/'src/trw_pin_cfg.v').read_text()
    for kind,text in (('gold',reference),('gate',trial)):
        (output/f'{kind}.v').write_text(text.replace('module trw_pin_cfg #(',f'module trw_pin_cfg_{kind} #(',1))
    results=[]
    for full in (0,1):
        target=output/f'phase{full}.vvp'
        subprocess.run(['iverilog','-g2005','-Isrc','-s','tb_cfg_staging',
                        f'-Ptb_cfg_staging.FULL={full}','-o',str(target),'gold.v','gate.v',
                        str(ROOT/'test_internal/cfg_staging/tb_cfg_staging.v')],cwd=output,check=True,timeout=30)
        phase=subprocess.check_output(['vvp',str(target)],cwd=output,text=True,timeout=30)
        (output/f'phase{full}.log').write_text(phase)
        assert f'PASS full={full} cycles=2080 phase_checks=10400' in phase
        for kind in ('gold','gate'):
            text=wrapper(kind,full).replace('output wire carrier_active, restart);',
                'output wire carrier_active, restart, bitsync_active, output wire [24:0] sample_delta);')
            text=text.replace('.carrier_active(carrier_active),.restart(restart));',
                '.carrier_active(carrier_active),.restart(restart),.bitsync_active(bitsync_active),.sample_delta(sample_delta));')
            (output/f'wrapper_{kind}.v').write_text(text)
        script=output/f'proof{full}.ys'
        script.write_text('''read_verilog -nosynthesis -Isrc gold.v gate.v wrapper_gold.v wrapper_gate.v
hierarchy -check
proc
flatten wrapper_gold wrapper_gate
opt
equiv_make wrapper_gold wrapper_gate equiv
hierarchy -top equiv
clk2fflogic
opt_clean
equiv_simple
equiv_induct -seq 6
equiv_status -assert
''')
        with (output/f'proof{full}.log').open('w') as log:
            subprocess.run([args.yosys,'-Q','-s',str(script)],cwd=output,stdout=log,
                           stderr=subprocess.STDOUT,check=True,timeout=180)
        log=(output/f'proof{full}.log').read_text()
        match=re.search(r'Of those cells (\d+) are proven and 0 are unproven',log)
        assert match and 'Equivalence successfully proven!' in log
        results.append(dict(full=full,equivalence_points=int(match[1]),induction_sequence_cap=6,
                            phase_cycles=2080,phase_checks=10400))
    exhaustive=verify_exhaustive(output)
    cost=generic_cost(output,args.yosys)
    (output/'receipt.json').write_text(json.dumps(dict(reference_sha256=hashlib.sha256(reference.encode()).hexdigest(),
        candidate_sha256=hashlib.sha256(trial.encode()).hexdigest(),checks=results,
        source_inventory=receipt,exhaustive=exhaustive,generic_cost=cost,scope='Configuration module/all outputs with clocked host writes; no blacklisted correspondence; not full-chip formal or physical timing'),indent=2)+'\n')
    print(json.dumps(results))


if __name__=='__main__':main()
