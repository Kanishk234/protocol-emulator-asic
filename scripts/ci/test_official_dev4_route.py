import hashlib
import json
from pathlib import Path
import sys
import types

import pytest
import yaml

import official_dev4_route as route


def test_route_and_extraction_jobs_export_pdk_root():
    workflow = Path(__file__).parents[2] / '.github/workflows/gds-official-dev4-hold125-route.yaml'
    config = yaml.safe_load(workflow.read_text())
    for job in ('route', 'extraction'):
        assert config['jobs'][job]['env']['PDK_ROOT'] == '/home/runner/pdk'


def test_restore_resolved_pdk_root_uses_exact_versioned_directory(tmp_path, monkeypatch):
    versioned = tmp_path / route.PDK
    (versioned / 'ihp-sg13cmos5l').mkdir(parents=True)
    assert route.restore_resolved_pdk_root({'resolved_pdk_root': str(versioned)}) == versioned
    assert __import__('os').environ['PDK_ROOT'] == str(versioned)


def test_restore_resolved_pdk_root_rejects_cache_root(tmp_path):
    with pytest.raises(ValueError, match='exact resolved Ciel PDK root'):
        route.restore_resolved_pdk_root({'resolved_pdk_root': str(tmp_path)})


def make_source(tmp_path, monkeypatch, inventory_matches=True):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(route, 'RUNNER_ROOT', tmp_path.resolve())
    (tmp_path / 'src').mkdir()
    (tmp_path / 'macro').mkdir()
    (tmp_path / 'runs/stock-official-baseline/45-openroad-stamidpnr-3').mkdir(parents=True)
    (tmp_path / 'runs/stock-corner-audit').mkdir()
    (tmp_path / 'src/config.json').write_text('{"CLOCK_PERIOD": 20}\n')
    (tmp_path / 'src/config_merged.json').write_text('{"CLOCK_PERIOD": 20}\n')
    (tmp_path / 'src/signoff.sdc').write_text('create_clock -period 20 clk\n')
    (tmp_path / 'src/design.v').write_text('module design; endmodule\n')
    (tmp_path / 'info.yaml').write_text('project:\n  tiles: 8x4\n')
    state_path = tmp_path / 'runs/stock-official-baseline/45-openroad-stamidpnr-3/state_out.json'
    state = {}
    for key, name in (('odb', 'design.odb'), ('def', 'design.def'), ('nl', 'design.nl.v'),
                      ('pnl', 'design.pnl.v'), ('sdc', 'design.sdc')):
        path = state_path.parent / name
        path.write_text('view\n')
        state[key] = str(path)
    state_path.write_text(json.dumps(state))
    run = dict(id=route.SOURCE_RUN, head_sha=route.SOURCE_SHA, head_branch='main',
               conclusion='success', path=route.SOURCE_WORKFLOW)
    (tmp_path / 'official-dev4-source-run.json').write_text(json.dumps(run))
    from official_nov9_preflight import inventory
    inputs = inventory(tmp_path)
    if not inventory_matches:
        inputs['src/design.v'] = 'incorrect-digest'
    config_sha = hashlib.sha256((tmp_path / 'src/config.json').read_bytes()).hexdigest()
    (tmp_path / 'compatibility-input.json').write_text(json.dumps(dict(
        tiles='8x4', tools_sha=route.TOOLS, pdk_revision=route.PDK,
        inputs=inputs, project_config_sha256=config_sha)))
    (tmp_path / 'compatibility-generated.json').write_text(json.dumps(
        dict(generation_passed=True, tiles='8x4')))
    (tmp_path / 'compatibility-engine.json').write_text(json.dumps(
        dict(librelane='3.1.0.dev4', pdk_revision=route.PDK, tools_sha=route.TOOLS)))
    (tmp_path / 'runs/stock-corner-audit/screen_qualification.json').write_text(json.dumps(dict(
        qualified=True, final_global_overflow=0, minimum_fast_hold_ns=.05,
        detailed_routing_performed=False, official_gds_signoff=False,
        source_state=str(state_path))))
    monkeypatch.setitem(sys.modules, 'stock_screen_gate', types.SimpleNamespace(
        qualify=lambda physical, audit: dict(qualified=True, failures=[])))
    return state_path


def test_verify_source_accepts_exact_screen_inventory(tmp_path, monkeypatch):
    source_path = make_source(tmp_path, monkeypatch)
    source, config = route.verify_source()
    assert source.resolve() == source_path.resolve()
    assert config == {'CLOCK_PERIOD': 20}


def test_verify_source_rejects_changed_screen_inventory(tmp_path, monkeypatch):
    make_source(tmp_path, monkeypatch, inventory_matches=False)
    with pytest.raises(ValueError, match='Source or macro inventory'):
        route.verify_source()
