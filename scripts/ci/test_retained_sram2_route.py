import copy
import json
from pathlib import Path
import pytest
import retained_sram2_route as runner


def source():
    return (dict(id=runner.SOURCE_RUN, head_sha=runner.SOURCE_SHA, head_branch='main',
                 conclusion='success', path='.github/workflows/gds-retained-sram2-screen.yaml'),
            dict(source_run=38116800326, kind='relocate', added_buffers=0, changed_cells=0, relocated_instances=1, qualified=True,
                 minimum_fast_hold_ns=.05, physical_screen_only=True))


def test_exact_source_passes():
    runner.validate_provenance(*source())


@pytest.mark.parametrize('part,key,value', [(0,'id',1),(0,'head_sha','wrong'),
    (0,'head_branch','other'),(0,'conclusion','failure'),(0,'path','wrong'),
    (1,'changed_cells',1),(1,'relocated_instances',0),(1,'source_run',1),(1,'added_buffers',1),(1,'kind','hold'),(1,'qualified',False),
    (1,'minimum_fast_hold_ns',.01),(1,'physical_screen_only',False)])
def test_source_and_gate_cannot_be_replaced(part,key,value):
    data=list(source());data[part][key]=value
    with pytest.raises(ValueError): runner.validate_provenance(*data)


@pytest.mark.parametrize('timing_ok', [True, False])
@pytest.mark.parametrize('antenna_ok', [True, False])
def test_continuation_runs_drt_only_after_fresh_gates(tmp_path,monkeypatch,timing_ok,antenna_ok):
    import sys,types
    from postgrt_timing import CORNERS
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('PDK_ROOT','/pdk')
    monkeypatch.setenv('LIBRELANE_IMAGE_OVERRIDE','unreviewed')
    run,gate=source()
    def write(path,value):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))
    root=Path('runs/retained-sram2-screen')
    write(root/'gates.json',gate)
    write(Path('src/config_native_stock.json'),{})
    write(Path('src/config_clock8_residual_relocate.json'),{'GRT_ALLOW_CONGESTION':False})
    Path('runs/extracted-timing').mkdir(parents=True)
    original_read=Path.read_text
    def read(path,*args,**kwargs):
        if str(path)=='/tmp/native-strength-source-run.json':return json.dumps(run)
        if str(path) in ('/tmp/native-trusted-files.json','/tmp/native-trusted-config.json'):return '{}'
        return original_read(path,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',read)
    monkeypatch.setattr(runner,'fingerprints',lambda *args:{})
    source_state=root/'source.json'
    write(source_state,{})
    monkeypatch.setattr(runner,'validate_checkpoint',lambda *args:source_state)
    calls=[]
    def step(config,state,output,steps):
        assert 'LIBRELANE_IMAGE_OVERRIDE' not in runner.os.environ
        assert state==source_state
        calls.append(steps)
        if steps==['OpenROAD.CheckAntennas']:
            write(output/'1-openroad-checkantennas/or_metrics_out.json',
                  {'antenna__violating__nets':0 if antenna_ok else 1,'antenna__violating__pins':0})
    def sta(path,state,output,pdk,repaired,sdc):
        assert state==repaired==source_state
        write(output/'comparison.json',{'corners':{c:{'after':{
            f'timing__setup__ws__corner:{c}':0,
            f'timing__hold__ws__corner:{c}':.06 if timing_ok else .049}} for c in CORNERS}})
    monkeypatch.setattr(runner,'run_step',step)
    monkeypatch.setattr(runner,'screen',sta)
    extracted=[]
    monkeypatch.setitem(sys.modules,'extracted_timing',types.SimpleNamespace(main=lambda path:extracted.append(path)))
    if timing_ok and antenna_ok:
        runner.main()
        assert calls==[['OpenROAD.CheckAntennas'],['OpenROAD.DetailedRouting']]
        assert extracted==[Path('runs/retained-sram2-route/drt')]
        assert Path('runs/retained-sram2-route/source-extracted-timing').is_dir()
    else:
        with pytest.raises(ValueError,match='Fresh native route'):runner.main()
        assert calls==[['OpenROAD.CheckAntennas']]
        assert not extracted


def test_workflow_downloads_exact_qualified_screen():
    import yaml
    path=Path(__file__).resolve().parents[2]/'.github/workflows/gds-retained-sram2-route.yaml'
    workflow=yaml.safe_load(path.read_text())
    steps=workflow['jobs']['harden']['steps']
    download=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert int(download['with']['run-id'])==runner.SOURCE_RUN
    assert download['with']['name']=='gds-retained-sram2-38171124079'




@pytest.mark.parametrize('placement', ['45120 245700', '341280 230580'])
def test_continuation_requires_relocated_destination(placement):
    layout = '- wire9439 sg13cmos5l_buf_4 + PLACED ( ' + placement + ' ) N ;'
    if placement == '45120 245700':
        runner.verify_location(layout)
    else:
        with pytest.raises(ValueError):
            runner.verify_location(layout)


@pytest.mark.parametrize('failure', [None, 'proposal', 'layout', 'reset', 'rewire', 'hold', 'missing'])
def test_complete_hold_chain_is_required(tmp_path, monkeypatch, failure):
    from test_retained_sram2_screen import source as relocation_fixture
    from retained_sram2_plan import plan
    from postgrt_timing import CORNERS
    before, layout = relocation_fixture(monkeypatch)
    proposal = plan(before, layout, 'relocate')
    after = before
    monkeypatch.chdir(tmp_path)
    root = Path('runs/retained-sram2-screen')
    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)
    original = Path('runs/dominant-slew-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v')
    write(original, before)
    write(original.with_name('tt_um_tripwire.def'), layout if failure != 'layout' else layout+'changed')
    if failure == 'proposal': proposal['kind'] = 'hold'
    write(root/'proposal.json', json.dumps(proposal))
    grt = root/'grt/1-openroad-globalrouting'
    write(grt/'tt_um_tripwire.baseline.nl.v', before)
    write(grt/'tt_um_tripwire.eco.nl.v', after if failure != 'rewire' else after.replace('net9439', 'other'))
    write(grt/'openroad-globalrouting.log', 'TRIPWIRE SRAM relocation: wire9439 moved\nexact site/master/nets retained after legalization\n' +
          ('' if failure == 'reset' else 'TRIPWIRE native route reset: cleared 20 ordinary routed wires\n'))
    monkeypatch.setattr(runner, 'validate_overflow', lambda log: None)
    checked = root/'antenna/1-openroad-checkantennas/state_out.json'
    views = {}
    for key in ['odb','def','nl','pnl','sdc']:
        p = checked.parent/('chip.'+key)
        write(p, layout.replace("341280 230580", "45120 245700") if key == "def" else after)
        views[key] = str(p)
    write(checked, json.dumps(views))
    write(checked.parent/'or_metrics_out.json', json.dumps({'antenna__violating__nets':0, 'antenna__violating__pins':0}))
    timing = {'after_state':str(checked), 'corners':{c:{'after':{
        f'timing__setup__ws__corner:{c}':0, f'timing__hold__ws__corner:{c}':.1}} for c in CORNERS}}
    if failure == 'hold': timing['corners'][CORNERS[0]]['after'][f'timing__hold__ws__corner:{CORNERS[0]}'] = .049
    if failure == 'missing': Path(views['pnl']).unlink()
    write(root/'timing/comparison.json', json.dumps(timing))
    if failure:
        with pytest.raises(ValueError): runner.validate_checkpoint(root)
    else:
        assert runner.validate_checkpoint(root) == checked
