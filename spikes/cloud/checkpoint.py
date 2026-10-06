#!/usr/bin/env python3
"""Package preserved compact inputs, or verify/materialize them on a fresh host.

This is a checkpoint reproduction, not a clean-source fabric rebuild. Binary
inputs are release assets, not committed build output. No EDA tools run here.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[2]
NAME = 'warp_g1_prune_clock_primpruned_5x3_compact_edges'
TOKEN = '${WARP_CHECKPOINT_ROOT}'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace(value, old, new):
    if isinstance(value, dict):
        return {k: replace(v, old, new) for k, v in value.items()}
    if isinstance(value, list):
        return [replace(v, old, new) for v in value]
    if isinstance(value, str):
        return value.replace(old, new)
    return value


def paths(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from paths(v)
    elif isinstance(value, list):
        for v in value:
            yield from paths(v)
    elif isinstance(value, str) and value.startswith(str(ROOT) + '/'):
        yield Path(value)


def package(out):
    out.mkdir(exist_ok=False, parents=True)
    payload = out / 'payload'
    project = payload / 'project'
    project.mkdir(parents=True)
    work = ROOT / 'build/arch_explore/compact_edges_tighter'
    route = ROOT / 'build/route_root_audit_20261006/chip_schedule64'
    step = route / 'runs/schedule64/01-openroad-detailedrouting'
    # Only a complete iteration, with its matching native report, is portable.
    odb = step / 'drt_iter8.odb'
    drc = step / f'drt-run-0/tt_um_warp.drc-8.rpt'
    markers = drc.read_text().count('violation type:')
    if markers != 15:
        raise ValueError(f'Expected the measured 15-marker checkpoint, got {markers}')
    config = json.loads((route / 'config.json').read_text())
    state = json.loads((step / 'state_in.json').read_text())
    state['odb'] = str(odb)
    # Existing parasitics/DEF/metrics are not evidence for this rerouted snapshot.
    for key in ('def', 'sdf', 'spef'):
        state[key] = None
    state['metrics'] = {}
    native_config = json.loads((work / 'chip_shared_crc_cfgbranches/config.json').read_text())
    selected = set(paths(config)) | set(paths(state)) | set(paths(native_config))
    selected |= {ROOT / 'LICENSE', ROOT / 'docs/VERSIONS.md', drc,
                 work / f'{NAME}.csv', ROOT / 'build/arch_explore/compiled_structural/uart_words.hex',
                 work / f'macro/fabulous/{NAME}.v', work / f'macro/nl/{NAME}.nl.v',
                 work / 'chip_shared_crc_cfgbranches/tt_um_warp_candidate.v',
                 work / 'fabulous-tiles/models_pack.v'}
    tiles = set()
    in_fabric = False
    for row in csv.reader((work / f'{NAME}.csv').open()):
        if row and row[0] == 'FabricBegin':
            in_fabric = True
        elif row and row[0] == 'FabricEnd':
            break
        elif in_fabric:
            tiles.update(n for n in row if n and n != 'NULL')
    for tile in tiles:
        directory = work / 'fabulous-tiles/tiles/tiny' / tile
        selected.update(directory.glob('*.v'))
        selected.add(directory / f'macro/ihp-sg13cmos5l/nl/{tile}.nl.v')
    for primitive in ('FABULOUS_LC', 'IOBUF', 'GBUF', 'SYS_RESET'):
        selected.add(work / f'fabulous-tiles/primitives/{primitive}/fabulous/{primitive}.v')
    selected.update((ROOT / 'arch/prims').glob('*.v'))
    inventory = []
    for source in sorted(selected):
        # The project's tt/ is a symlink to pinned support tools. Preserve the
        # logical project-relative name but dereference the selected input.
        source = source.absolute()
        relative = source.relative_to(ROOT)
        if not source.is_file():
            raise FileNotFoundError(source)
        dst = project / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        before = digest(source)
        shutil.copyfile(source, dst)
        if digest(dst) != before or digest(source) != before:
            raise ValueError(f'Input changed while packaging: {source}')
        inventory.append({'path': relative.as_posix(), 'sha256': before})
    # JSON templates are materialized after the exact binary/source inventory
    # is verified. They never overwrite a tracked source file.
    for name, value in (('route_config', config), ('route_state', state), ('native_config', native_config)):
        (payload / f'{name}.json').write_text(json.dumps(replace(value, str(ROOT), TOKEN), indent=2)+'\n')
    manifest = {
        'format': 1, 'scope': 'experimental checkpoint, not a submission or clean-source rebuild',
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'source_iteration': 8, 'source_markers': markers, 'source_odb_sha256': digest(odb),
        'pdk_revision': '2bbec755dc67ca3db0261c3d6163e15735d66710',
        'openroad_revision': 'dcf36133a369abc8f3c5e5738cd4d82e4903c0e0',
        'native_work': work.relative_to(ROOT).as_posix(),
        'words': 'build/arch_explore/compiled_structural/uart_words.hex',
        'inventory': inventory,
    }
    (payload / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    (payload / 'ATTRIBUTION.md').write_text(
        'WARP experimental generated fabric/checkpoint. Project license: project/LICENSE.\n'
        'FABulous: FPGA-Research/FABulous; tile library: mole99/fabulous-tiles at7999e5a,\n'
        'with WARP changes under D-010/D-037/D-038. Original source headers retained.\n'
        'PDK/model files are fetched separately at the manifest revision.\n'
        'Tool pins and limitations: project/docs/VERSIONS.md and manifest.json.\n')
    archive = out / 'compact-checkpoint.tar.gz'
    with tarfile.open(archive, 'w:gz', compresslevel=1) as tar:
        tar.add(payload, arcname='payload')
    print(json.dumps({'archive': str(archive), 'sha256': digest(archive),
                      'bytes': archive.stat().st_size, 'files': len(inventory), 'markers': markers}))


def materialize(archive, out, expected):
    if digest(archive) != expected:
        raise ValueError('Release asset SHA256 mismatch')
    out.mkdir(exist_ok=False, parents=True)
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            p = Path(member.name)
            if p.is_absolute() or '..' in p.parts or p.parts[0] != 'payload':
                raise ValueError('Invalid archive path')
            if not (member.isfile() or member.isdir()):
                raise ValueError('Links/devices are not checkpoint inputs')
        tar.extractall(out, filter='data')
    payload = out / 'payload'
    manifest = json.loads((payload / 'manifest.json').read_text())
    project = payload / 'project'
    for item in manifest['inventory']:
        path = project / item['path']
        if not path.resolve().is_relative_to(project.resolve()) or digest(path) != item['sha256']:
            raise ValueError(f'Checkpoint inventory mismatch: {item["path"]}')
    generated = {}
    for name in ('route_config', 'route_state', 'native_config'):
        value = replace(json.loads((payload / f'{name}.json').read_text()), TOKEN, str(project.resolve()))
        generated[name] = value
    # Four standard hosted vCPUs, not a paid/larger or self-hosted runner.
    generated['route_config']['DRT_THREADS'] = 4
    for name in ('route_config', 'route_state'):
        (out / f'{name}.json').write_text(json.dumps(generated[name], indent=2)+'\n')
    native_work = project / manifest['native_work']
    (native_work / 'chip_shared_crc_cfgbranches/config.json').write_text(
        json.dumps(generated['native_config'], indent=2)+'\n')
    (out / 'materialized.json').write_text(json.dumps({
        'project': str(project.resolve()), 'native_work': str(native_work.resolve()),
        'words': str((project / manifest['words']).resolve()),
        'source_markers': manifest['source_markers'],
        'source_odb_sha256': manifest['source_odb_sha256'],
        'inventory_verified': len(manifest['inventory']),
        'flow_changes': {'DRT_THREADS': 4, 'librelane': '3.1.0.dev3'},
    }, indent=2)+'\n')
    print('Verified/materialized checkpoint:', out)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='operation', required=True)
    a = sub.add_parser('package'); a.add_argument('--out', type=Path, required=True)
    a = sub.add_parser('materialize')
    a.add_argument('--archive', type=Path, required=True)
    a.add_argument('--out', type=Path, required=True)
    a.add_argument('--sha256', required=True)
    args = p.parse_args()
    if args.operation == 'package':
        package(args.out)
    else:
        materialize(args.archive, args.out, args.sha256)
