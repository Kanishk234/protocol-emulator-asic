#!/usr/bin/env python3
"""Map the current TRIPWIRE top to Artix-7 primitives for a resource preflight."""
import argparse
from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'build/basys3-preflight'


def project_sources():
    project = yaml.safe_load((ROOT / 'info.yaml').read_text())['project']
    names = project['source_files']
    if names.count('trw_sram.v') != 1:
        raise ValueError('Expected one ASIC SRAM wrapper in the project sources')
    sources = [f'src/{name}' if name != 'trw_sram.v' else 'fpga/basys3/trw_sram.v'
               for name in names]
    return project['top_module'], sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', action='store_true', help='Include the Basys 3 clock and board I/O adapter')
    args = parser.parse_args()
    top, sources = project_sources()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    recipe = OUTPUT / 'synthesis.ys'
    log = OUTPUT / 'synthesis.log'
    libraries = ''
    io_options = ' -noiopad'
    board_checks = ''
    if args.board:
        sources.append('fpga/basys3/tripwire_basys3.v')
        top = 'tripwire_basys3'
        recipe = OUTPUT / 'board-synthesis.ys'
        log = OUTPUT / 'board-synthesis.log'
        libraries = 'read_verilog -lib +/xilinx/cells_xtra.v\n'
        io_options = ''
        board_checks = ('select -assert-count 1 t:MMCME2_BASE\n'
                        'select -assert-count 8 t:IOBUF\n')
    recipe.write_text(
        'read_verilog -I src -DTRW_SLOTS_FLOPS -DTRW_PIN_CFG_FLOPS '
        + ' '.join(sources) + '\n'
        + libraries
        + f'synth_xilinx -family xc7 -top {top}{io_options}\n'
        + 'select -assert-count 1 t:RAMB18E1\n'
        + board_checks
        + 'check -assert\n'
        + 'stat -tech xilinx\n'
    )
    with log.open('w') as stream:
        subprocess.run(['yosys', '-QT', '-s', str(recipe)], cwd=ROOT,
                       stdout=stream, stderr=subprocess.STDOUT, check=True)
    print(f'Artix-7 resource preflight passed: {log}')


if __name__ == '__main__':
    main()
