import copy
from pathlib import Path
import pytest
import sram_bank_plan as planner
import sram_bank_clean_screen as runner
from test_sram_bank_plan import fixture


def inputs(tmp_path, monkeypatch):
    nl, layout, macro = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(planner, 'CLEAN_NL_SHA', planner.NL_SHA)
    monkeypatch.setattr(planner, 'CLEAN_DEF_SHA', planner.DEF_SHA)
    proposal = planner.plan(nl, layout, Path('/unused'), macro, clean_postgpl=True)
    config = dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56, SYNTH_STRATEGY='AREA 1',
        GRT_RESIZER_HOLD_SLACK_MARGIN=.10, CTS_SINK_CLUSTERING_SIZE=8,
        GRT_ALLOW_CONGESTION=True, meta={'version':1, 'flow':'Classic'},
        SIGNOFF_SDC_FILE='unchanged.sdc', MACROS={'unchanged':{'location':[12,40]}})
    return config, proposal


def test_config_changes_only_manual_placement_and_strict_congestion(tmp_path, monkeypatch):
    config, proposal = inputs(tmp_path, monkeypatch)
    original = copy.deepcopy(config)
    result = runner.configure(config, proposal)
    assert config == original
    assert result.pop('MANUAL_GLOBAL_PLACEMENTS') == planner.placement_fragment(proposal)['MANUAL_GLOBAL_PLACEMENTS']
    result.pop('GRT_ALLOW_CONGESTION'); original.pop('GRT_ALLOW_CONGESTION')
    assert result == original


@pytest.mark.parametrize('key,value', [('CLOCK_PERIOD',25),('PL_TARGET_DENSITY_PCT',60),
    ('SYNTH_STRATEGY','DELAY 1'),('GRT_RESIZER_HOLD_SLACK_MARGIN',.05),
    ('CTS_SINK_CLUSTERING_SIZE',16),('meta',{'flow':'Custom'}),
    ('MANUAL_GLOBAL_PLACEMENTS',{'other':{}})])
def test_wrong_baseline_recipe_rejected(tmp_path, monkeypatch, key, value):
    config, proposal = inputs(tmp_path, monkeypatch); config[key] = value
    with pytest.raises(ValueError): runner.configure(config, proposal)


def test_wrong_stage_and_moved_after_legalization_rejected(tmp_path, monkeypatch):
    config, proposal = inputs(tmp_path, monkeypatch)
    wrong = copy.deepcopy(proposal); wrong['source_stage'] = 'drt'
    with pytest.raises(ValueError): runner.configure(config, wrong)
    layout = '\n'.join('- '+p['instance']+' sg13cmos5l_buf_4 + PLACED ( '
                       +str(p['new_location'][0])+' '+str(p['new_location'][1])+' ) '
                       +p['new_location'][2]+' ;' for p in proposal['proposals'])
    runner.verify_stage(layout, proposal)
    with pytest.raises(ValueError): runner.verify_stage(layout.replace('buf0 ', 'other '), proposal)


def test_workflow_uses_clean_script_and_keeps_frozen_shape():
    import yaml
    root = Path(__file__).resolve().parents[2]
    workflow = yaml.safe_load((root/'.github/workflows/gds-sram-bank-clean-screen.yaml').read_text())
    job = workflow['jobs']['harden']; steps = job['steps']
    assert job['env']['CANDIDATE_SHA'] == '3393eea9a58c5cad9077cc360a8515d0e5ec8284'
    download = next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert download['with']['run-id'] == 38172640071
    assert any(s.get('run') == 'python workflow-src/scripts/ci/sram_bank_clean_screen.py' for s in steps)


def test_launch_creates_required_directory_before_cli_and_uses_clean_stock_flow(tmp_path, monkeypatch):
    flow = tmp_path/'screen/flow'
    monkeypatch.setenv('LIBRELANE_IMAGE_OVERRIDE', 'unreviewed')
    calls = []
    def run(args, check):
        assert flow.is_dir() and not list(flow.iterdir())
        assert 'LIBRELANE_IMAGE_OVERRIDE' not in runner.os.environ
        assert args[args.index('--force-run-dir')+1] == str(flow)
        assert '--with-initial-state' not in args and check is True
        calls.append(args)
    monkeypatch.setattr(runner.subprocess, 'run', run)
    runner.start_clean_flow(Path('src/config_trial.json'), flow, '/pdk')
    assert len(calls) == 1


def test_launch_refuses_reusing_existing_flow(tmp_path, monkeypatch):
    flow = tmp_path/'flow'; flow.mkdir()
    def unexpected(*args, **kwargs): raise AssertionError('Must refuse before CLI')
    monkeypatch.setattr(runner.subprocess, 'run', unexpected)
    with pytest.raises(FileExistsError): runner.start_clean_flow(Path('config.json'), flow, '/pdk')
