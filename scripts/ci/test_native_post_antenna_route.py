import copy
import json
from pathlib import Path
import pytest
import native_post_antenna_route as runner
from native_stock_screen import configure
from native_post_antenna_screen import configure as final_configure


def receipts():
    run=dict(id=runner.SOURCE_RUN,head_sha=runner.SOURCE_SHA,head_branch='main',
             conclusion='success',path='.github/workflows/gds-native-post-timing-antenna-screen.yaml')
    gate=dict(qualified=True,minimum_fast_hold_ns=.05,clean_synthesis=True,checkpoint_ecos=False,
              custom_image=False,physical_screen_only=True,official_signoff=False,
              final_native_antenna_repair=True,stock_sequence=False,estimated_margin_pass=True,
              estimated_margin_limit=.45)
    recipe=dict(source_variant='bs-event-late',synthesis_strategy='AREA 1',stock_sequence=False,
                stock_prefix_sequence=True,checkpoint_ecos=False,post_grt_design_repair=True,
                hold_target_ns=.10,clock_sink_clustering_size=8,repair_corners=list(runner.CORNERS),
                extra_native_steps=['OpenROAD.RepairAntennas'])
    return run,gate,recipe


@pytest.mark.parametrize('part,key,value',[(0,'head_sha','wrong'),(0,'id',1),
    (0,'conclusion','failure'),(0,'path','wrong'),(0,'head_branch','trial'),
    (1,'qualified',False),(1,'custom_image',True),(1,'minimum_fast_hold_ns',0),
    (1,'estimated_margin_pass',False),(1,'estimated_margin_limit',1),
    (1,'final_native_antenna_repair',False),(1,'checkpoint_ecos',True),
    (2,'extra_native_steps',[]),(2,'stock_sequence',True),(2,'hold_target_ns',.05)])
def test_provenance_binds_only_passing_native_source(part,key,value):
    values=receipts()
    runner.validate_provenance(*values)
    values[part][key]=value
    with pytest.raises(ValueError):runner.validate_provenance(*values)


@pytest.mark.parametrize('fault',[None,'hardware','config','fresh_gate'])
def test_main_refuses_route_until_all_checks_pass(tmp_path,monkeypatch,fault):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('PDK_ROOT','/pdk')
    monkeypatch.setenv('LIBRELANE_IMAGE_OVERRIDE','unreviewed')
    Path('src').mkdir();Path('src/signoff.sdc').write_text('exact constraints')
    config=final_configure(configure(dict(CLOCK_PERIOD=20,PL_TARGET_DENSITY_PCT=56),
        'AREA 1',Path('src/signoff.sdc'),hold_target=.10,clock_cluster=8))
    Path('src/config_native_stock.json').write_text(json.dumps(config))
    trusted=copy.deepcopy(config)
    if fault=='config':trusted['CLOCK_PERIOD']=21
    monkeypatch.setattr(runner,'fingerprints',lambda p:{'src/a.v':'changed' if fault=='hardware' else 'same'})
    # Keep /tmp trust evidence isolated during this test.
    original_read=Path.read_text
    run,gates,recipe=receipts()
    mapping={'/tmp/native-trusted-config.json':trusted,'/tmp/native-trusted-files.json':{'src/a.v':'same'},
             '/tmp/native-source-run.json':run}
    def read(p,*a,**k):
        return json.dumps(mapping[str(p)]) if str(p) in mapping else original_read(p,*a,**k)
    monkeypatch.setattr(Path,'read_text',read)
    runner.ROOT.mkdir(parents=True)
    (runner.ROOT/'gates.json').write_text(json.dumps(gates))
    (runner.ROOT/'recipe.json').write_text(json.dumps(recipe))
    source=Path('audited_state.json');source.write_text('{}')
    monkeypatch.setattr(runner,'validate_checkpoint',lambda *a:source)
    calls=[]
    def step(config,source,out,steps):
        calls.append(steps)
        out.mkdir(parents=True)
        d=out/'1-openroad-checkantennas';d.mkdir()
        (d/'or_metrics_out.json').write_text('{}')
    monkeypatch.setattr(runner,'run_step',step)
    def screen(*a,**k):
        assert k['repaired']==source and k['extra_tcl'].name=='electrical_margin_probe.tcl'
        assert 'LIBRELANE_IMAGE_OVERRIDE' not in runner.os.environ
    monkeypatch.setattr(runner,'screen',screen)
    monkeypatch.setattr(runner,'evaluate_saved',lambda *a:dict(qualified=fault!='fresh_gate'))
    import electrical_incremental_route
    monkeypatch.setattr(electrical_incremental_route,'continue_route',lambda *a,**k:calls.append('route'))
    if fault:
        with pytest.raises(ValueError):runner.main()
        assert 'route' not in calls
    else:
        runner.main()
        assert calls==[['OpenROAD.CheckAntennas'],'route']
        assert json.loads((runner.OUTPUT/'gates.json').read_text())['repair_repeated'] is False


def test_workflow_restores_exact_source_after_trusted_prepare():
    import yaml
    path=Path(__file__).resolve().parents[2]/'.github/workflows/gds-native-post-timing-antenna-route.yaml'
    job=yaml.safe_load(path.read_text())['jobs']['harden'];steps=job['steps']
    download=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    prepare=next(s for s in steps if s['name'].startswith('Prepare trusted'))
    assert steps.index(prepare)<steps.index(download)
    assert download['with']['run-id']==runner.SOURCE_RUN
    assert download['with']['name']==f'gds-native-post-timing-antenna-area1-{runner.SOURCE_RUN}'
    assert job['timeout-minutes']==350
    assert 'native_post_antenna_route.py --prepare' in prepare['run']


@pytest.mark.parametrize('fault',[None,'measured_state','receipt_state','readback','saved_gate'])
def test_checkpoint_rejects_mismatched_measurements_and_views(tmp_path,monkeypatch,fault):
    from test_native_post_antenna import fixture_states
    prior,raw,timing=fixture_states(tmp_path)
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    monkeypatch.setattr(runner,'checkpoint',lambda root,final_antenna=False:raw if final_antenna else prior)
    monkeypatch.setattr(runner,'validate_overflow',lambda log:None)
    (prior.parent/'openroad-resizertimingpostgrt.log').write_text('audited full GRT')
    log=raw.parent/'1-openroad-diodeinsertion/openroad-diodeinsertion.log'
    log.parent.mkdir();log.write_text('+ repair_antennas sg13cmos5l_antennanp -ratio_margin 50\n')
    source=runner.audit_post_antenna(prior,raw,timing)
    receipt=dict(final_state=str(source),final_timing_root=str(timing),qualified=True)
    recipe=dict(receipt)
    (timing/'comparison.json').write_text(json.dumps({'after_state':str(raw if fault!='measured_state' else prior)}))
    ant=tmp_path/'antenna/1-openroad-checkantennas';ant.mkdir(parents=True)
    (ant/'or_metrics_out.json').write_text('{}')
    monkeypatch.setattr(runner,'evaluate_saved',lambda *a:dict(qualified=True))
    if fault=='receipt_state':recipe['final_state']=str(prior)
    if fault=='saved_gate':receipt['qualified']=False
    if fault=='readback':
        saved=json.loads(source.read_text());saved['nl']='stale.v';source.write_text(json.dumps(saved))
    if fault:
        with pytest.raises(ValueError):runner.validate_checkpoint({'GRT_ALLOW_CONGESTION':False},receipt,recipe)
    else:
        assert runner.validate_checkpoint({'GRT_ALLOW_CONGESTION':False},receipt,recipe)==source
