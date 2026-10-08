import copy
from pathlib import Path
import pytest
import native_stock_route as runner
from native_stock_screen import configure


def source():
    run=dict(id=runner.SOURCE_RUN, conclusion='success', head_branch='main', head_sha=runner.SOURCE_SHA,
             path='.github/workflows/gds-native-stock-screen.yaml')
    recipe=dict(synthesis_strategy='AREA 1', source_variant='bs-event-late', stock_sequence=True,
                checkpoint_ecos=False, repair_corners=list(runner.CORNERS), hold_target_ns=.125)
    config=configure(dict(CLOCK_PERIOD=20,PL_TARGET_DENSITY_PCT=56),'AREA 1',Path('src/signoff.sdc'))
    return run,recipe,config


def test_source_accepts_exact_recipe_and_rejects_hardware_changes():
    run,recipe,config=source()
    runner.validate_source(run,recipe,config,{'src/trw_defs.vh':'a'}, {'src/trw_defs.vh':'a'})
    with pytest.raises(ValueError):
        runner.validate_source(run,recipe,config,{'src/trw_defs.vh':'a'}, {'src/trw_defs.vh':'b'})


@pytest.mark.parametrize('part,key,value',[
    (0,'head_sha','wrong'),(0,'head_branch','trial'),(0,'conclusion','failure'),
    (0,'id',1),(0,'path','wrong'),(1,'synthesis_strategy','AREA 0'),
    (1,'checkpoint_ecos',True),(1,'stock_sequence',False),(1,'hold_target_ns',.05),
    (2,'CLOCK_PERIOD',21),(2,'GRT_ADJUSTMENT',.12),
    (2,'RUN_POST_GRT_RESIZER_TIMING',False)])
def test_rejects_unqualified_source(part,key,value):
    values=list(source());values[part][key]=value
    with pytest.raises(ValueError):runner.validate_source(*values,{}, {})


def timing():
    return {'corners':{c:{'after':{f'timing__setup__ws__corner:{c}':0,
                                 f'timing__hold__ws__corner:{c}':.1}} for c in runner.CORNERS}}


@pytest.mark.parametrize('kind,value',[('setup',-.01),('setup',float('nan')),
                                      ('hold',.049),('hold',float('inf'))])
def test_fresh_margin_rejects_bad_values(kind,value):
    t=timing();c=runner.CORNERS[0];t['corners'][c]['after'][f'timing__{kind}__ws__corner:{c}']=value
    assert not runner.qualified(t,{'antenna__violating__nets':0,'antenna__violating__pins':0})


def test_antenna_and_positive_margin_required():
    assert runner.qualified(timing(),{'antenna__violating__nets':0,'antenna__violating__pins':0})
    assert not runner.qualified(timing(),{})
    assert not runner.qualified(timing(),{'antenna__violating__nets':1,'antenna__violating__pins':1})


@pytest.mark.parametrize('setup_ok',[True,False])
def test_main_gates_route_and_extract_without_repair(tmp_path,monkeypatch,setup_ok):
    import json, sys, types
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('PDK_ROOT','/pdk')
    monkeypatch.setenv('LIBRELANE_IMAGE_OVERRIDE','stale:custom')
    Path('src').mkdir()
    Path('src/signoff.sdc').write_text('fully timed')
    run,recipe,config=source()
    Path('src/config_native_stock.json').write_text(json.dumps(config))
    root=Path('runs/native-stock-screen');root.mkdir(parents=True)
    (root/'recipe.json').write_text(json.dumps(recipe))
    source_path=root/'flow/43-openroad-resizertimingpostgrt/state_out.json'
    source_path.parent.mkdir(parents=True)
    source_path.write_text('{}')
    source_path.with_name('openroad-resizertimingpostgrt.log').write_text('overflow evidence')
    real_read=Path.read_text
    def read(path,*args,**kwargs):
        if str(path)=='/tmp/native-trusted-config.json':return json.dumps(config)
        if str(path)=='/tmp/native-source-run.json':return json.dumps(run)
        if str(path)=='/tmp/native-trusted-files.json':return '{}'
        return real_read(path,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',read)
    monkeypatch.setattr(runner,'fingerprints',lambda root:{})
    monkeypatch.setattr(runner,'checkpoint',lambda root:source_path)
    monkeypatch.setattr(runner,'validate_overflow',lambda log:None)
    calls=[]
    def step(cfg,saved,out,steps):
        import os
        assert 'LIBRELANE_IMAGE_OVERRIDE' not in os.environ
        assert saved==source_path
        assert 'OpenROAD.ResizerTimingPostGRT' not in steps
        calls.append(steps[0]);out.mkdir(parents=True)
        if steps==['OpenROAD.CheckAntennas']:
            stage=out/'1-openroad-checkantennas';stage.mkdir()
            (stage/'or_metrics_out.json').write_text(json.dumps({'antenna__violating__nets':0,'antenna__violating__pins':0}))
    def sta(path,saved,out,pdk,**kwargs):
        assert kwargs['repaired']==saved==source_path
        out.mkdir();t=timing()
        if not setup_ok:
            c=runner.CORNERS[1];t['corners'][c]['after'][f'timing__setup__ws__corner:{c}']=-.01
        (out/'comparison.json').write_text(json.dumps(t));calls.append('STA')
    monkeypatch.setattr(runner,'run_step',step)
    monkeypatch.setattr(runner,'screen',sta)
    fake=types.ModuleType('extracted_timing')
    fake.main=lambda root:calls.append('extract')
    monkeypatch.setitem(sys.modules,'extracted_timing',fake)
    if setup_ok:
        runner.main()
        assert calls==['OpenROAD.CheckAntennas','STA','OpenROAD.DetailedRouting','extract']
    else:
        with pytest.raises(ValueError,match='routing refused'):runner.main()
        assert calls==['OpenROAD.CheckAntennas','STA']
