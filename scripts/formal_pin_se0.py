#!/usr/bin/env python3
"""Prove that registered BITSYNC SE0 implies the registered drive state."""
import argparse
import re
import subprocess
from pathlib import Path

from formal_channels import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', type=Path, default=ROOT / 'src/trw_pin_bs.v')
    args = parser.parse_args()
    source = args.source.read_text()
    # This proof concerns the drive invariant. The queue assertions have their
    # own proof harness with separate interface premises.
    source, count = re.subn(r'(?ms)^`ifdef TRW_ASSERT_ON\n.*?^`endif\n', '', source)
    if count != 1 or source.count('endmodule') != 1:
        raise ValueError('Unexpected BITSYNC module or assertion block')
    properties = """
    reg se0_initialized = 1'b0;
    always @(posedge clk)
        se0_initialized <= 1'b1;
    always @* begin
        if (!se0_initialized)
            assume(!rst_n);
        if (se0_initialized)
            assert(!se0_r || drv);
    end
"""
    source = source.replace('endmodule', properties + 'endmodule')
    old = "drv <= 1'b0;  tlv <= idle;  se0_r <= 1'b0;  jbit <= 1'b0;"
    if source.count(old) != 2:
        raise ValueError('Expected both release and listen-only state updates')
    mutant = source.replace(old, old.replace("se0_r <= 1'b0", "se0_r <= 1'b1"), 1)
    output = ROOT / 'build/formal_pin_se0'
    output.mkdir(parents=True, exist_ok=True)
    for name, rtl, options, expected in (
        ('se0_drive', source, '-seq 2 -tempinduct -verify', 'Induction step proven: SUCCESS!'),
        ('se0_on_release', mutant, '-seq 8', 'model found: FAIL!'),
    ):
        path = output / f'{name}.v'
        path.write_text(rtl)
        command = (
            f'read_verilog -formal -sv -I src build/formal_pin_se0/{name}.v; '
            'prep -top trw_pin_bs; chformal -lower; '
            f'sat {options} -set-assumes -prove-asserts'
        )
        result = subprocess.run(['yosys', '-QT', '-p', command], cwd=ROOT,
                                capture_output=True, text=True)
        log = output / f'{name}.log'
        log.write_text(result.stdout + result.stderr)
        if result.returncode or expected not in result.stdout:
            raise RuntimeError(f'{name}: expected {expected}; see {log}')
        print(f'{name}: {expected}')


if __name__ == '__main__':
    main()
