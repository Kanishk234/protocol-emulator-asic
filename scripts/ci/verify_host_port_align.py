"""Reproduce complete host equivalence and isolated port-mux mapping."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from apply_host_port_align import apply

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('reference','includes','output','liberty','exclude-cells'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--yosys',default='yosys')
    args=parser.parse_args()
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    shutil.copytree(args.includes,output/'src')
    reference=args.reference.read_text();(output/'src/trw_host.v').write_text(reference)
    apply(output,ROOT/'spikes/phase2_stock_flow/host_port_align')
    trial=(output/'src/trw_host.v').read_text()
    (output/'gold.v').write_text(reference);(output/'trial.v').write_text(trial)
    def run(name,script):
        result=subprocess.run([args.yosys,'-Q','-p',script],cwd=output,text=True,
                              capture_output=True,check=True,timeout=180)
        (output/(name+'.log')).write_text(result.stdout+result.stderr)
        return result.stdout
    proofs=[]
    for nl,nu,nc in ((2,4,9),(3,6,13)):
        script=f'''read_verilog -DSYNTHESIS -Isrc gold.v src/trw_spi.v
chparam -set NL {nl} -set NU {nu} -set NC {nc} trw_host
rename trw_host gold
read_verilog -DSYNTHESIS -Isrc trial.v
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
        log=run(f'proof-{nl}-{nu}',script)
        match=re.search(r'Of those cells (\d+) are proven and 0 are unproven',log)
        assert match and 'Equivalence successfully proven!' in log
        proofs.append(dict(nl=nl,nu=nu,points=int(match[1]),induction_sequence_cap=2))
    exclude=' '.join('-dont_use '+n for n in ['sg13cmos5l_buf_1']+args.exclude_cells.read_text().split())
    mapped={}
    for nc in (9,13):
        for load in (6,130):
            tag=f'nc{nc}-load{load}';constraint=output/(tag+'.constr')
            constraint.write_text(f'set_driving_cell sg13cmos5l_buf_2\nset_load {load}\n')
            mapped[tag]={}
            for kind in ('gold','gate'):
                header=f'module cone(input [{10*nc-1}:0] port_state,input [15:0] r_pt,output [15:0] data);\n'
                if kind=='gold':
                    body=f"assign data=(r_pt<{nc}) ? {{6'd0,port_state[10*r_pt[3:0]+:10]}} : 16'd0;\n"
                else:
                    body=f"wire [{16*nc-1}:0] words; genvar p; generate for(p=0;p<{nc};p=p+1) begin: gp assign words[16*p+:16]={{6'd0,port_state[10*p+:10]}}; end endgenerate\nassign data=(r_pt<{nc}) ? words[16*r_pt[3:0]+:16] : 16'd0;\n"
                source=output/(tag+'-'+kind+'.v');source.write_text(header+body+'endmodule\n')
                log=run(tag+'-'+kind,f'read_verilog {source}; hierarchy -top cone; proc; flatten; opt; techmap; opt; abc -liberty {args.liberty.resolve()} -constr {constraint} {exclude}; stat -liberty {args.liberty.resolve()}')
                timing=re.findall(r'ABC:.*Gates\s*=\s*(\d+).*Delay\s*=\s*([\d.]+) ps',log)
                area=re.findall(r'Chip area for module.*?:\s*([\d.]+)',log)
                assert len(timing)==1 and area
                mapped[tag][kind]=dict(gates=int(timing[0][0]),delay_ps=float(timing[0][1]),area_um2=float(area[-1]))
    (output/'receipt.json').write_text(json.dumps(dict(reference_sha256=hashlib.sha256(reference.encode()).hexdigest(),
        candidate_sha256=hashlib.sha256(trial.encode()).hexdigest(),proofs=proofs,isolated_mapping=mapped,
        scope='Complete host/SPI equivalence at stated parameters; isolated mux mapping is not extracted timing or full-chip area'),indent=2)+'\n')
    print(json.dumps(proofs))


if __name__=='__main__':main()
