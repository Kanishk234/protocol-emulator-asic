import json
from pathlib import Path

import pytest
import yaml

import event_nor2_screen as screen
from test_hold_leaves_route import repair_chain, write

DRIVER = "sg13cmos5l_a21oi_1 _38386_ (.A1(_12085_), .A2(_12163_), .B1(_12191_), .Y(_12192_));"


def source_tree(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state = repair_chain()
    for p in Path('.').rglob('*.v'):
        p.write_text(p.read_text() + '\n' + DRIVER)
    return state


@pytest.mark.parametrize('failure', [None, 'net', 'master', 'extra', 'clock', 'leaf', 'destination'])
def test_only_one_driver_master_changes(tmp_path, monkeypatch, failure):
    state = source_tree(tmp_path, monkeypatch)
    original = Path(state['nl']).read_text()
    changed = original.replace('a21oi_1 _38386_', 'a21oi_2 _38386_')
    if failure:
        changed = {'net': changed.replace('_12163_', 'wrong'),
                   'master': original,
                   'extra': changed + '\nsg13cmos5l_inv_1 extra (.A(a), .Y(b));',
                   'clock': changed.replace('.CLK(clk)', '.CLK(wrong)', 1),
                   'leaf': changed.replace('tripwire_drop_hold_buf_46568_', 'wrong'),
                   'destination': changed.replace('.D(tripwire_drop_hold_net_46568_)', '.D(wrong)')}[failure]
        with pytest.raises(ValueError): screen.validate_driver_netlist(original, changed)
    else:
        screen.validate_driver_netlist(original, changed)
        with pytest.raises(ValueError): screen.validate_driver_netlist(changed, changed)


def test_missing_powered_driver_and_stale_views(tmp_path, monkeypatch):
    state = source_tree(tmp_path, monkeypatch)
    original = Path(state['nl'])
    before = original.read_text()
    changed = before.replace('a21oi_1 _38386_', 'a21oi_2 _38386_')
    state_path = write('eco/state.json', dict(odb='eco/chip.odb', spef='old', sdf='old', lib='old'))
    write('eco/chip.baseline.nl.v', before)
    write('eco/chip.eco.nl.v', changed)
    write('eco/chip.eco.pnl.v', before)
    with pytest.raises(ValueError, match='Powered netlist missing driver'):
        screen.promote_netlists(state_path, original, driver=True)
    write('eco/chip.eco.pnl.v', changed)
    output = json.loads(screen.promote_netlists(state_path, original, driver=True).read_text())
    assert all(output[k] is None for k in ('spef', 'sdf', 'lib'))


@pytest.mark.parametrize('failure', [None, 'source_hold', 'history', 'provenance', 'fresh_hold', 'fresh_setup'])
def test_driver_screen_uses_qualified_source_and_fresh_measurements(tmp_path, monkeypatch, failure):
    state = source_tree(tmp_path, monkeypatch)
    root = Path('runs/drop-hold')
    source = root / 'antenna/3-openroad-checkantennas-1/eco_state.json'
    for key,value in dict(ECO_PROFILE='drop-driver', PDK_ROOT='/pdk', REPAIR_ECO_ANTENNAS='1').items():
        monkeypatch.setenv(key,value)
    data = dict(after_state=str(source), corners={c: {'after': {
        **{f'timing__{kind}__ws__corner:{c}': 0.1 if kind == 'hold' else 0 for kind in ('hold','setup')},
        **{f'timing__{kind}_vio__count__corner:{c}': 0 for kind in ('hold','setup')}
    }} for c in screen.CORNERS})
    if failure == 'source_hold':
        data['corners'][screen.CORNERS[0]]['after'][f'timing__hold__ws__corner:{screen.CORNERS[0]}'] = 0.049
    write(root / 'timing/comparison.json',data)
    gates = dict(state=str(source), source_route=screen.ROUTE_RUN, ready_for_route_review=True,
                 antenna_repair_requested=True, antenna_nets=0, antenna_pins=0,
                 eco_profile='drop-hold', source_screen=screen.HOLD_SOURCE_RUN,
                 minimum_fast_hold_ns=0.05, fast_hold_margin_pass=True)
    if failure == 'history': gates['source_screen']=1
    write(root/'gates.json',gates)
    marker = '+ repair_antennas diode\nTRIPWIRE antenna overflow audit: incremental repair completed with congestion disallowed\n'
    write(root/'antenna/2-openroad-repairantennas/1-openroad-diodeinsertion/openroad-diodeinsertion.log',marker)
    run = write('run.json',dict(id=screen.DRIVER_SOURCE_RUN, head_branch='main', conclusion='success',
                              path='.github/workflows/gds-drop-leaf-hold-screen.yaml'))
    if failure == 'provenance': write(run, dict(id=1,head_branch='main',conclusion='success',path='wrong'))
    identity = {'source_run_id':screen.SOURCE_RUN}
    write(root/'source_identity.json',identity)
    trusted=write('identity.json',identity)
    real_read=Path.read_text
    def read(path,*args,**kwargs):
        if str(path)=='/tmp/event-nor2-route-run.json': return real_read(run)
        if str(path)=='/tmp/placement-source-identity.json': return real_read(trusted)
        return real_read(path,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',read)
    monkeypatch.setattr(screen,'validate_identity',lambda value,*args:value)
    write('src/signoff.sdc','fully timed')
    write('src/config_rx_screen.json',dict(CLOCK_PERIOD=20,PL_TARGET_DENSITY_PCT=56,GRT_ADJUSTMENT=0.16,
          PL_TIMING_DRIVEN=True,PL_OPTIMIZE_MIRRORING=False,PNR_SDC_FILE=str(Path('src/signoff.sdc').resolve())))
    before=Path(state['nl']).read_text()
    after=before.replace('a21oi_1 _38386_','a21oi_2 _38386_')
    calls=[]
    def physical(args,**kwargs):
        config=json.loads(Path(args[-1]).read_text())
        steps=config['meta']['flow']
        dest=Path(args[args.index('--force-run-dir')+1]);calls.append(steps)
        if steps==['OpenROAD.GlobalRouting']:
            stage=dest/'1-openroad-globalrouting';stage.mkdir()
            write(stage/'tt_um_tripwire.baseline.nl.v',before)
            write(stage/'tt_um_tripwire.eco.nl.v',after)
            write(stage/'tt_um_tripwire.eco.pnl.v',after)
            write(stage/'openroad-globalrouting.log','TRIPWIRE drop-driver sizing:\nTRIPWIRE hotspot screen:\nFinal congestion report:\n'+''.join(f'Metal{i} 100 50 50.00% 0 / 0 / 0\n' for i in range(1,5)))
        else:
            assert config['GRT_ALLOW_CONGESTION'] is False
            stage=dest/'3-openroad-checkantennas-1';stage.mkdir()
            write(stage/'tt_um_tripwire.eco.nl.v',after)
            write(stage/'tt_um_tripwire.eco.pnl.v',after)
            write(stage/'or_metrics_out.json',dict(antenna__violating__nets=0,antenna__violating__pins=0))
            write(dest/'2-openroad-repairantennas/1-openroad-diodeinsertion/openroad-diodeinsertion.log',marker)
        fresh=dict(state,odb=str(stage/'tt_um_tripwire.odb'))
        write(stage/'state_out.json',fresh)
    monkeypatch.setattr(screen.subprocess,'run',physical)
    def sta(config,before_state,output,pdk,**kwargs):
        fresh=json.loads(json.dumps(data));fresh['after_state']=str(kwargs['repaired'])
        if failure in ('fresh_setup','fresh_hold'):
            kind=failure.split('_')[1]
            fresh['corners'][screen.CORNERS[0]]['after'][f'timing__{kind}__ws__corner:{screen.CORNERS[0]}']=-0.001
        write(output/'comparison.json',fresh)
    monkeypatch.setattr(screen,'screen',sta)
    if failure:
        with pytest.raises(ValueError):screen.main()
        if failure.startswith('fresh_'):
            assert len(calls)==2
            assert json.loads(Path('runs/drop-driver/gates.json').read_text())['ready_for_route_review'] is False
        else: assert not calls
    else:
        screen.main()
        gate=json.loads(Path('runs/drop-driver/gates.json').read_text())
        assert gate['source_screen']==screen.DRIVER_SOURCE_RUN
        assert gate['ready_for_route_review'] is True and gate['drt_launched'] is False
        assert gate['minimum_fast_hold_ns']==0.05
        assert len(calls)==2


def test_frozen_workflow_and_single_helper():
    root=Path(__file__).parents[2]
    wf=yaml.safe_load((root/'.github/workflows/gds-drop-driver-screen.yaml').read_text())
    job=wf['jobs']['harden']
    assert job['env']['ECO_PROFILE']=='drop-driver'
    step=next(s for s in job['steps'] if s.get('uses','').startswith('actions/download-artifact'))
    assert step['with']['run-id']==screen.DRIVER_SOURCE_RUN
    assert step['with']['name']=='gds-drop-leaf-hold-37806209914'
    docker=(root/'scripts/ci/Dockerfile.openroad-drop-driver').read_text()
    assert 'COPY drop_driver_size.tcl' in docker
    assert 'COPY drop_leaf_hold.tcl' not in docker
