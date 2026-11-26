#!/usr/bin/env python3
"""Bounded reference-clock checks of single LEVEL and OE actions."""
import subprocess

from formal_channels import ROOT


def main():
    output = ROOT / 'build/formal_tx_cursor'
    output.mkdir(parents=True, exist_ok=True)
    source = (ROOT / 'src/trw_pin_tx.v').read_text()
    properties = (ROOT / 'formal/props/tx_cursor_bounded.vh').read_text()
    if source.count('endmodule') != 1:
        raise ValueError('Expected one module in the TX source')
    # Move the reference deadline by one edge as a negative control.
    wrong_deadline = properties.replace('test_decision + 2', 'test_decision + 3')
    if wrong_deadline == properties:
        raise ValueError('Missing reference deadline')
    for name, body, expected in (
        ('actual', properties, 'no model found: SUCCESS!'),
        ('late_oracle', wrong_deadline, 'model found: FAIL!'),
    ):
        design = output / f'{name}.v'
        design.write_text(source.replace('endmodule', body + 'endmodule'))
        for full in (0, 1):
            cmd = (
                f'read_verilog -formal -sv -I src build/formal_tx_cursor/{name}.v; '
                f'hierarchy -top trw_pin_tx -chparam FULL {full} -chparam USE_LEVEL_CACHE {full}; '
                'prep -top trw_pin_tx; chformal -lower; '
                'sat -seq 12 -set-assumes -prove-asserts'
            )
            run = subprocess.run(['yosys', '-QT', '-p', cmd], cwd=ROOT,
                                 check=True, capture_output=True, text=True)
            (output / f'{name}-{full}.log').write_text(run.stdout + run.stderr)
            if expected not in run.stdout:
                raise RuntimeError(f'Unexpected SAT result for {name}, FULL={full}')
            print(f'{name}, FULL={full}: {expected}')


if __name__ == '__main__':
    main()
