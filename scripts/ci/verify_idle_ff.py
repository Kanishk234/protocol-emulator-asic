"""Reproduce phase/inductive checks for the bound sparse configuration flop."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from apply_idle_ff import apply
from verify_cfg_staging import wrapper

ROOT = Path(__file__).resolve().parents[2]


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
    receipt=apply(output,ROOT/'spikes/phase2_stock_flow/idle_ff')
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
    (output/'receipt.json').write_text(json.dumps(dict(reference_sha256=hashlib.sha256(reference.encode()).hexdigest(),
        candidate_sha256=hashlib.sha256(trial.encode()).hexdigest(),checks=results,
        source_inventory=receipt,scope='Configuration module/all outputs with clocked host writes; no blacklisted correspondence; not full-chip formal or physical timing'),indent=2)+'\n')
    print(json.dumps(results))


if __name__=='__main__':main()
