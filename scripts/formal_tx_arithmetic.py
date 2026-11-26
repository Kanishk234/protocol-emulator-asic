#!/usr/bin/env python3
"""Prove the isolated TX cursor arithmetic for all quotient, delay and prescaler values."""
import subprocess

from formal_channels import ROOT


def region(source, first, last):
    start = source.index(first)
    return source[start:source.index(last, start)]


def main():
    source = (ROOT / 'src/trw_pin_tx.v').read_text()
    output = ROOT / 'build/formal_tx_arithmetic'
    output.mkdir(parents=True, exist_ok=True)
    subtract = region(source, '    wire [16:0] q_sub_eq', '    // ----')
    advance = region(source, '    reg [15:0] qn;', '    always @(posedge clk)')
    quotient = ''.join(
        region(source, f'    wire [15:0] {signal}', '\n') + '\n'
        for signal in ('q_eff', 'q_b ')
    )
    harness = """module cursor_arithmetic(
    input [15:0] eq,
    input [7:0] r_b, presc,
    input [11:0] h_d,
    input w_fire, use_pe, pe_m1,
    input tk, h_ext, c_sync, tk_late, c_gap, tk_timed
);
""" + quotient + subtract + advance + (ROOT / 'formal/props/tx_cursor_arithmetic.vh').read_text() + 'endmodule\n'
    mutant = harness.replace("wide_delta < -18'sd32768", "wide_delta < -18'sd32767")
    if mutant == harness:
        raise ValueError('Missing range-check negative control')
    for name, text, expected in (
        ('native', harness, 'no model found: SUCCESS!'),
        ('wrong_boundary', mutant, 'model found: FAIL!'),
    ):
        path = output / f'{name}.v'
        path.write_text(text)
        command = (
            f'read_verilog -formal -sv build/formal_tx_arithmetic/{name}.v; '
            'prep -top cursor_arithmetic; chformal -lower; sat -set-assumes -prove-asserts'
        )
        result = subprocess.run(['yosys', '-QT', '-p', command], cwd=ROOT,
                                capture_output=True, text=True, check=True)
        (output / f'{name}.log').write_text(result.stdout + result.stderr)
        if expected not in result.stdout:
            raise RuntimeError(f'{name}: expected {expected}')
        print(f'{name}: {expected}')


if __name__ == '__main__':
    main()
