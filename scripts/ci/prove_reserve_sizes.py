"""Prove the two library strength substitutions, including flop reset behavior."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def prove(library_dir, output):
    output = Path(output).resolve()
    output.mkdir(exist_ok=True)
    wrappers = ''
    for name, size in [('gold', 1), ('gate', 2)]:
        wrappers += f'''module {name}(input clk,rst_n,d,a,b,c,output q,y);
sg13cmos5l_dfrbpq_{size} u_reg(.CLK(clk),.RESET_B(rst_n),.D(d),.Q(q));
sg13cmos5l_nor3_{size} u_gate(.A(a),.B(b),.C(c),.Y(y));
endmodule
'''
    (output/'wrappers.v').write_text(wrappers)
    receipts = []
    for corner in ['slow_1p08V_125C', 'typ_1p20V_25C', 'fast_1p32V_m40C']:
        lib = (Path(library_dir)/f'sg13cmos5l_stdcell_{corner}.lib').resolve()
        # An unrelated ICG internal output lacks a Liberty function. It is not
        # instantiated here; both resized cells must flatten and prove q/y.
        script = f'''read_liberty -ignore_miss_func {lib}
read_verilog wrappers.v
proc
flatten gold gate
opt
memory
opt
equiv_make gold gate equiv
hierarchy -top equiv
clk2fflogic
opt_clean
equiv_simple
equiv_induct -seq 2
equiv_status -assert
'''
        (output/(corner+'.ys')).write_text(script)
        with (output/(corner+'.log')).open('w') as log:
            subprocess.run(['yosys', '-Q', '-s', corner+'.ys'], cwd=output,
                           stdout=log, stderr=subprocess.STDOUT, timeout=60, check=True)
        text = (output/(corner+'.log')).read_text()
        match = re.search(r'Of those cells (\d+) are proven and 0 are unproven', text)
        if not match or int(match[1]) < 2 or 'Equivalence successfully proven!' not in text:
            raise ValueError('Incomplete resized-cell functional proof')
        receipts.append(dict(corner=corner, points=int(match[1]),
                             library_sha256=hashlib.sha256(lib.read_bytes()).hexdigest()))
    (output/'receipt.json').write_text(json.dumps(receipts, indent=2)+'\n')
    return receipts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('library_dir', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(prove(args.library_dir, args.output), indent=2))
