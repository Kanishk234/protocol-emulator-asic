from pathlib import Path
import json

import pytest

from event_nor2_route import CORNERS, ROUTE_RUN, SCREEN_RUN, validate_gate, validate_run


@pytest.mark.parametrize('failure', [None, 'argument', 'id', 'head_branch', 'conclusion', 'path'])
def test_only_exact_successful_main_screen(failure):
    run = dict(id=SCREEN_RUN, head_branch='main', conclusion='success',
               path='.github/workflows/gds-event-nor2-screen.yaml')
    selected = SCREEN_RUN
    if failure == 'argument':
        selected += 1
    elif failure:
        run[failure] = 0 if failure == 'id' else 'wrong'
    if failure:
        with pytest.raises(ValueError):
            validate_run(run, selected)
    else:
        validate_run(run, selected)


def test_nor2_delegates_before_original_checkpoint_is_loaded(monkeypatch):
    import placement_route
    import event_nor2_route
    monkeypatch.setenv('REPAIRED_SOURCE_RUN_ID', str(SCREEN_RUN))
    monkeypatch.setenv('SOURCE_VARIANT', 'bs-event-late')
    monkeypatch.setattr(event_nor2_route, 'main', lambda: 'guarded NOR2 route')
    assert placement_route.main() == 'guarded NOR2 route'


@pytest.mark.parametrize('failure', [None, 'route', 'ready', 'drt', 'state', 'timing_state',
                                    'setup', 'hold', 'hold_count', 'setup_count', 'budget', 'antenna'])
def test_all_saved_gates_and_margin_are_required(failure):
    source = Path('checkpoint.json')
    gates = dict(source_route=ROUTE_RUN, ready_for_route_review=True, drt_launched=False,
                 state=str(source))
    timing = {'after_state': str(source), 'corners': {c: {'after': {
        **{f'timing__{k}__ws__corner:{c}': 0.07 if k == 'hold' else 0 for k in ('setup', 'hold')},
        **{f'timing__{k}_vio__count__corner:{c}': 0 for k in ('setup', 'hold')}
    }} for c in CORNERS}}
    antenna = dict(antenna__violating__nets=0, antenna__violating__pins=0)
    if failure == 'route': gates['source_route'] += 1
    if failure == 'ready': gates['ready_for_route_review'] = False
    if failure == 'drt': gates['drt_launched'] = True
    if failure == 'state': gates['state'] = 'other'
    if failure == 'timing_state': timing['after_state'] = 'other'
    if failure in ('setup', 'hold'):
        timing['corners'][CORNERS[1]]['after'][f'timing__{failure}__ws__corner:{CORNERS[1]}'] = -0.001
    if failure in ('hold_count', 'setup_count'):
        kind = failure.split('_')[0]
        timing['corners'][CORNERS[2]]['after'][f'timing__{kind}_vio__count__corner:{CORNERS[2]}'] = 1
    if failure == 'budget': timing['corners'][CORNERS[0]]['after'][f'timing__hold__ws__corner:{CORNERS[0]}'] = 0.049
    if failure == 'antenna': antenna['antenna__violating__pins'] = 1
    if failure:
        with pytest.raises(ValueError): validate_gate(gates, timing, antenna, source)
    else:
        validate_gate(gates, timing, antenna, source)


