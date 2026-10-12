import json
from pathlib import Path
import pytest
import electrical_incremental_route as runner
from native_stock_route import CORNERS


def evidence():
    run=dict(id=runner.SOURCE_RUN,head_sha=runner.SOURCE_SHA,head_branch='main',conclusion='success',path='.github/workflows/gds-electrical-incremental-screen.yaml')
    gates=dict(source_run=38294805019,qualified=True,timing_antenna_qualified=True,electrical_qualified=True,added_buffers=10,minimum_fast_hold_ns=.05,unrelated_routes_preserved_after_rebase=True,initial_full_route=True,live_capacity_initialized=True,custom_image=True,physical_screen_only=True,official_signoff=False)
    return run,gates


@pytest.mark.parametrize('group,key,value',[(0,'id',1),(0,'head_sha','wrong'),(0,'conclusion','failure'),(1,'electrical_qualified',False),(1,'live_capacity_initialized',False),(1,'minimum_fast_hold_ns',.01)])
def test_wrong_source_and_unqualified_evidence_refused(group,key,value):
    args=list(evidence());args[group][key]=value
    with pytest.raises(ValueError):runner.validate_provenance(*args)


def test_workflow_uses_exact_successful_source():
    import yaml
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/gds-electrical-incremental-route.yaml').read_text())
    d=next(s for s in w['jobs']['harden']['steps'] if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==runner.SOURCE_RUN
    assert d['with']['name']==f'gds-electrical-incremental-{runner.SOURCE_RUN}'
    runner.validate_provenance(*evidence())


@pytest.mark.parametrize('fault',[None,'hold','slew','antenna','missing','stale'])
def test_measured_current_views_and_all_gates_required(tmp_path,fault):
    root=tmp_path/'screen'; raw=root/'incremental/1-openroad-globalrouting'; ant=root/'antenna/1-openroad-checkantennas'
    raw.mkdir(parents=True);ant.mkdir(parents=True);(root/'timing').mkdir()
    views={}
    for k in ('odb','def','nl','pnl','sdc'):
        p=raw/('chip.incremental.'+k+'.v' if k in ('nl','pnl') else 'chip.'+k)
        p.write_text('view');views[k]=str(p)
    (raw/'state_out.json').write_text(json.dumps(views))
    (ant/'state_out.json').write_text(json.dumps(views))
    log='Final congestion report:\n'+''.join(f'Metal{i} 100 100 0.0% 0 / 0 / 0\n' for i in range(1,5))+'Total 1000 100 10.0% 0 / 0 / 0\n'
    (raw/'openroad-globalrouting.log').write_text(log+log)
    metrics={'antenna__violating__nets':1 if fault=='antenna' else 0,'antenna__violating__pins':0}
    (ant/'or_metrics_out.json').write_text(json.dumps(metrics))
    corners={c:{'after':{f'timing__setup__ws__corner:{c}':0,f'timing__hold__ws__corner:{c}':.049 if fault=='hold' else .06,**{f'design__max_{kind}_violation__count__corner:{c}':1 if fault=='slew' and kind=='slew' else 0 for kind in ('slew','fanout','cap')}}} for c in CORNERS}
    (root/'timing/comparison.json').write_text(json.dumps({'after_state':str(ant/'state_out.json'),'corners':corners}))
    if fault=='missing':Path(views['odb']).unlink()
    if fault=='stale':
        views['nl']=views['def'];(ant/'state_out.json').write_text(json.dumps(views))
    if fault:
        with pytest.raises(ValueError):runner.validate_checkpoint(root)
    else:assert runner.validate_checkpoint(root)==ant/'state_out.json'


@pytest.mark.parametrize('fault',[None,'hold','slew','antenna','extracted_hold','extracted_slew'])
def test_fresh_gates_block_drt_and_extracted_failures_are_not_success(tmp_path,monkeypatch,fault):
    import sys,types
    monkeypatch.chdir(tmp_path);monkeypatch.setenv('PDK_ROOT','/pdk');monkeypatch.setenv('LIBRELANE_IMAGE_OVERRIDE','custom')
    Path('src').mkdir();Path('runs').mkdir();calls=[]
    source=Path('source.json');nl=Path('source.v');nl.write_text('sg13cmos5l_buf_4 b (.A(a), .X(x));');source.write_text(json.dumps({'nl':str(nl)}))
    def step(config,checkpoint,out,steps):
        assert checkpoint==source and 'LIBRELANE_IMAGE_OVERRIDE' not in runner.os.environ
        calls.extend(steps)
        if steps==['OpenROAD.CheckAntennas']:
            p=out/'1-openroad-checkantennas/or_metrics_out.json';p.parent.mkdir(parents=True);p.write_text(json.dumps({'antenna__violating__nets':1 if fault=='antenna' else 0,'antenna__violating__pins':0}))
    def sta(config,checkpoint,out,pdk,**kwargs):
        out.mkdir(parents=True)
        corners={c:{'after':{f'timing__setup__ws__corner:{c}':0,f'timing__hold__ws__corner:{c}':.049 if fault=='hold' else .06,**{f'design__max_{k}_violation__count__corner:{c}':1 if fault=='slew' else 0 for k in ('slew','fanout','cap')}}} for c in CORNERS}
        (out/'comparison.json').write_text(json.dumps({'corners':corners}))
    def extract(root):
        calls.append('extract');out=Path('runs/extracted-timing');out.mkdir()
        metrics={f'timing__{kind}__ws__corner:{c}':(.049 if fault=='extracted_hold' else .06) if kind=='hold' else 0 for c in CORNERS for kind in ('setup','hold')}
        (out/'corner_summary.json').write_text(json.dumps(metrics));(out/'electrical_summary.json').write_text(json.dumps({c:{'no_reported_electrical_violations':fault!='extracted_slew'} for c in CORNERS}))
        p=out/'2-openroad-checkantennas/or_metrics_out.json';p.parent.mkdir();p.write_text(json.dumps({'antenna__violating__nets':0,'antenna__violating__pins':0}))
    monkeypatch.setattr(runner,'run_step',step);monkeypatch.setattr(runner,'screen',sta);monkeypatch.setattr(runner,'validate_final_route',lambda *args:None)
    monkeypatch.setitem(sys.modules,'extracted_timing',types.SimpleNamespace(main=extract))
    if fault:
        with pytest.raises(ValueError):runner.continue_route({},source,Path('runs/route'))
    else:runner.continue_route({},source,Path('runs/route'))
    if fault in ('hold','slew','antenna'):assert calls==['OpenROAD.CheckAntennas']
    else:assert calls==['OpenROAD.CheckAntennas','OpenROAD.DetailedRouting','extract']
