import hashlib
import json
from pathlib import Path
import pytest
import native_clock8_screen as screen


def inputs(tmp_path, monkeypatch):
    src = tmp_path / 'src'
    src.mkdir()
    cfg = {'CLOCK_PERIOD': 20, 'CTS_SINK_CLUSTERING_SIZE': 8}
    (src / 'config_native_stock.json').write_text(json.dumps(cfg))
    recipe = tmp_path / 'runs/native-stock-screen'
    recipe.mkdir(parents=True)
    (recipe / 'recipe.json').write_text('{}')
    nl = tmp_path / 'runs/extracted-timing/final/nl/tt_um_tripwire.nl.v'
    nl.parent.mkdir(parents=True)
    nl.write_text('reviewed netlist')
    monkeypatch.setattr(screen, 'SOURCE_SHA256', hashlib.sha256(nl.read_bytes()).hexdigest())
    monkeypatch.setattr(screen, 'fingerprints', lambda root: {'trusted': 'hardware'})
    calls = []
    monkeypatch.setattr(screen, 'validate_source', lambda *args, **kwargs: calls.append((args, kwargs)))
    run = dict(id=screen.SOURCE_RUN, head_sha=screen.SOURCE_SHA, head_branch='main',
               conclusion='success', path='.github/workflows/gds-native-clock8-route.yaml')
    return run, cfg, nl, calls


def test_source_receipt_and_clean_recipe_validation(tmp_path, monkeypatch):
    run, cfg, nl, calls = inputs(tmp_path, monkeypatch)
    screen.validate_inputs(tmp_path, run, {'trusted': 'hardware'}, cfg)
    assert len(calls) == 1
    assert calls[0][1] == {'profile': 'clock8'}
    assert calls[0][0][0]['id'] == 37990280838


@pytest.mark.parametrize('key,value', [('id', 1), ('head_sha', 'wrong'),
    ('head_branch', 'other'), ('conclusion', 'failure'), ('path', 'other')])
def test_wrong_route_provenance_rejected(tmp_path, monkeypatch, key, value):
    run, cfg, nl, calls = inputs(tmp_path, monkeypatch)
    run[key] = value
    with pytest.raises(ValueError, match='provenance'):
        screen.validate_inputs(tmp_path, run, {}, cfg)
    assert not calls


def test_changed_recipe_rejected(tmp_path, monkeypatch):
    run, cfg, nl, calls = inputs(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='recipe'):
        screen.validate_inputs(tmp_path, run, {}, dict(cfg, CLOCK_PERIOD=25))


def test_changed_extracted_netlist_rejected(tmp_path, monkeypatch):
    run, cfg, nl, calls = inputs(tmp_path, monkeypatch)
    nl.write_text('different netlist')
    with pytest.raises(ValueError, match='netlist'):
        screen.validate_inputs(tmp_path, run, {}, cfg)