@pytest.mark.parametrize('fresh_pass', [True, False])
def test_continuation_uses_repaired_views_and_never_repeats_eco(tmp_path, monkeypatch, fresh_pass):
    import event_nor2_route as route
    from event_nor2_screen import SOURCE_RUN, VARIANT
    monkeypatch.chdir(tmp_path)
    for key, value in dict(SOURCE_VARIANT=VARIANT, SOURCE_RUN_ID=str(SOURCE_RUN),
                           REPAIRED_SOURCE_RUN_ID=str(SCREEN_RUN), PRE_ROUTE_HOLD_TARGET='source',
                           REPAIR_POSTANTENNA_HOLD='0', PDK_ROOT='/pdk').items():
        monkeypatch.setenv(key, value)

    def write(path, content):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content if isinstance(content, str) else json.dumps(content))
        return path

    original = 'sg13cmos5l_nor2_1 _27853_ (.A(_21095_), .B(_02509_), .Y(_02510_));'
    antennas = '\n'.join(f'sg13cmos5l_antennanp ant{i} (.A(_02510_));' for i in range(92))
    baseline = original + '\n' + antennas
    changed = baseline.replace('nor2_1', 'nor2_2')
    grt = Path('runs/event-nor2/grt/1-openroad-globalrouting')
    write(grt / 'tt_um_tripwire.baseline.nl.v', baseline)
    write(grt / 'tt_um_tripwire.eco.nl.v', changed)
    final_nl = write('final.nl.v', changed + '\nsg13cmos5l_antennanp extra (.A(_02510_));')
    original_nl = write('original.nl.v', original)
    write('runs/placement-route/antenna/3-openroad-checkantennas-1/state_out.json', {'nl': str(original_nl)})
    source = Path('runs/event-nor2/antenna/3-openroad-checkantennas-1/eco_state.json')
    state = {'nl': str(final_nl)}
    for key in ('odb', 'def', 'pnl', 'sdc'):
        state[key] = str(write('final.' + key, 'checkpoint'))
    write(source, state)
    antenna = dict(antenna__violating__nets=0, antenna__violating__pins=0)
    write(source.with_name('or_metrics_out.json'), antenna)
    timing = {'after_state': str(source), 'corners': {c: {'after': {
        **{f'timing__{k}__ws__corner:{c}': 0.093 if k == 'hold' else 0 for k in ('setup', 'hold')},
        **{f'timing__{k}_vio__count__corner:{c}': 0 for k in ('setup', 'hold')}
    }} for c in CORNERS}}
    write('runs/event-nor2/timing/comparison.json', timing)
    write('runs/event-nor2/gates.json', dict(source_route=ROUTE_RUN, ready_for_route_review=True,
          drt_launched=False, state=str(source), antenna_repair_requested=True))
    log = 'Final congestion report:\n' + ''.join(f'Metal{i} 100 50 50.0% 0 / 0 / 0\n' for i in range(1, 5))
    write(grt / 'openroad-globalrouting.log', log)
    write('runs/event-nor2/antenna/2-openroad-repairantennas/1-openroad-diodeinsertion/openroad-diodeinsertion.log',
          '+ repair_antennas diode\nTRIPWIRE antenna overflow audit: incremental repair completed with congestion disallowed\n' + log)
    run_json = write('run.json', dict(id=SCREEN_RUN, head_branch='main', conclusion='success',
                     path='.github/workflows/gds-event-nor2-screen.yaml'))
    identity = {'source_run_id': SOURCE_RUN}
    write('runs/event-nor2/source_identity.json', identity)
    expected_json = write('identity.json', identity)
    real_read = Path.read_text

    def read(path, *args, **kwargs):
        if str(path) == '/tmp/placement-repaired-run.json': return real_read(run_json)
        if str(path) == '/tmp/placement-source-identity.json': return real_read(expected_json)
        return real_read(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'read_text', read)
    monkeypatch.setattr(route, 'validate_identity', lambda value, *args: value)
    write('src/signoff.sdc', 'fully timed constraints')
    write('src/config_rx_screen.json', dict(CLOCK_PERIOD=20, GRT_ADJUSTMENT=0.16,
          PNR_SDC_FILE=str(Path('src/signoff.sdc').resolve())))

    def sta(config, before, output, pdk, **kwargs):
        assert before == source and kwargs['repaired'] == source
        assert kwargs['sdc'] == Path('src/signoff.sdc')
        assert __import__('os').environ['LIBRELANE_IMAGE_OVERRIDE'] == 'tripwire-hotspot:local'
        fresh = json.loads(json.dumps(timing))
        if not fresh_pass:
            fresh['corners'][CORNERS[1]]['after'][f'timing__setup__ws__corner:{CORNERS[1]}'] = -0.001
        write(output / 'comparison.json', fresh)

    monkeypatch.setattr(route, 'screen', sta)
    calls = []
    monkeypatch.setattr(route.subprocess, 'run', lambda args, **kwargs: calls.append(args))
    if fresh_pass:
        route.main()
        assert len(calls) == 1
        cfg = json.loads(Path('src/config_event_nor2_drt.json').read_text())
        assert cfg['meta']['flow'] == ['OpenROAD.DetailedRouting']
        assert calls[0][calls[0].index('--with-initial-state') + 1] == str(source)
    else:
        with pytest.raises(ValueError, match='Fresh NOR2 timing fails'):
            route.main()
        assert not calls
        assert not Path('runs/placement-route/drt').exists()
