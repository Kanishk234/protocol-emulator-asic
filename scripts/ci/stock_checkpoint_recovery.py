"""Validate a frozen stock checkpoint for read-only audit recovery.

This validates artifact files without rewriting any saved state or constraints.
It never runs a physical repair or qualifies the design for routing.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath


def validate(root, manifest, run, artifact, *, require_runner_root=False):
    root = Path(root).resolve()
    for key, expected in manifest['run'].items():
        if run.get(key) != expected:
            raise ValueError(f'Wrong source run field: {key}')
    for key, expected in manifest['artifact'].items():
        if artifact.get(key) != expected:
            raise ValueError(f'Wrong artifact field: {key}')
    runner = PurePosixPath(manifest['runner_root'])
    if require_runner_root and str(root) != str(runner):
        raise ValueError('Runner checkout path differs from frozen checkpoint')
    if list((root / 'runs/stock-official-baseline').glob('*-openroad-detailedrouting')):
        raise ValueError('Unexpected detailed-routing checkpoint')

    def local(name):
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Unsafe artifact-relative path')
        result = root / str(path)
        if not result.resolve().is_relative_to(root):
            raise ValueError('Artifact path escapes checkpoint root')
        return result

    files = manifest['files']
    source = local(manifest['source_state'])
    if manifest['source_state'] not in files:
        raise ValueError('Unbound source state')
    for name, digest in files.items():
        path = local(name)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Missing or changed frozen file: {name}')
    state = json.loads(source.read_text())
    for key in ('odb', 'def', 'nl', 'pnl', 'sdc'):
        try:
            name = str(PurePosixPath(state[key]).relative_to(runner))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f'Missing or invalid physical view: {key}') from exc
        if name not in files or not local(name).is_file():
            raise ValueError(f'Unbound physical view: {key}')
    config = json.loads(local('src/config.json').read_text())
    recipes = {
        'recovered_hold275': dict(CLOCK_PERIOD=20, PL_RESIZER_HOLD_SLACK_MARGIN=0.275,
                                 GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=300,
                                 GRT_OVERFLOW_ITERS=100, RUN_POST_GRT_RESIZER_TIMING=False),
        'shared_cluster100': dict(CLOCK_PERIOD=20, PL_RESIZER_HOLD_SLACK_MARGIN=0.175,
                                 GRT_RESIZER_HOLD_SLACK_MARGIN=0.175,
                                 GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=200,
                                 GRT_OVERFLOW_ITERS=100, RUN_POST_GRT_RESIZER_TIMING=True,
                                 CTS_SINK_CLUSTERING_MAX_DIAMETER=100,
                                 GRT_ANTENNA_REPAIR_DIODE_ONLY=True),
    }
    recipe = manifest.get('recipe', 'recovered_hold275')
    if recipe not in recipes:
        raise ValueError('Unknown recovered physical recipe')
    expected = recipes[recipe]
    if (any((config.get(key) is not value) if isinstance(value, bool)
            else (type(config.get(key)) not in (int, float) or config[key] != value)
            for key, value in expected.items())
            or 'PNR_SDC_FILE' in config or 'SIGNOFF_SDC_FILE' in config):
        raise ValueError('Wrong recovered physical recipe')
    return source
