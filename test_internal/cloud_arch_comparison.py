"""Hosted current G0/G1 design-set compile evidence; no physical acceptance."""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from compile import compile as compiler
from compile.bitfile import BitFile

DESIGNS = ('uart', 'spi_ctrl', 'i2c_ctrl', 'i2c_target')
ARCHES = {'warp_g0': 0, 'warp_g1': 1}
OUT = ROOT/'build/arch_comparison'


def require_nonfit_fatals(diagnosis):
    """Require reviewed native placement fatals, never demand alone.

    Broaden this grammar only after inspecting an actual retained native log.
    Any additional unknown/setup/routing fatal rejects the case.
    """
    fatals = diagnosis['fatal_messages']
    known = r'^\s*(?:ERROR|FATAL):\s*(?:Unable to place cell\b[^\n]*|no BELs remaining\b[^\n]*)$'
    if not fatals or any(not re.fullmatch(known, line) for line in fatals):
        raise ValueError('Nonfit includes unknown/setup fatal, regardless of capacity')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parameters(design, arch):
    if design not in DESIGNS or arch not in ARCHES:
        raise ValueError('Unapproved design/architecture')
    params = dict(yaml.safe_load((ROOT/'protocols'/design/'pins.yaml').read_text())['params'])
    if 'PRIMS' not in params:
        raise ValueError('Missing explicit primitive selection')
    return dict(params, PRIMS=ARCHES[arch])


def validate_case(directory, design, arch):
    directory = Path(directory)
    row = json.loads((directory/'case.json').read_text())
    expected = parameters(design, arch)
    if row['params'] != expected or row['design'] != design or row['arch'] != arch:
        raise ValueError('Actual case identity/parameters differ')
    if row['timing_corner'] != compiler.SLOW_CORNER or row['seed'] != 1:
        raise ValueError('Timing model/seed differs')
    top = yaml.safe_load((ROOT/'protocols'/design/'pins.yaml').read_text())['top']
    if compiler.chparam(expected, top) not in (directory/'synth.ys').read_text().splitlines():
        raise ValueError('Actual synthesis parameters differ')
    estimate = compiler.cell_estimate(directory/'design.json', 'warp_top')
    if row['synthesis_estimate'] != estimate:
        raise ValueError('Synthesis estimate differs from retained native netlist')
    if row['fits']:
        report = json.loads((directory/'report.json').read_text())
        if (report['params'] != expected or report['arch'] != arch or report['design'] != top
                or report['timing_corner'] != compiler.SLOW_CORNER):
            raise ValueError('Native report identity differs')
        if report['tools'] != row['tools'] or report['build_options']['seed'] != 1:
            raise ValueError('Native report tool/seed identity differs')
        for item in report['provenance']['inputs']:
            if sha(item['path']) != item['sha256']:
                raise ValueError('Retained compile input fingerprint differs')
        util, fmax = compiler.parse_pnr_log(directory/'pnr.log')
        if not util or report['utilisation'] != util or report['fmax_mhz'] != fmax:
            raise ValueError('Native placed usage/timing report differs')
        if any(v['used'] > v['available'] for v in util.values()):
            raise ValueError('Successful placement exceeds resource capacity')
        image = directory/(report['design']+'.wbit')
        bitfile = BitFile.load(image)
        arch_meta, _ = compiler.load_arch(ROOT/'arch'/arch)
        if (bitfile.arch_version != int(arch_meta['arch_version']) or
                sha(image) != report['provenance']['bitfile_sha256'] or
                len(bitfile.words) != report['words'] or
                f'0x{bitfile.arch_version:04X}' != report['arch_version'] or
                f'0x{bitfile.crc:08X}' != report['crc32']):
            raise ValueError('Actual emitted image differs from native report')
        row.update(placed_utilisation=util, compiler_fmax_mhz=fmax, image_sha256=sha(image))
    else:
        failure = json.loads((directory/'failure.json').read_text())
        native = (directory/'pnr_stdout.log').read_text()
        util, _ = compiler.parse_pnr_log(directory/'pnr_stdout.log')
        diagnosis = compiler.diagnose_pnr_failure(native, util)
        if (failure['stage'] != 'place_route' or failure['arch'] != arch or
                failure['seed'] != 1 or failure['diagnosis'] != diagnosis or
                diagnosis['category'] not in ('resource_capacity', 'placement') or
                not diagnosis['fatal_messages']):
            raise ValueError('Nonfit lacks actual native capacity/placement rejection')
        if failure['tools'] != row['tools']:
            raise ValueError('Rejected native tool identity differs')
        require_nonfit_fatals(diagnosis)
        if list(directory.glob('*.wbit')) or (directory/'report.json').exists():
            raise ValueError('Rejected design retains successful artifacts')
        row.update(failure_category=diagnosis['category'], fatal_messages=diagnosis['fatal_messages'],
                   synthesis_capacity_estimate=estimate, placed_utilisation=None)
    row['artifact_sha256'] = {str(p.relative_to(directory)): sha(p)
                              for p in sorted(directory.rglob('*')) if p.is_file()}
    return row


