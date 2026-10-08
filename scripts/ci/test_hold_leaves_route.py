import json
from pathlib import Path

import pytest

import event_nor2_route as route
from drop_leaf_hold import TARGETS


@pytest.mark.parametrize('failure', [None, 'id', 'conclusion', 'head_branch', 'path'])
def test_exact_successful_hold_screen_required(failure):
    data = dict(id=route.HOLD_SCREEN_RUN, conclusion='success', head_branch='main',
                path='.github/workflows/gds-drop-leaf-hold-screen.yaml')
    if failure:
        data[failure] = 'wrong'
        with pytest.raises(ValueError):
            route.validate_run(data, route.HOLD_SCREEN_RUN)
    else:
        assert route.validate_run(data, route.HOLD_SCREEN_RUN) == 'hold'


@pytest.mark.parametrize('field', [None, 'eco_profile', 'source_screen',
                                  'minimum_fast_hold_ns', 'fast_hold_margin_pass'])
def test_saved_margin_policy_and_history(field):
    gate = dict(eco_profile='drop-hold', source_screen=37803300460,
                minimum_fast_hold_ns=0.05, fast_hold_margin_pass=True)
    if field:
        gate[field] = 'wrong'
        with pytest.raises(ValueError):
            route.validate_hold_history(gate)
    else:
        route.validate_hold_history(gate)


def write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content if isinstance(content, str) else json.dumps(content))
    return path


def repair_chain():
    original = ('sg13cmos5l_nor2_1 _27853_ (.A(_21095_), .B(_02509_), .Y(_02510_));\n'
                'sg13cmos5l_nor2_1 _31567_ (.A(_05964_), .B(_05968_), .Y(_05970_));\n')
    for sink, net, driver, master in TARGETS:
        original += f'{master} {driver} (.Y({net}));\n'
        original += f'sg13cmos5l_dfrbpq_1 {sink} (.D({net}), .Q(q{sink}), .CLK(clk), .RESET_B(reset));\n'
    inherited = write('inherited.v', original)
    write('runs/placement-route/antenna/3-openroad-checkantennas-1/state_out.json', {'nl': str(inherited)})
    baseline = original + '\n'.join(f'sg13cmos5l_antennanp ant{i} (.A(_02510_));' for i in range(92))
    prior = None
    for root, kind in [('runs/event-nor2', 'nor2'), ('runs/drop-event', 'drop'), ('runs/drop-hold', 'hold')]:
        if prior:
            baseline = prior
        folder = Path(root) / 'grt/1-openroad-globalrouting'
        write(folder / 'tt_um_tripwire.baseline.nl.v', baseline)
        if kind == 'nor2':
            changed = baseline.replace('nor2_1 _27853_', 'nor2_2 _27853_')
        elif kind == 'drop':
            changed = baseline.replace('nor2_1 _31567_', 'nor2_2 _31567_')
        else:
            changed = baseline
            for sink, net, *_ in TARGETS:
                name = f'tripwire_drop_hold_net{sink}'
                changed = changed.replace(f'.D({net})', f'.D({name})')
                changed += f'\nsg13cmos5l_buf_1 tripwire_drop_hold_buf{sink} (.A({net}), .X({name}));'
        write(folder / 'tt_um_tripwire.eco.nl.v', changed)
        prior = changed + f'\nsg13cmos5l_antennanp ant_{kind} (.A(_02510_));'
        nl = write(Path(root) / 'final.v', prior)
        state = dict(nl=str(nl), spef=None, sdf=None, lib=None)
        for key in ('odb', 'def', 'pnl', 'sdc'):
            state[key] = str(write(Path(root) / f'final.{key}', 'checkpoint'))
        write(Path(root) / 'antenna/3-openroad-checkantennas-1/eco_state.json', state)
    return state


@pytest.mark.parametrize('failure', [None, 'source_snapshot', 'hold_snapshot', 'extra_logic', 'clock'])
def test_every_transition_audited(tmp_path, monkeypatch, failure):
    monkeypatch.chdir(tmp_path)
    state = repair_chain()
    if failure:
        path = {'source_snapshot': 'runs/drop-event/grt/1-openroad-globalrouting/tt_um_tripwire.baseline.nl.v',
                'hold_snapshot': 'runs/drop-hold/grt/1-openroad-globalrouting/tt_um_tripwire.baseline.nl.v',
                'extra_logic': state['nl'], 'clock': state['nl']}[failure]
        p = Path(path)
        text = p.read_text()
        p.write_text(text.replace('.CLK(clk)', '.CLK(wrong)', 1) if failure == 'clock'
                     else text + '\nsg13cmos5l_inv_1 extra (.A(a), .Y(b));')
        with pytest.raises(ValueError):
            route.validate_repair_chain(Path('runs/drop-hold'), state, held=True)
    else:
        route.validate_repair_chain(Path('runs/drop-hold'), state, held=True)


