#!/usr/bin/env python3
"""Map the current TRIPWIRE top to Artix-7 primitives for a resource preflight."""
from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'build/basys3-preflight'


def main():
    project = yaml.safe_load((ROOT / 'info.yaml').read_text())['project']
    names = project['source_files']
    if names.count('trw_sram.v') != 1:
        raise ValueError('Expected one ASIC SRAM wrapper in the project sources')
    sources = [f'src/{name}' if name != 'trw_sram.v' else 'fpga/basys3/trw_sram.v'
               for name in names]
    top = project['top_module']
    OUTPUT.mkdir(parents=True, exist_ok=True)
    recipe = OUTPUT / 'synthesis.ys'
    recipe.write_text(
        'read_verilog -I src -DTRW_SLOTS_FLOPS -DTRW_PIN_CFG_FLOPS '
        + ' '.join(sources) + '\n'
        + f'synth_xilinx -family xc7 -top {top} -noiopad\n'
        + 'select -assert-count 1 t:RAMB18E1\n'
        + 'stat -tech xilinx\n'
    )
    log = OUTPUT / 'synthesis.log'
    with log.open('w') as stream:
        subprocess.run(['yosys', '-QT', '-s', str(recipe)], cwd=ROOT,
                       stdout=stream, stderr=subprocess.STDOUT, check=True)
    print(f'Artix-7 resource preflight passed: {log}')


if __name__ == '__main__':
    main()
