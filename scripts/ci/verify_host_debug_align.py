"""Reproduce complete host/SPI equivalence and isolated guarded debug-mux mapping."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from apply_host_debug_align import apply

ROOT = Path(__file__).resolve().parents[2]


def proof_script(nl, nu, nc, trial='trial.v'):
    return f'''read_verilog -DSYNTHESIS -Isrc gold.v src/trw_spi.v
chparam -set NL {nl} -set NU {nu} -set NC {nc} trw_host
rename trw_host gold
read_verilog -DSYNTHESIS -Isrc {trial}
chparam -set NL {nl} -set NU {nu} -set NC {nc} trw_host
rename trw_host gate
proc
memory
flatten gold gate
opt
equiv_make gold gate equiv
hierarchy -top equiv
equiv_simple
equiv_induct -seq 2
equiv_status -assert
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('reference','includes','output','liberty'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--yosys',default='yosys')
    args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    shutil.copytree(args.includes,out/'src')
    reference=args.reference.read_text();(out/'src/trw_host.v').write_text(reference)
    inventory=apply(out,ROOT/'spikes/phase2_stock_flow/host_debug_align')
    trial=(out/'src/trw_host.v').read_text()
    (out/'gold.v').write_text(reference);(out/'trial.v').write_text(trial)

    def run(name,script,require_success=True):
        path=out/(name+'.ys');path.write_text(script)
        result=subprocess.run([args.yosys,'-Q','-s',str(path)],cwd=out,text=True,
                              capture_output=True,timeout=180)
        text=result.stdout+result.stderr;(out/(name+'.log')).write_text(text)
        if require_success:result.check_returncode()
        return result.returncode,text

    proofs=[]
    for nl,nu,nc in ((2,4,9),(3,6,13)):
        _,log=run(f'proof-{nl}-{nu}',proof_script(nl,nu,nc))
        match=re.search(r'Of those cells (\d+) are proven and 0 are unproven',log)
        assert match and 'Equivalence successfully proven!' in log
        proofs.append(dict(nl=nl,nu=nu,points=int(match[1]),induction_sequence_cap=2))

    # A bad stride must not pass merely because invalid lane addresses are guarded.
    original='assign ld = words[256*lk +: LDW];'
    assert trial.count(original)==1
    (out/'mutant.v').write_text(trial.replace(original,'assign ld = words[128*lk +: LDW];'))
    code,log=run('wrong-stride',proof_script(2,4,9,'mutant.v'),False)
    assert code!=0 and 'unproven' in log,'Wrong lane-record stride mutant was not rejected'

    constraint=out/'cone.constr'
    constraint.write_text('set_driving_cell sg13cmos5l_buf_2\nset_load 6\n')
    mapped={}
    for nl in (2,3):
        mapped[nl]={}
        for kind,text in (('gold',reference),('gate',trial)):
            # Use the actual unchanged word decoder and external address-range guard.
            body=text.split("    // the addressed lane's debug fields\n",1)[1].split('    reg     uf_late',1)[0]
            body=body.split('    // Align each 10-bit',1)[0]
            source=out/f'cone-{kind}-{nl}.v'
            source.write_text(f'`include "trw_defs.vh"\nmodule cone #(parameter LDW=180, NL={nl})(input [NL*LDW-1:0] lane_dbg,input [15:0] r_ln,output [15:0] data);\n'+body+"assign data=(r_ln<NL*`TRW_HA_LANE_STRIDE)?lane_word:16'd0;\nendmodule\n")
            _,log=run(f'map-{kind}-{nl}',f'read_verilog -Isrc {source}; hierarchy -top cone; proc; flatten; opt; techmap; opt; abc -liberty {args.liberty.resolve()} -constr {constraint} -dont_use sg13cmos5l_buf_1; stat -liberty {args.liberty.resolve()}')
            timing=re.findall(r'ABC:.*Gates\s*=\s*(\d+).*Delay\s*=\s*([\d.]+) ps',log)
            area=re.findall(r'Chip area for module.*?:\s*([\d.]+)',log)
            assert len(timing)==1 and area
            mapped[nl][kind]=dict(gates=int(timing[0][0]),delay_ps=float(timing[0][1]),area_um2=float(area[-1]))
    receipt=dict(reference_sha256=hashlib.sha256(reference.encode()).hexdigest(),
        candidate_sha256=hashlib.sha256(trial.encode()).hexdigest(),proofs=proofs,
        wrong_stride_mutant_rejected=True,source_inventory=inventory,
        liberty_sha256=hashlib.sha256(args.liberty.read_bytes()).hexdigest(),
        isolated_guarded_debug_mapping=mapped,
        scope='Complete host/SPI module equivalence at stated counts, all outputs/all read addresses. Mapping is isolated guarded debug-word cone, not whole-host or full-chip area/extracted timing.')
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(proofs))


if __name__=='__main__':main()
