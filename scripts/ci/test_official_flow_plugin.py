"""Run explicitly with the pinned LibreLane Python package available."""
import json
from pathlib import Path

import pytest

import librelane.plugins
from librelane.flows import Flow
from librelane.state import State
import librelane_plugin_tripwire as plugin


def instance(root, monkeypatch):
    monkeypatch.chdir(root)
    monkeypatch.setattr(plugin, 'native', lambda: True)
    monkeypatch.setattr(plugin, 'validate_source', lambda root: {})
    (root/'runs/wokwi').mkdir(parents=True)
    (root/'src').mkdir()
    context = root/'runs/context.json'
    context.write_text(json.dumps(dict(id=123, head_sha='head', head_branch='main',
        path=plugin.OFFICIAL_WORKFLOW, status='in_progress', conclusion=None)))
    (root/'src/config_merged.json').write_text('{"original": true}\n')
    (root/'src/user_config.json').write_text('{}\n')
    obj = object.__new__(plugin.TripwireReproduced)
    obj.run_dir = str(root/'runs/wokwi')
    obj.config = {'TRIPWIRE_RUN_CONTEXT': str(context)}
    return obj


def test_real_cli_plugin_discovery_and_config_api():
    assert Flow.factory.get('TripwireReproduced') is plugin.TripwireReproduced
    obj = object.__new__(plugin.TripwireReproduced)
    variables = obj.get_all_config_variables()
    assert len([v for v in variables if v.name == 'TRIPWIRE_RUN_CONTEXT']) == 1


def test_failed_child_flow_restores_input_and_exposes_failure_reports(tmp_path, monkeypatch):
    obj = instance(tmp_path, monkeypatch)
    def fail(**kwargs):
        assert kwargs['workflow'] == plugin.OFFICIAL_WORKFLOW
        raise ValueError('physical gate failure')
    monkeypatch.setattr(plugin, 'reproduce', fail)
    with pytest.raises(ValueError, match='physical gate failure'):
        obj.run(State())
    assert (tmp_path/'src/config_merged.json').read_text() == '{"original": true}\n'
    assert not (tmp_path/'workflow-src').is_symlink()
    assert (tmp_path/'runs/wokwi/tripwire-extracted-timing').is_symlink()
    assert not (tmp_path/'runs/wokwi/final').exists()


def test_real_state_snapshot_and_tt_stage_contract(tmp_path, monkeypatch):
    obj = instance(tmp_path, monkeypatch)
    def reproduce(**kwargs):
        root = tmp_path
        stages = ['runs/native-stock-screen/flow/01-verilator-lint',
            'runs/native-stock-screen/flow/06-yosys-synthesis',
            'runs/native-stock-screen/flow/28-openroad-globalplacement',
            'runs/extracted-timing/11-openroad-stapostpnr',
            'runs/wire600-integrated-proof/export/6-checker-lvs']
        for name in stages:
            (root/name).mkdir(parents=True)
        views = {}
        for name, suffix in [('gds', 'gds'), ('lef', 'lef'), ('nl', 'nl.v'), ('pnl', 'pnl.v')]:
            path = root/'runs/wire600-integrated-proof/export'/('tt_um_tripwire.'+suffix)
            path.write_text(name+' fixture')
            views[name] = str(path)
        views['metrics'] = {'design__lvs_error__count': 0}
        (root/stages[-1]/'state_out.json').write_text(json.dumps(views))
        (root/'runs/wire600-integrated-proof/gates.json').write_text('{"official_signoff": false}\n')
        (root/'src/config_electrical_incremental_route.json').write_text('{"CLOCK_PERIOD":20}\n')
        (root/'runs/tripwire-image.json').write_text('{"image":"fixture"}\n')
    monkeypatch.setattr(plugin, 'reproduce', reproduce)
    final, steps = obj.run(State())
    assert steps == []
    out = tmp_path/'runs/wokwi/final'
    assert (out/'gds/tt_um_tripwire.gds').read_text() == 'gds fixture'
    assert (out/'lef/tt_um_tripwire.lef').is_file()
    assert (out/'nl/tt_um_tripwire.nl.v').is_file()
    assert (out/'pnl/tt_um_tripwire.pnl.v').is_file()
    assert (out/'metrics.csv').is_file()
    assert len(list((tmp_path/'runs/wokwi').glob('*-yosys-synthesis'))) == 1
    assert len(list((tmp_path/'runs/wokwi').glob('*-openroad-stapostpnr'))) == 1
    assert not (tmp_path/'workflow-src').is_symlink()


def test_initial_checkpoint_and_partial_run_refused(tmp_path, monkeypatch):
    obj = instance(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='initial physical'):
        obj.run(State(metrics={'old': 1}))
    with pytest.raises(ValueError, match='complete build'):
        obj.run(State(), to='OpenROAD.DetailedRouting')
