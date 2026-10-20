"""Bounded G1 baseline census for R1; compile evidence, not physical timing."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'test_internal'))
from compile import compile as compiler
from compile.bitfile import BitFile
from cloud_arch_comparison import run_bounded, require_nonfit_fatals

SINGLES = ('uart', 'spi_ctrl', 'i2c_ctrl', 'ws2812', 'onewire', 'swd', 'i2c_target')
CASES = (*SINGLES, 'uart_spi_11', 'uart_spi_10', 'uart_spi_01', 'uart_spi_00')
OUT = ROOT / 'build/fresh_baseline'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def specification(name):
    if name not in CASES:
        raise ValueError('Unknown baseline case')
    if name in SINGLES:
        folder = ROOT / 'protocols' / name
        pins = folder / 'pins.yaml'
        sources = sorted(folder.glob('*.v'))
        params = dict(yaml.safe_load(pins.read_text())['params'])
        params['PRIMS'] = 1
    else:
        pins = ROOT / 'protocols/uart_spi/concurrency.yaml'
        sources = sorted((ROOT / 'protocols/uart').glob('*.v')) + [
            ROOT / 'protocols/spi_ctrl/spi_ctrl_top.v', ROOT / 'protocols/uart_spi/uart_spi_top.v']
        params = dict(yaml.safe_load(pins.read_text())['params'])
        params.update(UART_PRIMS=int(name[-2]), SPI_PRIMS=int(name[-1]))
    return pins, sources, params


def validate(directory, name):
    directory = Path(directory)
    pins, _, params = specification(name)
    row = json.loads((directory / 'case.json').read_text())
    if row['name'] != name or row['params'] != params or row['seed'] != 1:
        raise ValueError('Case identity/parameters differ')
    top = yaml.safe_load(pins.read_text())['top']
    if compiler.chparam(params, top) not in (directory / 'synth.ys').read_text().splitlines():
        raise ValueError('Synthesis parameters differ')
    estimate = compiler.cell_estimate(directory / 'design.json', 'warp_top')
    if estimate != row['synthesis_estimate']:
        raise ValueError('Synthesis resource estimate differs')
    if row['fits'] is True:
        report = json.loads((directory / 'report.json').read_text())
        util, fmax = compiler.parse_pnr_log(directory / 'pnr.log')
        if (report['params'] != params or report['arch'] != 'warp_g1' or report['design'] != top
                or report['build_options']['seed'] != 1
                or report['tools'] != row['tools'] or report['timing_corner'] != compiler.SLOW_CORNER
                or report['utilisation'] != util or report['fmax_mhz'] != fmax):
            raise ValueError('Native successful report mismatch')
        if not util or any(v['used'] > v['available'] for v in util.values()):
            raise ValueError('Successful design exceeds resources')
        if not report['provenance']['inputs']:
            raise ValueError('Missing source fingerprints')
        if report['meets_50mhz'] != (fmax is not None and fmax >= 50):
            raise ValueError('Model clock assessment differs')
        for item in report['provenance']['inputs']:
            if sha(item['path']) != item['sha256']:
                raise ValueError('Successful source fingerprint differs')
        images = list(directory.glob('*.wbit'))
        if len(images) != 1:
            raise ValueError('Missing/ambiguous image')
        image = BitFile.load(images[0])
        if (image.arch_version != 3 or len(image.words) != report['words']
                or f'0x{image.crc:08X}' != report['crc32']
                or sha(images[0]) != report['provenance']['bitfile_sha256']):
            raise ValueError('Image identity/CRC mismatch')
        if name.startswith('uart_spi') and (report['unmapped_inputs_tied_0'] or report['unmapped_outputs_open']):
            raise ValueError('Concurrent workload has unmapped ports')
        row.update(placed_utilisation=util, model_fmax_mhz=fmax,
                   model_meets_50mhz=report['meets_50mhz'], words=report['words'])
    elif row['fits'] is False:
        failure = json.loads((directory / 'failure.json').read_text())
        diagnosis = failure['diagnosis']
        native_util, _ = compiler.parse_pnr_log(directory / 'pnr_stdout.log')
        native = compiler.diagnose_pnr_failure((directory / 'pnr_stdout.log').read_text(), native_util)
        if (failure['stage'] != 'place_route' or failure['arch'] != 'warp_g1'
                or failure['seed'] != 1 or failure['tools'] != row['tools']
                or diagnosis != native or diagnosis['category'] not in ('resource_capacity', 'placement')):
            raise ValueError('Unqualified native nonfit')
        require_nonfit_fatals(diagnosis)
        if (directory / 'report.json').exists() or list(directory.glob('*.wbit')):
            raise ValueError('Rejected case has successful artifacts')
        row.update(failure_category=diagnosis['category'], native_diagnosis=diagnosis,
                   placed_utilisation=None)
    else:
        raise ValueError('Nonboolean fits')
    row['artifact_sha256'] = {str(p.relative_to(directory)): sha(p)
                             for p in sorted(directory.rglob('*')) if p.is_file()}
    return row


def worker(name, path):
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('Compiler measurement is hosted-only')
    pins, sources, params = specification(name)
    directory = Path(path)
    directory.mkdir(exist_ok=False)
    row = dict(name=name, params=params, seed=1, fits=False, tools=compiler.tool_versions())
    try:
        compiler.compile_design(sources, pins, ROOT / 'arch/warp_g1', directory,
                                seed=1, set_params=params, strict_ports=name.startswith('uart_spi'))
        row['fits'] = True
    except compiler.CompileError:
        if not (directory / 'failure.json').exists():
            raise
    row['synthesis_estimate'] = compiler.cell_estimate(directory / 'design.json', 'warp_top')
    (directory / 'case.json').write_text(json.dumps(row, indent=2) + '\n')
    validate(directory, name)


def snapshot():
    paths = set()
    for folder in ('arch/warp_g1', 'arch/prims', 'tools/compile', 'tools/host'):
        paths.update(p for p in (ROOT / folder).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts)
    for name in CASES:
        pins, sources, _ = specification(name)
        paths.update([pins, *sources])
    paths.update([Path(__file__), ROOT / 'test_internal/cloud_arch_comparison.py',
                  ROOT / '.github/workflows/fresh_baseline.yaml'])
    fab = ROOT / 'macro/warp_g1/fabulous'
    paths.add(fab / 'bitStreamSpec.bin')
    paths.update((fab / '.FABulous').glob('*.txt'))
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('Baseline runs on hosted runners only')
    OUT.mkdir(parents=True, exist_ok=False)
    result = dict(passed=False, cases={}, native_route_installed=False,
                  physical_acceptance=False, timing_acceptance=False)
    try:
        tiles = Path(subprocess.check_output([str(ROOT / 'scripts/fetch_tiles.sh')], text=True).strip())
        if subprocess.check_output(['git', '-C', str(tiles), 'rev-parse', 'HEAD'], text=True).strip() != '7999e5a91dab77357fe9d401b6dfb0758f438bf1':
            raise ValueError('Unpinned tile library')
        versions = compiler.tool_versions()
        if ('Yosys 0.66+179' not in versions['yosys'] or 'e74db6dea' not in versions['yosys']
                or 'nextpnr-0.11.1-34-gc4fbb55a' not in versions['nextpnr-generic']):
            raise ValueError('Unpinned compiler tools')
        before = snapshot()
        library = {str(p.relative_to(tiles)): sha(p) for p in sorted(tiles.rglob('*'))
                   if p.is_file() and '.git' not in p.parts}
        result.update(commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                      run=os.environ.get('GITHUB_RUN_ID'), attempt=os.environ.get('GITHUB_RUN_ATTEMPT'),
                      tools=versions, tools_sha256={k: sha(compiler.tool(k)) for k in ('yosys', 'nextpnr-generic')},
                      input_sha256=before, library_sha256=library,
                      scope='G1 compiler fit/model timing only; no configured or physical timing; seed1 census')
        for name in CASES:
            run_bounded([sys.executable, str(Path(__file__).resolve()), '--worker', name, str(OUT / name)],
                        OUT / (name + '.log'))
            row = validate(OUT / name, name)
            if row['tools'] != versions:
                raise ValueError('Tool identity drift')
            result['cases'][name] = row
        if snapshot() != before or library != {str(p.relative_to(tiles)): sha(p)
                for p in sorted(tiles.rglob('*')) if p.is_file() and '.git' not in p.parts}:
            raise ValueError('Inputs drifted')
        if set(result['cases']) != set(CASES):
            raise ValueError('Incomplete matrix')
        if not all(result['cases'][name]['fits'] for name in SINGLES if name != 'i2c_target'):
            raise ValueError('G1 supported baseline regressed')
        result['passed'] = True
    except Exception as exc:
        result['error'] = str(exc)
        raise
    finally:
        (OUT / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--worker':
        worker(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit('Unsupported invocation')
