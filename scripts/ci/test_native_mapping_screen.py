import json
import os
from pathlib import Path

import pytest
import yaml

import rtl_grt_screen as runner


@pytest.mark.parametrize('variant,selected,valid', [
    ('bs-event-late',None,True), ('bs-event-late','AREA 0',True),
    ('bs-event-late','AREA 1',True), ('bs-event-late','DELAY 2',False),
    ('baseline','AREA 1',False), ('bs-event-late','',False)])
def test_only_reviewed_source_strategy_pairs(variant,selected,valid):
    if valid: assert runner.native_mapping_strategy(variant,selected)==selected
    else:
        with pytest.raises(ValueError): runner.native_mapping_strategy(variant,selected)


@pytest.mark.parametrize('strategy',['AREA 0','AREA 1'])
def test_native_screen_has_no_custom_image_and_keeps_full_contract(tmp_path,monkeypatch,strategy):
    monkeypatch.chdir(tmp_path)
    for k,v in dict(VARIANT='bs-event-late',NATIVE_MAPPING_STRATEGY=strategy,
                    ALL_CORNER_REPAIR='1',PDK_ROOT='/pdk',LIBRELANE_IMAGE_OVERRIDE='old:custom').items():
        monkeypatch.setenv(k,v)
    Path('src').mkdir()
    Path('src/signoff.sdc').write_text('fully timed')
    original=dict(CLOCK_PERIOD=20,PL_TARGET_DENSITY_PCT=56,MACROS={'sram':'frozen'},
                  PL_RESIZER_HOLD_SLACK_MARGIN=0.1,GRT_RESIZER_HOLD_SLACK_MARGIN=0.05)
    Path('src/config_merged.json').write_text(json.dumps(original))
    calls=[]
    def flow(args,**kwargs):
        assert 'LIBRELANE_IMAGE_OVERRIDE' not in os.environ
        config=json.loads(Path(args[-1]).read_text())
        assert config['SYNTH_STRATEGY']==strategy
        assert config['CLOCK_PERIOD']==20 and config['MACROS']==original['MACROS']
        assert config['GRT_ADJUSTMENT']==0.16
        assert config['GRT_RESIZER_HOLD_SLACK_MARGIN']==0.05
        assert Path(config['PNR_SDC_FILE']).resolve()==Path('src/signoff.sdc').resolve()
        assert args[args.index('--to')+1]=='OpenROAD.GlobalRouting'
        stage=Path('runs/rtl-grt-screen/flow/35-openroad-globalrouting')
        stage.mkdir()
        saved=stage/'saved';saved.write_text('checkpoint')
        (stage/'state_out.json').write_text(json.dumps({k:str(saved) for k in ('odb','def','nl','pnl','sdc')}))
        calls.append('flow')
    monkeypatch.setattr(runner.subprocess,'run',flow)
    def timing(config,before,output,pdk,**kwargs):
        assert 'LIBRELANE_IMAGE_OVERRIDE' not in os.environ
        assert kwargs['repair_corners']==runner.CORNERS
        assert kwargs['setup_margin']==0
        assert kwargs['sdc']==Path('src/signoff.sdc')
        calls.append('timing')
    monkeypatch.setattr(runner,'screen',timing)
    runner.main()
    assert calls==['flow','timing']
    assert json.loads(Path('src/config_merged.json').read_text())==original
    receipt=json.loads(Path('runs/rtl-grt-screen/native_mapping.json').read_text())
    assert receipt['custom_image'] is False and receipt['regional_reservation'] is False
    assert receipt['official_signoff'] is False


def test_matched_native_workflow_has_identical_hardware_and_stock_image():
    root=Path(__file__).parents[2]
    wf=yaml.safe_load((root/'.github/workflows/gds-native-mapping-screen.yaml').read_text())
    job=wf['jobs']['harden']
    assert job['strategy']['matrix']['strategy']==['AREA 0','AREA 1']
    assert job['env']['VARIANT']=='bs-event-late'
    assert job['env']['ALL_CORNER_REPAIR']=='1'
    assert job['env']['CANDIDATE_SHA']=='3393eea9a58c5cad9077cc360a8515d0e5ec8284'
    assert not any('docker build' in s.get('run','') for s in job['steps'])
    assert any('timing_trial.py' in s.get('run','') for s in job['steps'])
