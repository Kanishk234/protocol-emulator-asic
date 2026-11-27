#!/usr/bin/env python3
"""Bounded reference-clock checks of LEVEL and OE actions."""
import subprocess

from formal_channels import ROOT


def main():
    output = ROOT / 'build/formal_tx_cursor'
    output.mkdir(parents=True, exist_ok=True)
    source = (ROOT / 'src/trw_pin_tx.v').read_text()
    if source.count('endmodule') != 1:
        raise ValueError('Expected one module in the TX source')
    check(output, source, 'bounded', 'test_decision', 12)
    check(output, source, 'queued', 'test_second_due', 24)
    check(output, source, 'sync_gap', 'test_decision', 18)


def check(output, source, scenario, deadline, depth):
    properties = (ROOT / f'formal/props/tx_cursor_{scenario}.vh').read_text()
    # Move the reference deadline by one edge as a negative control.
    wrong_deadline = properties.replace(f'{deadline} + 2', f'{deadline} + 3')
    if wrong_deadline == properties:
        raise ValueError('Missing reference deadline')
    for name, body, expected in (
        ('actual', properties, 'no model found: SUCCESS!'),
        ('late_oracle', wrong_deadline, 'model found: FAIL!'),
    ):
        design = output / f'{scenario}-{name}.v'
        design.write_text(source.replace('endmodule', body + 'endmodule'))
        for full in (0, 1):
            cmd = (
                f'read_verilog -formal -sv -I src build/formal_tx_cursor/{design.name}; '
                f'hierarchy -top trw_pin_tx -chparam FULL {full} -chparam USE_LEVEL_CACHE {full}; '
                'prep -top trw_pin_tx; chformal -lower; '
                f'sat -seq {depth} -set-assumes -prove-asserts'
            )
            run = subprocess.run(['yosys', '-QT', '-p', cmd], cwd=ROOT,
                                 check=True, capture_output=True, text=True)
            (output / f'{scenario}-{name}-{full}.log').write_text(run.stdout + run.stderr)
            if expected not in run.stdout:
                raise RuntimeError(f'Unexpected SAT result for {scenario}/{name}, FULL={full}')
            print(f'{scenario}/{name}, FULL={full}: {expected}')


if __name__ == '__main__':
    main()
