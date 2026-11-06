"""Prove isolated A/B selector rewrites and compare mapped combinational cost.

Run inside the project venv. Liberty/ABC estimates exclude placement and routing.
Raw outputs belong under ignored build/, not in the evidence directory.
"""
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
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--yosys', default='yosys')
    parser.add_argument('--exclude-cells', type=Path)
    parser.add_argument('--load-ff', type=float, default=6)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    reference = args.reference.read_text()
    evidence = json.loads((Path(__file__).parent / 'c_select_candidate.json').read_text())
    assert hashlib.sha256(reference.encode()).hexdigest() == evidence['reference_sha256']
    reference = reference.replace(
        '    // Index the pad vector only with in-range values (the `*_on` checks pick the default otherwise).',
        '    // A/B retain bounded indexing. C defaults mask any unattached index.')
    reference = reference.replace("    wire       c_pad = pads[c_on ? pin_c : 5'd0];", '    wire c_pad = pads[pin_c];')
    reference = reference.replace('    assign sel  = (c_in == c_active);','    assign sel = !c_on || (c_pad == c_active);')
    assert hashlib.sha256(reference.encode()).hexdigest() == evidence['candidate_sha256']
    a_old = "    wire       a_pad = pads[a_on ? a_idx : 5'd0];"
    b_old = "    wire       b_pad = pads[b_on ? pin_b : 5'd0];"
    assert reference.count(a_old) == reference.count(b_old) == 1
    choices = {'reference': reference,
               'a_unclamped': reference.replace(a_old,'    wire a_pad = pads[a_idx];'),
               'ab_unclamped': reference.replace(a_old,'    wire a_pad = pads[a_idx];').replace(b_old,'    wire b_pad = pads[pin_b];')}
    choices['a_banked'] = reference.replace(a_old, """    wire [2:0] a_bank;
    assign a_bank[0] = pads[7:0] >> a_idx[2:0];
    assign a_bank[1] = pads[15:8] >> a_idx[2:0];
    assign a_bank[2] = pads[23:16] >> a_idx[2:0];
    wire a_pad = a_bank[a_idx[4:3]];""")
    choices['a_parallel_priority'] = reference.replace(
        '    assign a_in = a_on ? a_pad : idle;',
        "    assign a_in = s_on ? pads[pin_s] : ((pin_a < 5'd24) ? pads[pin_a] : idle);")
    choices['a_decoded'] = reference.replace(a_old, """    reg a_pad;
    integer ai;
    always @* begin
        a_pad = 1'b0;
        for (ai=0; ai<24; ai=ai+1)
            a_pad = a_pad | (pads[ai] && (a_idx == ai));
    end""").replace('    assign a_in = a_on ? a_pad : idle;',
                    '    assign a_in = a_pad | (!a_on && idle);')
    choices['a_parallel_priority'] = choices['a_parallel_priority'].replace(
        "    wire [4:0] a_idx = s_on ? pin_s : pin_a;\n", '').replace(
        "    wire       a_on  = (a_idx < 5'd24);\n", '').replace(a_old+'\n','').replace(
        '    // A/B retain bounded indexing. C defaults mask any unattached index.',
        '    // A selects S/A in parallel; B retains bounded indexing; unattached C is masked.')
    constr = root / 'abc.constr'
    constr.write_text(f'set_driving_cell sg13cmos5l_buf_2\nset_load {args.load_ff}\n')
    excluded = ['sg13cmos5l_buf_1']
    if args.exclude_cells:
        excluded += [line.strip() for line in args.exclude_cells.read_text().splitlines()
                     if line.strip() and not line.startswith('#')]
    exclusions = ' '.join('-dont_use ' + name for name in excluded)

    def run(name, script):
        result = subprocess.run([args.yosys, '-Q', '-T', '-p', script],
                                text=True, capture_output=True)
        (root / (name + '.log')).write_text(result.stdout + result.stderr)
        if result.returncode:
            raise ValueError(f'{name} failed; inspect its log')
        return result.stdout

    results = {}
    for name, source in choices.items():
        file = root / (name + '.v')
        file.write_text(source.replace('module trw_pin_io (', f'module {name} ('))
        proof = name == 'reference'
        if not proof:
            miter = root / (name + '-proof.v')
            ports = 'a_in,b_in,c_in,sel'
            text = ('module proof(input clk,input [23:0] pads, '
                    'input [4:0] pin_a,pin_s,pin_b,pin_c, '
                    'input idle,c_active,output equal);\n')
            for inst, module in [('r', 'reference'), ('t', name)]:
                text += 'wire ' + ','.join(inst + '_' + p for p in ports.split(',')) + ';\n'
                ins = ','.join(f'.{p}({p})' for p in
                               ['clk', 'pads', 'pin_a', 'pin_s', 'pin_b', 'pin_c', 'idle', 'c_active'])
                outs = ','.join(f'.{p}({inst}_{p})' for p in ports.split(','))
                text += f'{module} {inst}({ins},{outs});\n'
            text += 'assign equal={' + ','.join('r_' + p for p in ports.split(','))
            text += '}=={' + ','.join('t_' + p for p in ports.split(',')) + '}; endmodule\n'
            miter.write_text(text)
            log = run(name + '-proof', f'read_verilog {root / "reference.v"} {file} {miter}; '
                      'prep -top proof -flatten; opt_clean; sat -verify -prove equal 1')
            proof = 'SUCCESS!' in log
            if not proof:
                raise ValueError('Proof success marker absent')
            (root / (name + '.patch')).write_text(''.join(difflib.unified_diff(
                reference.splitlines(True), source.splitlines(True),
                fromfile='a/src/trw_pin_io.v', tofile='b/src/trw_pin_io.v')))
        wrapper = root / (name + '-cone.v')
        wrapper.write_text('module cone(input [23:0] pads,input [4:0] pin_a,pin_s,pin_b, '
                           'input idle,output a_in,b_in);\n'
                           f"{name} dut(.clk(1'b0),.pads(pads),.pin_a(pin_a),"
                           ".pin_s(pin_s),.pin_b(pin_b),.pin_c(5'd31),"
                           ".idle(idle),.c_active(1'b0),.a_in(a_in),.b_in(b_in)); endmodule\n")
        log = run(name + '-mapped', f'read_verilog {file} {wrapper}; '
                  'hierarchy -top cone; proc; flatten; opt; techmap; opt; '
                  f'abc -liberty {args.liberty.resolve()} -constr {constr} '
                  f'{exclusions}; '
                  f'stat -liberty {args.liberty.resolve()}; write_json {root / (name + "-mapped.json")}')
        timing = re.findall(r'ABC:.*Gates\s*=\s*(\d+).*Delay\s*=\s*([\d.]+) ps', log)
        if len(timing) != 1:
            raise ValueError('Expected one ABC delay summary')
        area = re.findall(r'Chip area for module.*?:\s*([\d.]+)', log)
        results[name] = {'equivalent': proof, 'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                         'mapped_area_um2': float(area[-1]) if area else None,
                         'mapped_gates': int(timing[0][0]),
                         'abc_delay_ps': float(timing[0][1])}
    receipt = {'scope': 'A/B-pin combinational cone only, reference includes verified C rewrite; BUF2 input driver; '
               'ABC Liberty estimates, no extracted wires or full-design physical proof',
               'output_load_ff': args.load_ff,
               'reference_sha256': hashlib.sha256(reference.encode()).hexdigest(),
               'liberty_sha256': hashlib.sha256(args.liberty.read_bytes()).hexdigest(),
               'excluded_cells': excluded,
               'results': results}
    (root / 'comparison.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
