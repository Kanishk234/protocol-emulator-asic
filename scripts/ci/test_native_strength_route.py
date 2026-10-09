import copy
import json
from pathlib import Path
import pytest
import native_strength_route as runner


def source():
    return (dict(id=runner.SOURCE_RUN, head_sha=runner.SOURCE_SHA, head_branch='main',
                 conclusion='success', path='.github/workflows/gds-native-hold100-strength-screen.yaml'),
            dict(source_run=37870374707, changes=6, qualified=True,
                 minimum_fast_hold_ns=.05, physical_screen_only=True))


def test_exact_source_passes():
    runner.validate_provenance(*source())


@pytest.mark.parametrize('part,key,value', [(0,'id',1),(0,'head_sha','wrong'),
    (0,'head_branch','other'),(0,'conclusion','failure'),(0,'path','wrong'),
    (1,'source_run',1),(1,'changes',5),(1,'qualified',False),
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
    root=Path('runs/native-hold100-strength')
    write(root/'gates.json',gate)
    write(Path('src/config_native_stock.json'),{})
    write(Path('src/config_native_hold100_strength.json'),{'GRT_ALLOW_CONGESTION':False})
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
        assert extracted==[Path('runs/native-strength-route/drt')]
        assert Path('runs/native-strength-route/source-extracted-timing').is_dir()
    else:
        with pytest.raises(ValueError,match='Fresh native route'):runner.main()
        assert calls==[['OpenROAD.CheckAntennas']]
        assert not extracted


def test_workflow_downloads_exact_qualified_screen():
    import yaml
    path=Path(__file__).resolve().parents[2]/'.github/workflows/gds-native-strength-route.yaml'
    workflow=yaml.safe_load(path.read_text())
    steps=workflow['jobs']['harden']['steps']
    download=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert int(download['with']['run-id'])==runner.SOURCE_RUN
    assert download['with']['name']=='gds-native-hold100-strength-37943825506'


@pytest.mark.parametrize('failure', [None,'state','hold','baseline','change','missing','cleanup','overflow'])
def test_complete_checkpoint_chain_is_required(tmp_path,monkeypatch,failure):
    import hashlib
    from test_native_hold100_size import netlist
    from postgrt_timing import CORNERS
    monkeypatch.chdir(tmp_path)
    root=Path('runs/native-hold100-strength')
    def write(path,text):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    original=Path('runs/extracted-timing/final/nl/tt_um_tripwire.nl.v')
    write(original,netlist())
    monkeypatch.setattr(runner,'SOURCE_SHA256',hashlib.sha256(original.read_bytes()).hexdigest())
    grt=root/'grt/1-openroad-globalrouting'
    write(grt/'tt_um_tripwire.baseline.nl.v',netlist())
    write(grt/'tt_um_tripwire.eco.nl.v',netlist(True))
    write(grt/'openroad-globalrouting.log','TRIPWIRE native hold100 setup:\n'*6)
    def overflow(log):
        if failure=='overflow':raise ValueError('overflow')
    monkeypatch.setattr(runner,'validate_overflow',overflow)
    cleanup=root/'antenna-cleanup'
    state=cleanup/'2-openroad-checkantennas/eco_state.json'
    views={}
    for key in ['odb','def','nl','pnl','sdc']:
        path=state.parent/('final.'+key)
        write(path,netlist(True))
        views[key]=str(path)
    write(state,json.dumps(views))
    write(state.parent/'or_metrics_out.json',json.dumps({'antenna__violating__nets':0,'antenna__violating__pins':0}))
    write(cleanup/'resolved.json',json.dumps({'GRT_ALLOW_CONGESTION':False}))
    write(cleanup/'1-openroad-repairantennas/1-openroad-diodeinsertion/openroad-diodeinsertion.log','repair_antennas\n')
    timing={'after_state':str(state),'corners':{c:{'after':{
        f'timing__setup__ws__corner:{c}':0,f'timing__hold__ws__corner:{c}':.1}} for c in CORNERS}}
    if failure=='state':timing['after_state']='other/state.json'
    if failure=='hold':timing['corners'][CORNERS[0]]['after'][f'timing__hold__ws__corner:{CORNERS[0]}']=.049
    if failure=='baseline':write(grt/'tt_um_tripwire.baseline.nl.v',netlist(True))
    if failure=='change':write(grt/'tt_um_tripwire.eco.nl.v',netlist(True).replace('net7221','wrong'))
    if failure=='missing':Path(views['pnl']).unlink()
    if failure=='cleanup':write(cleanup/'resolved.json',json.dumps({'GRT_ALLOW_CONGESTION':True}))
    write(root/'timing/comparison.json',json.dumps(timing))
    if failure:
        with pytest.raises(ValueError):runner.validate_checkpoint(root)
    else:
        assert runner.validate_checkpoint(root)==state