@pytest.mark.parametrize('failure', [None, 'fresh_setup', 'fresh_hold', 'source_hold', 'stale', 'history'])
def test_held_checkpoint_routes_only_after_fresh_sta(tmp_path, monkeypatch, failure):
    monkeypatch.chdir(tmp_path)
    state = repair_chain()
    root = Path('runs/drop-hold')
    source = root / 'antenna/3-openroad-checkantennas-1/eco_state.json'
    if failure == 'stale':
        state['spef'] = 'inherited.spef'
        write(source, state)
    for k, v in dict(SOURCE_VARIANT=route.VARIANT, SOURCE_RUN_ID=str(route.SOURCE_RUN),
                     REPAIRED_SOURCE_RUN_ID=str(route.HOLD_SCREEN_RUN), PRE_ROUTE_HOLD_TARGET='source',
                     REPAIR_POSTANTENNA_HOLD='0', PDK_ROOT='/pdk').items():
        monkeypatch.setenv(k, v)
    data = dict(after_state=str(source), corners={c: {'after': {
        **{f'timing__{kind}__ws__corner:{c}': 0.08 if kind == 'hold' else 0 for kind in ('hold', 'setup')},
        **{f'timing__{kind}_vio__count__corner:{c}': 0 for kind in ('hold', 'setup')}
    }} for c in route.CORNERS})
    if failure == 'source_hold':
        data['corners'][route.CORNERS[0]]['after'][f'timing__hold__ws__corner:{route.CORNERS[0]}'] = 0.049
    write(root / 'timing/comparison.json', data)
    gates = dict(source_route=route.ROUTE_RUN, ready_for_route_review=True, drt_launched=False,
                 state=str(source), antenna_repair_requested=True, eco_profile='drop-hold',
                 source_screen=37803300460, minimum_fast_hold_ns=0.05, fast_hold_margin_pass=True)
    if failure == 'history': gates['source_screen'] = 1
    write(root / 'gates.json', gates)
    write(source.with_name('or_metrics_out.json'), dict(antenna__violating__nets=0, antenna__violating__pins=0))
    zero = 'Final congestion report:\n' + ''.join(f'Metal{i} 100 50 50.00% 0 / 0 / 0\n' for i in range(1, 5))
    write(root / 'grt/1-openroad-globalrouting/openroad-globalrouting.log', zero)
    write(root / 'antenna/2-openroad-repairantennas/1-openroad-diodeinsertion/openroad-diodeinsertion.log',
          '+ repair_antennas diode\nTRIPWIRE antenna overflow audit: incremental repair completed with congestion disallowed\n')
    run = write('run.json', dict(id=route.HOLD_SCREEN_RUN, conclusion='success', head_branch='main',
                               path='.github/workflows/gds-drop-leaf-hold-screen.yaml'))
    identity = {'source_run_id': route.SOURCE_RUN}
    write(root / 'source_identity.json', identity)
    trusted = write('identity.json', identity)
    real_read = Path.read_text
    def read(path, *args, **kwargs):
        if str(path) == '/tmp/placement-repaired-run.json': return real_read(run)
        if str(path) == '/tmp/placement-source-identity.json': return real_read(trusted)
        return real_read(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', read)
    monkeypatch.setattr(route, 'validate_identity', lambda value, *args: value)
    write('src/signoff.sdc', 'fully timed constraints')
    write('src/config_rx_screen.json', dict(CLOCK_PERIOD=20, GRT_ADJUSTMENT=0.16,
          PNR_SDC_FILE=str(Path('src/signoff.sdc').resolve())))
    def sta(config, before, output, pdk, **kwargs):
        assert before == source and kwargs['repaired'] == source
        assert output.name == 'hold-leaves-sta'
        assert os_env('LIBRELANE_IMAGE_OVERRIDE') == 'tripwire-hotspot:local'
        fresh = json.loads(json.dumps(data))
        if failure in ('fresh_setup', 'fresh_hold'):
            kind = failure.split('_')[1]
            fresh['corners'][route.CORNERS[0]]['after'][f'timing__{kind}__ws__corner:{route.CORNERS[0]}'] = -0.001
        write(output / 'comparison.json', fresh)
    def os_env(key):
        import os
        return os.environ[key]
    monkeypatch.setattr(route, 'screen', sta)
    calls = []
    monkeypatch.setattr(route.subprocess, 'run', lambda args, **kwargs: calls.append(args))
    if failure:
        with pytest.raises(ValueError): route.main()
        assert not calls
        assert not Path('runs/placement-route/drt').exists()
    else:
        route.main()
        assert len(calls) == 1
        assert calls[0][calls[0].index('--with-initial-state') + 1] == str(source)
        config = json.loads(Path('src/config_event_nor2_drt.json').read_text())
        assert config['meta']['flow'] == ['OpenROAD.DetailedRouting']
