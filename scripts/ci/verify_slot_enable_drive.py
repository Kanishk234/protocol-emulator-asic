"""Prove actual synthesis-path enable buffers and replay real foundry cells."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from apply_slot_enable_drive import apply

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('reference','includes','output','liberty','cells','udp','ivl_root'):
        parser.add_argument('--'+name.replace('_','-'),dest=name,type=Path,required=True)
    parser.add_argument('--yosys',default='yosys')
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    liberty=args.liberty.read_text()
    # Authenticate the functional buffer and gate semantics against pinned Liberty.
    assert 'cell (sg13cmos5l_buf_4)' in liberty and 'cell (sg13cmos5l_lgcp_1)' in liberty
    buf=liberty.split('cell (sg13cmos5l_buf_4)',1)[1].split('  cell (',1)[0]
    icg=liberty.split('cell (sg13cmos5l_lgcp_1)',1)[1].split('  cell (',1)[0]
    assert 'function : "A";' in buf and 'area : 14.5152;' in buf
    assert 'clock_gating_integrated_cell : "latch_posedge";' in icg
    assert 'statetable ("CLK GATE", "int_GATE")' in icg and 'state_function : "CLK * int_GATE";' in icg
    assert all(row in icg for row in ('L L : - : L', 'L H : - : H', 'H - : - : N'))
    models='''module sg13cmos5l_buf_4(input A,output X);assign X=A;endmodule
module sg13cmos5l_lgcp_1(input CLK,GATE,output GCLK);
reg en;always @* if(!CLK)en=GATE;assign GCLK=CLK & en;endmodule
'''
    results=[]
    for variant in ('constants','all_words'):
        folder=out/variant;folder.mkdir();shutil.copytree(args.includes,folder/'src')
        reference=args.reference.read_text();(folder/'src/trw_slots.v').write_text(reference)
        inventory=apply(folder,ROOT/'spikes/phase2_stock_flow/slot_enable_drive',variant)
        candidate=(folder/'src/trw_slots.v').read_text()
        (folder/'gold.v').write_text(reference.replace('module trw_slots (','module trw_slots_gold (',1))
        (folder/'gate.v').write_text(candidate.replace('module trw_slots (','module trw_slots_gate (',1))
        (folder/'models.v').write_text(models)
        proofs=[]
        for flops in (False,True):
            name='flops' if flops else 'asic'
            script=folder/(name+'.ys')
            script.write_text('read_verilog -DSYNTHESIS '+('-DTRW_SLOTS_FLOPS ' if flops else '')+'-Isrc gold.v gate.v models.v\n'
                'hierarchy -check\nproc\nflatten trw_slots_gold trw_slots_gate\nopt\n'
                'equiv_make trw_slots_gold trw_slots_gate equiv\nhierarchy -top equiv\n'
                'clk2fflogic\nopt_clean\nequiv_simple\nequiv_induct -seq 6\nequiv_status -assert\n')
            with (folder/(name+'.log')).open('w') as log:
                subprocess.run([args.yosys,'-Q','-s',str(script)],cwd=folder,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
            log=(folder/(name+'.log')).read_text();m=re.search(r'Of those cells (\d+) are proven and 0 are unproven',log)
            assert m and 'Equivalence successfully proven!' in log
            proofs.append(dict(mode=name,equivalence_points=int(m[1]),induction_sequence_cap=6))
        mapping=folder/'preserve.ys'
        mapping.write_text(f'read_liberty -lib {args.liberty.resolve()}\n'
            'read_verilog -DSYNTHESIS -Isrc gate.v\nsynth -top trw_slots_gate -flatten\n'
            f'dfflibmap -liberty {args.liberty.resolve()}\nabc -liberty {args.liberty.resolve()}\n'
            'opt_clean\nwrite_verilog -noattr -noexpr mapped.v\n')
        with (folder/'preserve.log').open('w') as log:
            subprocess.run([args.yosys,'-Q','-s',str(mapping)],cwd=folder,stdout=log,
                           stderr=subprocess.STDOUT,check=True,timeout=180)
        words=sorted(map(int,re.findall(r'\bsg13cmos5l_buf_4\s+g_word\[(\d+)\]\.g_enable_drive\.u_buf\b',
                                       (folder/'mapped.v').read_text().replace('\\',''))))
        assert words==list(range(48,52) if variant=='constants' else range(52)), 'Source buffers optimized out or changed'
        iv=args.ivl_root.resolve()
        common=[str(iv/'usr/bin/iverilog'),'-B',str(iv/'usr/lib/ivl'),'-g2005','-DSYNTHESIS','-DFUNCTIONAL','-DSIM','-Isrc',
                '-s','tb_enable_drive']
        bench=ROOT/'test_internal/slot_enable_drive/tb_enable_drive.v'
        def simulate(name,gate):
            executable=folder/(name+'.vvp')
            command=common+['-o',str(executable),str(args.cells.resolve()),str(args.udp.resolve()),'gold.v',gate,str(bench)]
            with (folder/(name+'-compile.log')).open('w') as log:
                subprocess.run(command,cwd=folder,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=30)
            result=subprocess.run([str(iv/'usr/bin/vvp'),str(executable)],cwd=folder,text=True,capture_output=True,timeout=120)
            (folder/(name+'.log')).write_text(result.stdout+result.stderr)
            return result
        run=simulate('foundry-phase','gate.v');run.check_returncode()
        m=re.search(r'PASS_SLOT_ENABLE_DRIVE cycles=(\d+) phase_checks=(\d+)',run.stdout);assert m
        assert int(m[1])==3125 and int(m[2])==12288
        (folder/'mutant.v').write_text((folder/'gate.v').read_text().replace('.A (dec)', '.A (~dec)',1))
        bad=simulate('wrong-enable','mutant.v')
        assert bad.returncode and 'FAIL_SLOT_ENABLE_DRIVE' in bad.stdout,'Negative control was not detected'
        results.append(dict(variant=variant,proofs=proofs,foundry_phase_cycles=int(m[1]),foundry_phase_checks=int(m[2]),
                            wrong_enable_mutant_rejected=True,source_inventory=inventory,
                            post_abc_source_buffer_count_per_lane=len(words)))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    (out/'receipt.json').write_text(json.dumps(dict(checks=results,reference_sha256=sha(args.reference),
        liberty_sha256=sha(args.liberty),cells_sha256=sha(args.cells),udp_sha256=sha(args.udp),
        scope='Slot module synthesis-path equivalence with Liberty-checked two-state models; real PDK-cell phase/reset/address replay and negative control; no full-chip or physical closure'),indent=2)+'\n')
    print(json.dumps([{k:v for k,v in r.items() if k!='source_inventory'} for r in results]))


if __name__=='__main__':main()
