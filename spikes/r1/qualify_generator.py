"""Regenerate a clean G1 software control before R1 model exploration.

No hardened views or production inputs are changed. PIP delays are excluded
from graph identity and explicitly remain unqualified timing metadata.
"""
import argparse
from collections import Counter
import hashlib
import io
import json
import os
from pathlib import Path
import pickle
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[2]
TILES_REV = '7999e5a91dab77357fe9d401b6dfb0758f438bf1'
EXTRA_ARCH = dict(FrameSelectWidth=5, DesyncBit=20,
                  SyncHeaderHex='00AAFF01000000010000000000000000FAB0FAB1',
                  IncludeBorderRows=True, MultiClkDomains=False, FABulousVersion='2.2.0')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def graph_rows(text, *, pips=False):
    rows = []
    for line in text.splitlines():
        if not line or line.startswith('#'):
            continue
        if pips:
            parts = line.split(',')
            if len(parts) != 6:
                raise ValueError('Unsupported PIP record')
            rows.append(tuple(parts[:4] + parts[5:]))
        else:
            rows.append(line)
    return Counter(rows)


def compare_control(generated, reference):
    result = {}
    for name in ('pips.txt', 'bel.txt', 'bel.v2.txt'):
        a = graph_rows((generated/name).read_text(), pips=name == 'pips.txt')
        b = graph_rows((reference/'.FABulous'/name).read_text(), pips=name == 'pips.txt')
        if a != b:
            raise ValueError(f'{name} differs: new {sum((a-b).values())}, missing {sum((b-a).values())}')
        result[name] = sum(a.values())
    a = pickle.loads((generated/'bitStreamSpec.bin').read_bytes())
    b = pickle.loads((reference/'bitStreamSpec.bin').read_bytes())
    if set(a) != set(b):
        raise ValueError('Bitstream specification sections differ')
    for key in a:
        if key == 'ArchSpecs':
            if a[key] != dict(b[key], **EXTRA_ARCH):
                raise ValueError('Unexpected architecture metadata change')
        elif a[key] != b[key]:
            raise ValueError('Configuration mapping differs: ' + key)
    return dict(graph_records=result, configuration_maps_equal=True,
                added_arch_metadata=EXTRA_ARCH, pip_delays_qualified=False,
                physical_acceptance=False, timing_acceptance=False)


def run(source, out):
    import importlib.metadata
    from fabulous.fabulous_api import FABulous_API
    from fabulous.fabric_generator.code_generator.code_generator_Verilog import VerilogCodeGenerator
    from fabulous.fabric_generator.gen_fabric.gen_configmem import generateConfigMemInit
    if importlib.metadata.version('FABulous-FPGA') != '2.2.0':
        raise ValueError('Require pinned FABulous2.2.0')
    source, out = Path(source).resolve(), Path(out).resolve()
    if source == out or source in out.parents or out in source.parents:
        raise ValueError('Source and output must be disjoint')
    if subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() != TILES_REV:
        raise ValueError('Unpinned tile source')
    out.mkdir(parents=True, exist_ok=False)
    record = dict(passed=False, tiles_revision=TILES_REV, native_route_installed=False,
                  physical_acceptance=False, timing_acceptance=False)
    try:
        inputs = [ROOT/'arch/warp_g1/fabric.csv', Path(__file__).resolve(),
                  *sorted((ROOT/'arch/tiles/PRIM2T2S').glob('*')),
                  *sorted((ROOT/'arch/prims').glob('*.v')),
                  ROOT/'macro/warp_g1/fabulous/bitStreamSpec.bin',
                  *[ROOT/'macro/warp_g1/fabulous/.FABulous'/name for name in ('pips.txt','bel.txt','bel.v2.txt')]]
        before = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in inputs if p.is_file()}
        library = out/'library'
        library.mkdir()
        # Git archive excludes every ignored/untracked cached experiment.
        archive = subprocess.check_output(['git', '-C', str(source), 'archive', TILES_REV])
        record['source_archive_sha256'] = digest(archive)
        with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
            stream.extractall(library, filter='data')
        shutil.copytree(ROOT/'arch/tiles/PRIM2T2S', library/'tiles/tiny/PRIM2T2S')
        shutil.copytree(ROOT/'arch/prims', library/'primitives/WARP/fabulous',
                        ignore=shutil.ignore_patterns('__pycache__'))
        fabric = out/'r1_g1_control.csv'
        source_csv = (ROOT/'arch/warp_g1/fabric.csv').read_bytes()
        fabric.write_text(source_csv.decode().replace('TILES/', str(library/'tiles/tiny')+'/'))
        api = FABulous_API(VerilogCodeGenerator())
        api.loadFabric(fabric)
        for tile in api.getTiles():
            if tile.globalConfigBits:
                generateConfigMemInit(library/'tiles/tiny'/tile.name/(tile.name+'_ConfigMem.csv'),
                                      tile.globalConfigBits, api.fabric.frameBitsPerRow, api.fabric.maxFramesPerCol)
        model = api.gen_routing_model()
        for name, text in zip(('pips.txt', 'bel.txt', 'bel.v2.txt', 'bel.v3.txt', 'template.pcf'), model):
            (out/name).write_text(text)
        (out/'bitStreamSpec.bin').write_bytes(pickle.dumps(api.genBitStreamSpec()))
        check = compare_control(out, ROOT/'macro/warp_g1/fabulous')
        after = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in inputs if p.is_file()}
        if before != after:
            raise ValueError('Control sources changed during generation')
        record.update(check=check, input_sha256=before,
                      workflow_run=os.environ.get('GITHUB_RUN_ID'),
                      workflow_attempt=os.environ.get('GITHUB_RUN_ATTEMPT'),
                      source_revision=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
                      yosys_version=subprocess.check_output(['yosys','-V'], text=True).strip(),
                      library_sha256={str(p.relative_to(library)): digest(p.read_bytes())
                          for p in sorted(library.rglob('*')) if p.is_file()},
                      generated_sha256={name: digest((out/name).read_bytes()) for name in (
                          'pips.txt','bel.txt','bel.v2.txt','bel.v3.txt','template.pcf','bitStreamSpec.bin')},
                      fabulous_python_sha256={str(f): digest(importlib.metadata.distribution('FABulous-FPGA').locate_file(f).read_bytes())
                          for f in importlib.metadata.files('FABulous-FPGA') if str(f).endswith('.py')},
                      source_fabric_sha256=digest(source_csv), passed=True)
    except Exception as exc:
        record['error'] = str(exc)
        raise
    finally:
        (out/'qualification.json').write_text(json.dumps(record, indent=2, sort_keys=True)+'\n')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tiles', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.tiles, args.out)
    print(json.dumps(result['check'], sort_keys=True))


if __name__ == '__main__':
    main()
