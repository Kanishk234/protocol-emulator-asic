#!/usr/bin/env python3
"""Check known pads and resettable flop outputs after routed firmware startup."""
import argparse
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CHIP_TESTS = ROOT / 'test_internal/chip'
FLOP = re.compile(r'^\s*sg13cmos5l_dfrbpq_1\s+(\S+)\s+\(', re.M)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('netlist', type=Path)
    parser.add_argument('--pdk-root', type=Path, required=True)
    parser.add_argument('--iverilog-root', type=Path, required=True,
                        help='Tiny Tapeout Icarus 13 installation usr directory')
    args = parser.parse_args()
    netlist = args.netlist.resolve()
    iv = args.iverilog_root.resolve()
    instances = FLOP.findall(netlist.read_text())
    if not instances:
        raise ValueError('No sg13cmos5l_dfrbpq_1 flop instances found')
    shell = (CHIP_TESTS / 'tb_chip_gl.v').read_text()
    if shell.count('endmodule') != 1:
        raise ValueError('Expected one gate-level harness module')
    output = ROOT / 'build/routed-xprop'
    output.mkdir(parents=True, exist_ok=True)
    declarations = f'    wire [{len(instances) - 1}:0] routed_flops;\n'
    declarations += ''.join(
        f'    assign routed_flops[{index}] = u_dut.{instance} .Q;\n'
        for index, instance in enumerate(instances)
    )
    (output / 'tb_chip_gl.v').write_text(shell.replace('endmodule', declarations + 'endmodule'))
    lib = iv / 'lib/ivl'
    env = os.environ.copy()
    env.update(PATH=f"{iv / 'bin'}{os.pathsep}{env['PATH']}",
               IVERILOG_VPI_MODULE_PATH=str(lib), COMPILE_ARGS=f'-B {lib}',
               PYTHONPATH=os.pathsep.join(filter(None, (str(CHIP_TESTS), env.get('PYTHONPATH')))))
    log = output / 'run.log'
    with log.open('w') as stream:
        subprocess.run([
            'make', '-f', str(CHIP_TESTS / 'Makefile'), 'GATES=yes', 'SIM=icarus',
            f'NETLIST={netlist}', f'PDK_ROOT={args.pdk_root.resolve()}', f'TB_DIR={output}',
            f'MACRO_DIR={ROOT / "macro/RM_IHPSG13_1P_512x16_c2_bm_bist"}',
            'COCOTB_TEST_MODULES=test_xprop_routed', 'COCOTB_RESULTS_FILE=results.xml',
        ], cwd=output, env=env, stdout=stream, stderr=subprocess.STDOUT, check=True)
    print(f'Known pad and {len(instances)} monitored flop outputs after firmware startup. Evidence: {log}')


if __name__ == '__main__':
    main()
