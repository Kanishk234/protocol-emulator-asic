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


@pytest.mark.parametrize('fault', [None, 'congestion', 'command', 'rewire', 'missing', 'remaining'])
def test_post_timing_antenna_repair_preserves_logic_and_checks_policy(tmp_path, monkeypatch, fault):
    import json
    def write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(data)
    nl = 'sg13cmos5l_buf_1 original (.A(a), .X(x));'
    original = tmp_path/'original.v'; original.write_text(nl)
    source = tmp_path/'source.json'; source.write_text(json.dumps({'nl':str(original)}))
    calls = []
    def step(config, initial, cleanup, steps):
        assert config['GRT_ALLOW_CONGESTION'] is False and initial == source
        calls.append(steps)
        write(cleanup/'resolved.json', json.dumps({'GRT_ALLOW_CONGESTION':fault == 'congestion'}))
        write(cleanup/'1-openroad-repairantennas/1-openroad-diodeinsertion/openroad-diodeinsertion.log',
              'repair_antennas'+(' -allow_congestion' if fault == 'command' else ''))
        checked = cleanup/'2-openroad-checkantennas'
        views = {}
        for key in ('odb','def','nl','pnl','sdc'):
            path = checked/('chip.'+key)
            data = nl.replace('.A(a)', '.A(other)') if fault == 'rewire' else nl
            write(path, data+'\nsg13cmos5l_antennanp newdiode (.A(x));')
            views[key] = str(path)
        if fault == 'missing': Path(views['odb']).unlink()
        write(checked/'state_out.json', json.dumps(views))
        write(checked/'or_metrics_out.json', json.dumps({'antenna__violating__nets':1 if fault == 'remaining' else 0,
                                                       'antenna__violating__pins':0}))
    monkeypatch.setattr(runner, 'run_step', step)
    args = ({'GRT_ALLOW_CONGESTION':False}, source, tmp_path/'output', {'antenna__violating__nets':15,'antenna__violating__pins':17})
    if fault in ('congestion','command','rewire','missing'):
        with pytest.raises(ValueError): runner.repair_remaining_antennas(*args)
    else:
        checked, metrics = runner.repair_remaining_antennas(*args)
        assert checked != source
        from postgrt_timing import CORNERS
        timing = {'corners':{c:{'after':{f'timing__setup__ws__corner:{c}':0,
                                      f'timing__hold__ws__corner:{c}':.08}} for c in CORNERS}}
        assert runner.qualified(timing, metrics) == (fault != 'remaining')
    assert calls == [['OpenROAD.RepairAntennas', 'OpenROAD.CheckAntennas']]


def test_clean_antennas_skip_repair_and_no_congestion_waiver(tmp_path, monkeypatch):
    def unexpected(*args): raise AssertionError('No repair needed')
    monkeypatch.setattr(runner, 'run_step', unexpected)
    source = tmp_path/'source.json'; metrics = {'antenna__violating__nets':0,'antenna__violating__pins':0}
    assert runner.repair_remaining_antennas({'GRT_ALLOW_CONGESTION':False},source,tmp_path,metrics) == (source,metrics)
    with pytest.raises(ValueError): runner.repair_remaining_antennas({'GRT_ALLOW_CONGESTION':True},source,tmp_path,metrics)
