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
    check(output, source, 'bounded', 'test_decision', 28)
    check(output, source, 'queued', 'test_second_due', 24)
    check(output, source, 'sync_gap', 'test_decision', 29)
    guard = 'wire pend_ok = !pend_v || (pend_go && (pend_k != K_START));'
    if source.count(guard) != 1:
        raise ValueError('Expected one pending admission guard')
    properties = (ROOT / 'formal/props/tx_pending.vh').read_text()
    verify(output, 'pending-native', source, properties,
           '-seq 3 -tempinduct -verify', 'Induction step proven: SUCCESS!')
    verify(output, 'pending-unguarded', source.replace(guard, "wire pend_ok = 1'b1;"),
           properties, '-seq 6', 'model found: FAIL!')
    sample = 'smp       <= (pend_go && pend_k == K_SMP) || (tk_now && c_smp);'
    if source.count(sample) != 1:
        raise ValueError('Expected one SAMPLE dispatch assignment')
    verify(output, 'pending-lost-sample', source.replace(sample, 'smp       <= (tk_now && c_smp);'),
           properties, '-seq 8', 'model found: FAIL!')
    start = "p_act   <= 1'b1;"
    if source.count(start) != 1:
        raise ValueError('Expected one burst start assignment')
    verify(output, 'pending-lost-start', source.replace(start, "p_act   <= 1'b0;"),
           properties, '-seq 8', 'model found: FAIL!')
    oe_update = 'oe <= due_oe;'
    if source.count(oe_update) != 1:
        raise ValueError('Expected one pad output-enable update')
    verify(output, 'pending-lost-oe', source.replace(oe_update, 'oe <= oe;'),
           properties, '-seq 8', 'model found: FAIL!')
    carrier_mask = 'nlvx[0] && !(car_on && cph_next)'
    if source.count(carrier_mask) != 1:
        raise ValueError('Expected one cached carrier mask')
    verify(output, 'pending-uncarried', source.replace(carrier_mask, 'nlvx[0]'),
           properties, '-seq 8', 'model found: FAIL!', configurations=(1,))


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
        verify(output, f'{scenario}-{name}', source, body, f'-seq {depth}', expected)


def verify(output, name, source, properties, options, expected, configurations=(0, 1)):
    design = output / f'{name}.v'
    design.write_text(source.replace('endmodule', properties + 'endmodule'))
    for full in configurations:
        cmd = (
            f'read_verilog -formal -sv -I src build/formal_tx_cursor/{design.name}; '
            f'hierarchy -top trw_pin_tx -chparam FULL {full} -chparam USE_LEVEL_CACHE {full}; '
            f'prep -top trw_pin_tx; chformal -lower; sat {options} -set-assumes -prove-asserts'
        )
        run = subprocess.run(['yosys', '-QT', '-p', cmd], cwd=ROOT,
                             check=True, capture_output=True, text=True)
        (output / f'{name}-{full}.log').write_text(run.stdout + run.stderr)
        if expected not in run.stdout:
            raise RuntimeError(f'Unexpected SAT result for {name}, FULL={full}')
        print(f'{name}, FULL={full}: {expected}')


if __name__ == '__main__':
    main()