def worker(design, arch, directory):
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('Compile workers run on hosted runners only')
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    params = parameters(design, arch)
    sources = sorted((ROOT/'protocols'/design).glob('*.v'))
    row = dict(design=design, arch=arch, params=params, seed=1, tools=compiler.tool_versions(),
               timing_corner=compiler.SLOW_CORNER, fits=False)
    try:
        compiler.compile_design(sources, ROOT/'protocols'/design/'pins.yaml',
                                ROOT/'arch'/arch, directory, seed=1, set_params=params)
        row['fits'] = True
    except compiler.CompileError:
        # Only a retained native PNR diagnostic may qualify as expected nonfit.
        if not (directory/'failure.json').is_file():
            raise
    row['synthesis_estimate'] = compiler.cell_estimate(directory/'design.json', 'warp_top')
    (directory/'case.json').write_text(json.dumps(row, indent=2)+'\n')
    validate_case(directory, design, arch)


def run_bounded(command, log):
    with Path(log).open('w') as stream:
        child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                 start_new_session=True)
        try:
            code = child.wait(timeout=600)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
            raise
        if code:
            raise RuntimeError(f'Compile evidence worker failed ({code}); inspect {log}')


def snapshot(tiles):
    names = subprocess.check_output(['git', 'ls-files', '--', 'arch/warp_g0', 'arch/warp_g1',
        'arch/prims', 'macro/warp_g0', 'macro/warp_g1', 'tools/compile', 'tools/host',
        'scripts/fetch_tiles.sh', 'scripts/fetch_nextpnr.sh', 'requirements-dev.txt'], cwd=ROOT,
        text=True).splitlines()
    paths = [ROOT/name for name in names]
    for design in DESIGNS:
        paths.extend((ROOT/'protocols'/design).glob('*.v'))
        paths.append(ROOT/'protocols'/design/'pins.yaml')
    paths.extend([Path(__file__), ROOT/'.github/workflows/arch_comparison_evidence.yaml'])
    paths.extend(p for p in Path(tiles).rglob('*') if p.is_file() and '.git' not in p.parts)
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths))}


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('Compile measurement runs on hosted runners only')
    OUT.mkdir(parents=True, exist_ok=False)
    result = dict(passed=False, physical_acceptance=False, timing_acceptance=False, cases={})
    try:
        tiles = Path(subprocess.check_output([str(ROOT/'scripts/fetch_tiles.sh')], text=True).strip())
        revision = subprocess.check_output(['git', '-C', str(tiles), 'rev-parse', 'HEAD'], text=True).strip()
        if revision != '7999e5a91dab77357fe9d401b6dfb0758f438bf1':
            raise ValueError('Unexpected tile library revision')
        versions = compiler.tool_versions()
        if ('Yosys 0.66+179' not in versions['yosys'] or 'e74db6dea' not in versions['yosys'] or
                'nextpnr-0.11.1-34-gc4fbb55a' not in versions['nextpnr-generic']):
            raise ValueError('Unpinned synthesis/place-route tools')
        before = snapshot(tiles)
        result.update(commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            workflow_run=os.environ.get('GITHUB_RUN_ID'), workflow_attempt=os.environ.get('GITHUB_RUN_ATTEMPT'),
            python_version=sys.version, tiles_revision=revision, input_sha256=before, tools=versions,
            tool_sha256={name: sha(compiler.tool(name)) for name in ('yosys', 'nextpnr-generic')},
            assessment_clock_mhz=50, timing_corner=compiler.SLOW_CORNER,
            scope='Current compiler results; synthesis estimates are not placed LCs; model Fmax is not physical timing; no equal-total-area proof')
        for arch in ARCHES:
            for design in DESIGNS:
                name = arch+'__'+design
                command = [sys.executable, str(Path(__file__).resolve()), '--worker', design, arch, str(OUT/name)]
                run_bounded(command, OUT/(name+'.log'))
                result['cases'][name] = validate_case(OUT/name, design, arch)
                if result['cases'][name]['tools'] != versions:
                    raise ValueError('Worker tool identities changed')
        if snapshot(tiles) != before:
            raise ValueError('Inputs changed during paired measurement')
        if len(result['cases']) != 8:
            raise ValueError('Incomplete paired compile matrix')
        result.update(passed=True, inputs_unchanged=True)
    except Exception as exc:
        result['error'] = str(exc)
        raise
    finally:
        (OUT/'result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == '--worker':
        worker(*sys.argv[2:])
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit('Unsupported invocation')
