"""Bind a route checkpoint to exact frozen or explicitly patched source files."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from timing_trial import CANDIDATE, apply_trial

SOURCES = {
    'placement': ('gds-placement-multicorner-screen', 'gds-placement-multicorner-timing-placement'),
    'lane': ('gds-lane-slew-screen', 'gds-lane-slew-lane'),
    'sram': ('gds-sram-slew-screen', 'gds-sram-slew-sram'),
    'cts': ('gds-cts-cluster-screen', 'gds-cts-cluster-cts-cluster8'),
    'bs-resync': ('gds-drop-counter-screen', 'gds-drop-counter-bs-resync'),
}
REQUIRED = {'src/trw_pin_bs.v', 'src/trw_chan_port.v', 'src/trw_defs.vh',
            'src/config.json', 'src/signoff.sdc', 'info.yaml'}


def validate_run(run, variant, run_id):
    if variant not in SOURCES:
        raise ValueError('Unknown route source variant')
    workflow, _ = SOURCES[variant]
    if (run['id'] != int(run_id) or run['conclusion'] != 'success'
            or run['head_branch'] != 'main'
            or run['path'] != f'.github/workflows/{workflow}.yaml'):
        raise ValueError('Wrong source run provenance')
    if variant == 'placement' and not run['head_sha'].startswith('f4bc126'):
        raise ValueError('Wrong original placement revision')


def validate_identity(identity, root, variant=None):
    if (identity['candidate'] != CANDIDATE or identity['variant'] not in SOURCES
            or (variant is not None and identity['variant'] != variant)
            or type(identity['source_run_id']) is not int or identity['source_run_id'] <= 0):
        raise ValueError('Wrong source identity')
    files = identity['files']
    if not REQUIRED.issubset(files):
        raise ValueError('Incomplete source identity')
    root = root.resolve()
    for name, digest in files.items():
        path = Path(name)
        if (path.is_absolute() or '..' in path.parts
                or not (name == 'info.yaml' or name.startswith(('src/', 'macro/')))
                or not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest)):
            raise ValueError('Invalid source fingerprint')
        actual = root / path
        if root not in actual.resolve().parents or not actual.is_file():
            raise ValueError(f'Missing or escaped source: {name}')
        if hashlib.sha256(actual.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Source mismatch: {name}')
    return identity


def prepare(variant, run_id, helpers):
    if variant not in SOURCES:
        raise ValueError('Unknown route source variant')
    # This runs before the artifact download: expected hashes come from trusted
    # checkout + named patch, never from the artifact's own assertions.
    apply_trial('bs-resync' if variant == 'bs-resync' else 'timing-placement', helpers)
    names = subprocess.check_output(
        ['git', 'ls-files', '-z', '--', 'src', 'info.yaml', 'macro']).decode().split('\0')
    identity = {'candidate': CANDIDATE, 'variant': variant, 'source_run_id': int(run_id),
                'files': {name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
                          for name in names if name}}
    return validate_identity(identity, Path.cwd(), variant)


def validate_saved(root):
    path = root / 'runs/placement-route/source_identity.json'
    if path.exists():
        return validate_identity(json.loads(path.read_text()), root)
    # Older unchanged-RTL route artifacts predate this metadata. Their existing
    # workflow provenance, checkpoint, timing and netlist guards still apply.
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'validate'])
    parser.add_argument('--variant', required=True, choices=SOURCES)
    parser.add_argument('--run-id', required=True, type=int)
    parser.add_argument('--identity', type=Path, required=True)
    parser.add_argument('--helpers', type=Path, default=Path('workflow-src'))
    parser.add_argument('--run-json', type=Path)
    args = parser.parse_args()
    if args.mode == 'prepare':
        args.identity.write_text(json.dumps(prepare(args.variant, args.run_id, args.helpers), indent=2) + '\n')
    else:
        if args.run_json is None:
            parser.error('--run-json is required for validation')
        validate_run(json.loads(args.run_json.read_text()), args.variant, args.run_id)
        identity = validate_identity(json.loads(args.identity.read_text()), Path.cwd(), args.variant)
        if identity['source_run_id'] != args.run_id:
            raise ValueError('Wrong fingerprint run ID')
        print(f"Validated {args.variant} from main run {args.run_id}; {len(identity['files'])} source fingerprints")
