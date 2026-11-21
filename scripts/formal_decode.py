#!/usr/bin/env python3
"""Check the lane's field slices against YAML over arbitrary instruction words."""
import re
import subprocess

import yaml

from formal_channels import ROOT


ROUTINE_SIGNALS = {
    'LDI': {'rd': 'rt_crd', 'imm': 'rt_imm'},
    'LDIH': {'rd': 'rt_crd', 'imm': 'rt_imm'},
    'BR': {'cond': 'rt_cond', 'off': 'rt_boff'},
    'DJNZ': {'rd': 'rt_crd', 'off': 'rt_joff'},
    'LD': {'rd': 'rt_crd', 'ra': 'rt_mra', 'off': 'rt_moff'},
    'ST': {'rd': 'rt_crd', 'ra': 'rt_mra', 'off': 'rt_moff'},
    'OUT': {'port': 'rt_port', 'tag': 'rt_otag', 'ra': 'rt_ora'},
    'SYS': {'fn': 'rt_fn', 'arg': 'rt_arg'},
}


def field_checks(spec, lane):
    declarations = {}
    checks = []

    def add(signal, bounds, source, word):
        hi, lo = bounds
        if signal not in declarations:
            pattern = rf'^\s*((?:wire\s+(?:\[[^\]]+\]\s*)?|assign\s+){signal}\s*=\s*[^;]+;)'
            matches = re.findall(pattern, source, re.M)
            if len(matches) != 1:
                raise ValueError(f'Expected one decoder expression for {signal}')
            declarations[signal] = matches[0]
        checks.append(f'assert({signal} == {word}[{hi}:{lo}]);')

    start = lane.index('begin : g_cond')
    conditions = lane[start:lane.index('endgenerate', start)].replace('urgent[i]', 'urgent_value')
    for field in spec['slot']['fields']:
        name = field['name'].lower()
        lo = field['lsb']
        bounds = (lo + field['width'] - 1, lo)
        if field['group'] == 'condition' or name in ('op', 'dst', 'asrc'):
            add('urgent_value' if name == 'u' else name, bounds, conditions, 's')
        if field['group'] == 'action':
            add(f's_{name}', bounds, lane, 'ss')

    routine = spec['routine']
    ctl = routine['bits'] - 1
    add('rt_ctl', (ctl, ctl), lane, 'a_lat')
    add('rt_sub', routine['ctrl']['sub'], lane, 'a_lat')
    alu_fields = dict(op='rt_aop', rd='rt_ard', ra='rt_ara', bs='rt_bs', b='rt_b')
    for field, bounds in routine['alu']['fields'].items():
        add(alu_fields[field], bounds, lane, 'a_lat')
    for layout in routine['ctrl']['formats']:
        for field, bounds in layout['fields'].items():
            add(ROUTINE_SIGNALS[layout['name']][field], bounds, lane, 'a_lat')
    return list(declarations.values()), checks


def main():
    spec = yaml.safe_load((ROOT / 'spec/tripwire.yaml').read_text())
    lane = (ROOT / 'src/trw_lane.v').read_text()
    declarations, checks = field_checks(spec, lane)
    slot_msb = spec['slot']['bits'] - 1
    word_msb = spec['routine']['bits'] - 1
    header = f'module decode_contract(input [{slot_msb}:0] s, ss, input [{word_msb}:0] a_lat);'
    hdl = '\n'.join(['`include "trw_defs.vh"', header, 'wire urgent_value;', *declarations,
                     'always @* begin', *checks, 'end', 'endmodule', ''])
    out = ROOT / 'build/formal_decode'
    out.mkdir(parents=True, exist_ok=True)
    original = 's[`TRW_SLOT_TAG_MSB:`TRW_SLOT_TAG_LSB]'
    if hdl.count(original) != 1:
        raise ValueError('Expected one slot-tag decoder for the negative control')
    for name, source, expect_pass in (
        ('decode', hdl, True),
        ('corrupt_tag', hdl.replace(original, f'({original} ^ 2\'b01)'), False),
    ):
        design = out / f'{name}.v'
        design.write_text(source)
        run = subprocess.run(
            ['yosys', '-QT', '-p', f'read_verilog -formal -sv -I src build/formal_decode/{name}.v; '
             'prep -top decode_contract; chformal -lower; sat -prove-asserts -show-inputs'],
            cwd=ROOT, check=True, capture_output=True, text=True)
        (out / f'{name}.log').write_text(run.stdout + run.stderr)
        expected = 'no model found: SUCCESS!' if expect_pass else 'model found: FAIL!'
        if expected not in run.stdout:
            raise RuntimeError(f'Unexpected SAT result for {name}')
    print(f'{len(checks)} field-slice checks passed for arbitrary words, and the corrupt tag was rejected')


if __name__ == '__main__':
    main()
