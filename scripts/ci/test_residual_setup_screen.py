import json
from pathlib import Path

import pytest
import yaml

import event_nor2_screen as screen
from test_hold_leaves_route import repair_chain, write

DRIVER = "sg13cmos5l_a21oi_1 _38386_ (.A1(_12085_), .A2(_12163_), .B1(_12191_), .Y(_12192_));"


def source_tree(tmp_path, monkeypatch):
    from test_drop_driver_screen import source_tree as prior_tree
    from residual_setup import TARGETS
    state = prior_tree(tmp_path, monkeypatch)
    added = '\n'.join(old+' '+name+' ('+', '.join('.'+p+'('+v+')' for p,v in pins.items())+');'
                      for name,old,new,pins in TARGETS)
    for path in Path('.').rglob('*.v'):
        path.write_text(path.read_text()+'\n'+added)
    before = Path(state['nl']).read_text()
    changed = before.replace('a21oi_1 _38386_', 'a21oi_2 _38386_')
    root = Path('runs/drop-driver')
    write(root/'grt/1-openroad-globalrouting/tt_um_tripwire.baseline.nl.v',before)
    write(root/'grt/1-openroad-globalrouting/tt_um_tripwire.eco.nl.v',changed)
    state = dict(state, nl=str(write(root/'final.v',changed)))
    write(root/'antenna/3-openroad-checkantennas-1/eco_state.json',state)
    return state


def resized(before):
    from residual_setup import TARGETS
    for name,old,new,pins in TARGETS:
        before=before.replace(old+' '+name+' ', new+' '+name+' ')
    return before


def powered(text):
    from residual_setup import TARGETS
    for name,old,new,pins in TARGETS:
        text=text.replace(new+' '+name+' (',new+' '+name+' (.VDD(power), .VSS(ground), ')
    return text


@pytest.mark.parametrize('failure', [None, 'net', 'master', 'extra', 'clock', 'leaf', 'destination'])
def test_only_one_driver_master_changes(tmp_path, monkeypatch, failure):
    state = source_tree(tmp_path, monkeypatch)
    original = Path(state['nl']).read_text()
    changed = resized(original)
    if failure:
        changed = {'net': changed.replace('_16770_', 'wrong'),
                   'master': original,
                   'extra': changed + '\nsg13cmos5l_inv_1 extra (.A(a), .Y(b));',
                   'clock': changed.replace('.CLK(clk)', '.CLK(wrong)', 1),
                   'leaf': changed.replace('tripwire_drop_hold_buf_46568_', 'wrong'),
                   'destination': changed.replace('.D(tripwire_drop_hold_net_46568_)', '.D(wrong)')}[failure]
        with pytest.raises(ValueError): screen.validate_residual_netlist(original, changed)
    else:
        screen.validate_residual_netlist(original, changed)
        with pytest.raises(ValueError): screen.validate_residual_netlist(changed, changed)


@pytest.mark.parametrize('failure', [None, 'source_hold', 'history', 'provenance', 'fresh_hold', 'fresh_setup'])
def test_driver_screen_uses_qualified_source_and_fresh_measurements(tmp_path, monkeypatch, failure):
    state = source_tree(tmp_path, monkeypatch)
    root = Path('runs/drop-driver')
    source = root / 'antenna/3-openroad-checkantennas-1/eco_state.json'
    for key,value in dict(ECO_PROFILE='residual-setup', PDK_ROOT='/pdk', REPAIR_ECO_ANTENNAS='1').items():
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
                 eco_profile='drop-driver', source_screen=screen.DRIVER_SOURCE_RUN,
                 minimum_fast_hold_ns=0.05, fast_hold_margin_pass=True)
    if failure == 'history': gates['source_screen']=1
    write(root/'gates.json',gates)
    marker = '+ repair_antennas diode\nTRIPWIRE antenna overflow audit: incremental repair completed with congestion disallowed\n'
    write(root/'antenna/2-openroad-repairantennas/1-openroad-diodeinsertion/openroad-diodeinsertion.log',marker)
    run = write('run.json',dict(id=screen.RESIDUAL_SOURCE_RUN, head_branch='main', conclusion='success',
                              path='.github/workflows/gds-drop-driver-screen.yaml'))
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
    after=resized(before)
    calls=[]
    def physical(args,**kwargs):
        config=json.loads(Path(args[-1]).read_text())
        steps=config['meta']['flow']
        dest=Path(args[args.index('--force-run-dir')+1]);calls.append(steps)
        if steps==['OpenROAD.GlobalRouting']:
            stage=dest/'1-openroad-globalrouting';stage.mkdir()
            write(stage/'tt_um_tripwire.baseline.nl.v',before)
            write(stage/'tt_um_tripwire.eco.nl.v',after)
            write(stage/'tt_um_tripwire.eco.pnl.v',powered(after))
            write(stage/'openroad-globalrouting.log','TRIPWIRE residual setup:\nTRIPWIRE hotspot screen:\nFinal congestion report:\n'+''.join(f'Metal{i} 100 50 50.00% 0 / 0 / 0\n' for i in range(1,5)))
        else:
            assert config['GRT_ALLOW_CONGESTION'] is False
            stage=dest/'3-openroad-checkantennas-1';stage.mkdir()
            write(stage/'tt_um_tripwire.eco.nl.v',after)
            write(stage/'tt_um_tripwire.eco.pnl.v',powered(after))
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
            assert json.loads(Path('runs/residual-setup/gates.json').read_text())['ready_for_route_review'] is False
        else: assert not calls
    else:
        screen.main()
        gate=json.loads(Path('runs/residual-setup/gates.json').read_text())
        assert gate['source_screen']==screen.RESIDUAL_SOURCE_RUN
        assert gate['ready_for_route_review'] is True and gate['drt_launched'] is False
        assert gate['minimum_fast_hold_ns']==0.05
        assert len(calls)==2


