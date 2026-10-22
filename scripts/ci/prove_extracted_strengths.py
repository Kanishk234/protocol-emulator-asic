"""Combinational Liberty equivalence for the eleven extracted-path size changes."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess

PAIRS = [
    ('nor3_1', 'nor3_2', ['A','B','C'], 'Y'),
    ('a21oi_1', 'a21oi_2', ['A1','A2','B1'], 'Y'),
    ('buf_1', 'buf_4', ['A'], 'X'),
    ('inv_1', 'inv_2', ['A'], 'Y'),
    ('nand2_1', 'nand2_2', ['A','B'], 'Y'),
    ('and2_1', 'and2_2', ['A','B'], 'X'),
    ('buf_1', 'buf_2', ['A'], 'X'),
]


def prove(library_dir, output, *, pairs=None):
    pairs = PAIRS if pairs is None else pairs
    if not pairs:
        raise ValueError('Missing strength equivalence targets')
    output = Path(output).resolve()
    output.mkdir(exist_ok=False)
    wrapper = ''
    for variant, module in enumerate(('gold','gate')):
        wrapper += f'module {module}(input a,b,c,output [{len(pairs)-1}:0] y);\n'
        for i, (old,new,pins,out) in enumerate(pairs):
            ports = ','.join('.'+p+'('+v+')' for p,v in zip(pins, ['a','b','c']))
            wrapper += f'sg13cmos5l_{(old,new)[variant]} u{i}({ports},.{out}(y[{i}]));\n'
        wrapper += 'endmodule\n'
    (output/'wrapper.v').write_text(wrapper)
    result = []
    for corner in ('slow_1p08V_125C','typ_1p20V_25C','fast_1p32V_m40C'):
        lib = (Path(library_dir)/('sg13cmos5l_stdcell_'+corner+'.lib')).resolve()
        script = f'''read_liberty -ignore_miss_func {lib}
read_verilog wrapper.v
proc
flatten gold gate
opt
equiv_make gold gate equiv
hierarchy -top equiv
equiv_simple
equiv_status -assert
'''
        (output/(corner+'.ys')).write_text(script)
        with (output/(corner+'.log')).open('w') as log:
            subprocess.run(['yosys','-Q','-s',corner+'.ys'],cwd=output,
                           stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
        text = (output/(corner+'.log')).read_text()
        proven = re.search(r'Of those cells (\d+) are proven and 0 are unproven', text)
        if 'Equivalence successfully proven!' not in text or not proven or int(proven[1]) < len(pairs):
            raise ValueError('Incomplete strength equivalence proof')
        result.append(dict(corner=corner, proven_outputs=len(pairs),equivalence_points=int(proven[1]),
                           library_sha256=hashlib.sha256(lib.read_bytes()).hexdigest()))
    (output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('library_dir',type=Path)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    print(json.dumps(prove(args.library_dir,args.output),indent=2))
