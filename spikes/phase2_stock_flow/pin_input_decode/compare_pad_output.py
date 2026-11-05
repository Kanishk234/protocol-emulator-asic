"""Prove and map mutually-exclusive owner mux factoring, without changing state."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--liberty', type=Path, required=True)
    parser.add_argument('--exclude-cells', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--yosys', default='yosys')
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    source = args.reference.read_text()
    start = source.index('    integer i, u;')
    end = source.index('\n`ifdef TRW_ASSERT_ON', start)
    original = source[start:end]
    replacement = '''    integer i, u;
    always @* begin
        pad_out = 16'd0;
        pad_oe = 16'd0;
        for (i=0; i<16; i=i+1)
            for (u=0; u<NU; u=u+1) begin
                pad_out[i] = pad_out[i]
                    | (({29'd0,own[3*i +: 3]} == u)
                       && ((({27'd0,pin_a[5*u +: 5]} == i+8) && a_out[u])
                           || (({27'd0,pin_a[5*u +: 5]} != i+8)
                               && ({27'd0,pin_n[5*u +: 5]} == i+8) && n_out[u])));
                pad_oe[i] = pad_oe[i]
                    | (({29'd0,own[3*i +: 3]} == u)
                       && ((({27'd0,pin_a[5*u +: 5]} == i+8) && a_oe[u])
                           || (({27'd0,pin_a[5*u +: 5]} != i+8)
                               && ({27'd0,pin_n[5*u +: 5]} == i+8) && n_oe[u])));
            end
    end
'''
    trial = source[:start] + replacement + source[end:]
    (root / 'parallel_owner.patch').write_text(''.join(difflib.unified_diff(
        source.splitlines(True), trial.splitlines(True),
        fromfile='a/src/trw_pins.v', tofile='b/src/trw_pins.v')))
    header = ''' #(parameter NU=4)(input [47:0] own,
input [NU-1:0] a_out,a_oe,n_out,n_oe,
input [5*NU-1:0] pin_a,pin_n,output reg [15:0] pad_out,pad_oe);
'''
    for name, body in [('reference', original), ('trial', replacement)]:
        (root / (name + '.v')).write_text('module ' + name + header + body + '\nendmodule\n')
    miter = '''module proof(input [47:0] own,input [3:0] a_out,a_oe,n_out,n_oe,
input [19:0] pin_a,pin_n,output equal);
wire [15:0] ro,re,to,te;
reference r(own,a_out,a_oe,n_out,n_oe,pin_a,pin_n,ro,re);
trial t(own,a_out,a_oe,n_out,n_oe,pin_a,pin_n,to,te);
assign equal=({ro,re}=={to,te}); endmodule
'''
    (root / 'proof.v').write_text(miter)

    def run(name, script):
        result = subprocess.run([args.yosys, '-Q', '-T', '-p', script], capture_output=True, text=True)
        (root / (name + '.log')).write_text(result.stdout + result.stderr)
        if result.returncode:
            raise ValueError(f'{name} failed; inspect log')
        return result.stdout

    files = f'{root / "reference.v"} {root / "trial.v"}'
    proof = run('proof', f'read_verilog {files} {root / "proof.v"}; '
                'prep -top proof -flatten; opt_clean; sat -verify -prove equal 1')
    if 'SUCCESS!' not in proof:
        raise ValueError('Proof marker absent')
    constr = root / 'abc.constr'
    constr.write_text('set_driving_cell sg13cmos5l_buf_2\nset_load 6\n')
    excluded = ['sg13cmos5l_buf_1'] + args.exclude_cells.read_text().split()
    exclusions = ' '.join('-dont_use ' + c for c in excluded)
    results = {}
    for name in ['reference', 'trial']:
        log = run(name + '-mapped', f'read_verilog {root / (name + ".v")}; '
                  f'hierarchy -top {name}; proc; flatten; opt; techmap; opt; '
                  f'abc -liberty {args.liberty.resolve()} -constr {constr} {exclusions}; '
                  f'stat -liberty {args.liberty.resolve()}')
        timing = re.findall(r'ABC:.*Gates\s*=\s*(\d+).*Delay\s*=\s*([\d.]+) ps', log)
        area = re.findall(r'Chip area for module.*?:\s*([\d.]+)', log)
        if len(timing) != 1 or len(area) != 1:
            raise ValueError('Missing unique mapping result')
        results[name] = {'mapped_gates': int(timing[0][0]), 'abc_delay_ps': float(timing[0][1]),
                         'mapped_area_um2': float(area[0])}
    receipt = {'scope': 'NU=4 combinational pad output/OE cone; arbitrary owners and unit data/config; '
               'state logic unchanged; BUF2 driver/6 fF output load; no routing or full-chip proof',
               'equivalent': True, 'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
               'candidate_sha256': hashlib.sha256(trial.encode()).hexdigest(),
               'liberty_sha256': hashlib.sha256(args.liberty.read_bytes()).hexdigest(),
               'excluded_cells': excluded, 'results': results}
    (root / 'comparison.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
