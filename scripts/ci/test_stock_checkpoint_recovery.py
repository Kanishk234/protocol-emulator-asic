"""Reject stale, changed or incomplete checkpoint recovery inputs."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from stock_checkpoint_recovery import validate


@pytest.fixture
def checkpoint(tmp_path):
    source = 'runs/stock-official-baseline/final/state_out.json'
    config = dict(CLOCK_PERIOD=20, PL_RESIZER_HOLD_SLACK_MARGIN=0.275,
                  GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=300, GRT_OVERFLOW_ITERS=100,
                  RUN_POST_GRT_RESIZER_TIMING=False)
    contents = {'src/config.json': json.dumps(config)}
    state = {}
    for key in ('odb', 'def', 'nl', 'pnl', 'sdc'):
        name = f'runs/stock-official-baseline/final/chip.{key}'
        contents[name] = key
        state[key] = str(tmp_path / name)
    contents[source] = json.dumps(state)
    for name, text in contents.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    run = dict(id=1, head_sha='trusted')
    artifact = dict(id=2, expired=False)
    manifest = dict(run=run, artifact=artifact, runner_root=str(tmp_path),
                    source_state=source,
                    files={n: hashlib.sha256(t.encode()).hexdigest() for n, t in contents.items()})
    return tmp_path, manifest, run, artifact


def test_complete_source(checkpoint):
    root, manifest, run, artifact = checkpoint
    assert validate(root, manifest, run, artifact, require_runner_root=True).is_file()


@pytest.mark.parametrize('target,key,value', [('run', 'head_sha', 'stale'),
                                            ('artifact', 'id', 99),
                                            ('artifact', 'expired', True)])
def test_wrong_provenance(checkpoint, target, key, value):
    root, manifest, run, artifact = checkpoint
    run, artifact = copy.deepcopy(run), copy.deepcopy(artifact)
    (run if target == 'run' else artifact)[key] = value
    with pytest.raises(ValueError, match='Wrong'):
        validate(root, manifest, run, artifact)


def test_changed_database(checkpoint):
    root, manifest, run, artifact = checkpoint
    (root / 'runs/stock-official-baseline/final/chip.odb').write_text('changed')
    with pytest.raises(ValueError, match='Missing or changed'):
        validate(root, manifest, run, artifact)


def test_unbound_physical_view(checkpoint):
    root, manifest, run, artifact = checkpoint
    del manifest['files']['runs/stock-official-baseline/final/chip.def']
    with pytest.raises(ValueError, match='Unbound physical view'):
        validate(root, manifest, run, artifact)


def test_missing_physical_key(checkpoint):
    root, manifest, run, artifact = checkpoint
    source = root / manifest['source_state']
    state = json.loads(source.read_text())
    del state['odb']
    source.write_text(json.dumps(state))
    manifest['files'][manifest['source_state']] = hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='Missing or invalid physical view'):
        validate(root, manifest, run, artifact)


def test_path_escape(checkpoint):
    root, manifest, run, artifact = checkpoint
    manifest['files']['../escape'] = 'bad'
    with pytest.raises(ValueError, match='Unsafe'):
        validate(root, manifest, run, artifact)


def test_unexpected_drt(checkpoint):
    root, manifest, run, artifact = checkpoint
    (root / 'runs/stock-official-baseline/45-openroad-detailedrouting').mkdir()
    with pytest.raises(ValueError, match='Unexpected detailed'):
        validate(root, manifest, run, artifact)


def test_wrong_runner_root(checkpoint):
    root, manifest, run, artifact = checkpoint
    manifest['runner_root'] = '/other-checkout'
    with pytest.raises(ValueError, match='Runner checkout'):
        validate(root, manifest, run, artifact, require_runner_root=True)


def test_unbound_source(checkpoint):
    root, manifest, run, artifact = checkpoint
    del manifest['files'][manifest['source_state']]
    with pytest.raises(ValueError, match='Unbound source state'):
        validate(root, manifest, run, artifact)


def test_wrong_recipe_even_with_matching_file_hash(checkpoint):
    root, manifest, run, artifact = checkpoint
    config = root / 'src/config.json'
    values = json.loads(config.read_text())
    values['CLOCK_PERIOD'] = 40
    config.write_text(json.dumps(values))
    manifest['files']['src/config.json'] = hashlib.sha256(config.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='Wrong recovered physical recipe'):
        validate(root, manifest, run, artifact)
