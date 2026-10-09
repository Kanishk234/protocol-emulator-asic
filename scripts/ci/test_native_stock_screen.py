import json
from pathlib import Path
import pytest
import native_stock_screen as runner


@pytest.mark.parametrize('strategy', ['AREA 0', 'AREA 1'])
def test_recipe_preserves_shape_and_enables_stock_repair(strategy, tmp_path):
    original = dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56, MACROS={'sram': 'frozen'},
                    meta={'version': 1, 'flow': ['Custom.Step']})
    cfg = runner.configure(original, strategy, tmp_path / 'signoff.sdc')
    assert cfg['MACROS'] == original['MACROS']
    assert original['meta']['flow'] == ['Custom.Step']
    assert cfg['meta']['flow'] == 'Classic'
    assert cfg['RUN_POST_GRT_RESIZER_TIMING'] is True
    assert cfg['RSZ_CORNERS'] == list(runner.CORNERS)
    assert cfg['PNR_SDC_FILE'] == cfg['SIGNOFF_SDC_FILE']
    assert cfg['GRT_RESIZER_HOLD_SLACK_MARGIN'] == 0.125


@pytest.mark.parametrize('strategy', [None, 'DELAY 2', ''])
def test_unknown_recipe_rejected(strategy, tmp_path):
    with pytest.raises(ValueError):
        runner.configure(dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56), strategy, tmp_path/'sdc')


def test_missing_and_detailed_route_checkpoints_rejected(tmp_path):
    with pytest.raises(ValueError): runner.checkpoint(tmp_path)
    stage = tmp_path/'45-openroad-resizertimingpostgrt'
    stage.mkdir()
    view = stage/'saved'; view.write_text('view')
    state = {k: str(view) for k in ('odb', 'def', 'nl', 'pnl', 'sdc')}
    (stage/'state_out.json').write_text(json.dumps(state))
    assert runner.checkpoint(tmp_path) == stage/'state_out.json'
    (tmp_path/'47-openroad-detailedrouting').mkdir()
    with pytest.raises(ValueError): runner.checkpoint(tmp_path)


@pytest.mark.parametrize('hold_target',[.10,.125])
def test_main_uses_stock_stop_and_never_repeats_repair(tmp_path, monkeypatch, hold_target):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('NATIVE_HOLD_TARGET',str(hold_target))
    for k, v in dict(VARIANT='bs-event-late', NATIVE_MAPPING_STRATEGY='AREA 1',
                     PDK_ROOT='/pdk', LIBRELANE_IMAGE_OVERRIDE='old:custom').items():
        monkeypatch.setenv(k, v)
    Path('src').mkdir()
    Path('src/signoff.sdc').write_text('fully timed')
    Path('src/config_merged.json').write_text(json.dumps(dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56)))
    calls = []
    def flow(args, **kwargs):
        import os
        assert 'LIBRELANE_IMAGE_OVERRIDE' not in os.environ
        assert '--with-initial-state' not in args
        assert args[args.index('--to') + 1] == 'OpenROAD.ResizerTimingPostGRT'
        assert json.loads(Path(args[-1]).read_text())['GRT_RESIZER_HOLD_SLACK_MARGIN']==hold_target
        stage = Path('runs/native-stock-screen/flow/45-openroad-resizertimingpostgrt')
        stage.mkdir()
        view = stage/'saved'; view.write_text('view')
        (stage/'state_out.json').write_text(json.dumps({k:str(view) for k in ('odb','def','nl','pnl','sdc')}))
        calls.append('flow')
    def sta(config, source, output, pdk, **kwargs):
        assert kwargs['repaired'] == source
        assert kwargs['sdc'] == Path('src/signoff.sdc')
        calls.append('sta')
    monkeypatch.setattr(runner.subprocess, 'run', flow)
    monkeypatch.setattr(runner, 'screen', sta)
    runner.main()
    assert calls == ['flow', 'sta']
    receipt = json.loads(Path('runs/native-stock-screen/recipe.json').read_text())
    assert receipt['checkpoint_ecos'] is False
    assert receipt['hold_target_ns']==hold_target
    assert receipt['official_signoff'] is False



def test_design_repair_is_explicit_and_preserves_timing_recipe(tmp_path):
    original=dict(CLOCK_PERIOD=20,PL_TARGET_DENSITY_PCT=56)
    baseline=runner.configure(original,'AREA 1',tmp_path/'sdc')
    changed=runner.configure(original,'AREA 1',tmp_path/'sdc',design_repair=True)
    assert 'RUN_POST_GRT_DESIGN_REPAIR' not in baseline
    assert changed.pop('RUN_POST_GRT_DESIGN_REPAIR') is True
    assert changed==baseline
    with pytest.raises(ValueError):runner.configure(original,'AREA 1',tmp_path/'sdc',design_repair='1')



def test_hold_target_changes_one_physical_option(tmp_path):
    original=dict(CLOCK_PERIOD=20,PL_TARGET_DENSITY_PCT=56)
    baseline=runner.configure(original,'AREA 1',tmp_path/'sdc')
    changed=runner.configure(original,'AREA 1',tmp_path/'sdc',hold_target=.10)
    assert changed.pop('GRT_RESIZER_HOLD_SLACK_MARGIN')==.10
    baseline.pop('GRT_RESIZER_HOLD_SLACK_MARGIN')
    assert changed==baseline
    for value in (.05,.15,float('nan'),True,'0.10'):
        with pytest.raises(ValueError):runner.configure(original,'AREA 1',tmp_path/'sdc',hold_target=value)



def test_hold100_workflow_is_a_single_option_comparison():
    import yaml
    wf=yaml.safe_load((Path(__file__).parents[2]/'.github/workflows/gds-native-hold100-screen.yaml').read_text())
    job=wf['jobs']['harden']
    assert job['env']['NATIVE_HOLD_TARGET']=='0.10'
    assert 'NATIVE_DESIGN_REPAIR' not in job['env']
    assert job['env']['VARIANT']=='bs-event-late'
    assert job['strategy']['matrix']['strategy']==['AREA 1']
    assert not any('docker build' in step.get('run','') for step in job['steps'])
