#!/usr/bin/env python3
"""Build the full Basys 3 design and check its routed internal clock timing."""
import shutil
import subprocess
import tempfile
from pathlib import Path

from check_basys3_synthesis import ROOT, project_sources


WINDOWS_DRIVE = Path('/mnt/c')
CMD_EXE = WINDOWS_DRIVE / 'Windows/System32/cmd.exe'


def windows_vivado():
    if not CMD_EXE.is_file() or shutil.which('wslpath') is None:
        return None
    installations = [
        *((path.parents[2].name, path) for path in
          WINDOWS_DRIVE.glob('AMDDesignTools/*/Vivado/bin/vivado.bat')),
        *((path.parents[2].name, path) for path in
          WINDOWS_DRIVE.glob('Xilinx/Vivado/*/bin/vivado.bat')),
    ]
    return max(installations, default=('', None))[1]


def windows_argument(path, style='-m'):
    converted = subprocess.check_output(['wslpath', style, str(path)], text=True).strip()
    if any(char in converted for char in '"%!^&|<>()\r\n'):
        raise ValueError(f'Cannot pass this path through Windows cmd.exe: {path}')
    return converted


def main():
    vivado = shutil.which('vivado')
    batch = windows_vivado() if vivado is None else None
    if vivado is None and batch is None:
        raise SystemExit('Vivado is required for Basys 3 placement, routing and bitstream generation')
    _, sources = project_sources()
    sources.append('fpga/basys3/tripwire_basys3.v')
    output = ROOT / 'build'
    output.mkdir(exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix='basys3-vivado-', dir=output))
    print(f'Vivado run directory: {run}', flush=True)
    script = ROOT / 'fpga/basys3/build.tcl'
    arguments = [ROOT, run, *(ROOT / source for source in sources)]
    if batch is not None:
        command = [str(CMD_EXE), '/d', '/c', windows_argument(batch, '-w'),
                   '-mode', 'batch', '-nojournal', '-nolog', '-source',
                   windows_argument(script), '-tclargs', *map(windows_argument, arguments)]
        with (run / 'vivado.log').open('w') as stream:
            subprocess.run(command, cwd=WINDOWS_DRIVE,
                           stdout=stream, stderr=subprocess.STDOUT, check=True)
    else:
        subprocess.run([vivado, '-mode', 'batch', '-source', str(script), '-tclargs',
                        *map(str, arguments)], cwd=run, check=True)


if __name__ == '__main__':
    main()
