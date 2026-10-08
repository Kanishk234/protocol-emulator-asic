import copy
import pytest
from placement_route import timing_pass
from postgrt_timing import CORNERS


def fixture():
    return {"corners": {c: {"after": {
        **{f"timing__{k}__ws__corner:{c}": 0.01 for k in ("setup", "hold")},
        **{f"timing__{k}_vio__count__corner:{c}": 0 for k in ("setup", "hold")}
    }} for c in CORNERS}}


@pytest.mark.parametrize("corner", CORNERS)
@pytest.mark.parametrize("kind", ["setup", "hold"])
@pytest.mark.parametrize("failure", ["negative", "count", "missing"])
def test_every_corner_and_violation_count_required(corner, kind, failure):
    data = fixture()
    assert timing_pass(data)
    metrics = data["corners"][corner]["after"]
    if failure == "negative":
        metrics[f"timing__{kind}__ws__corner:{corner}"] = -0.001
    elif failure == "count":
        metrics[f"timing__{kind}_vio__count__corner:{corner}"] = 1
    else:
        del metrics[f"timing__{kind}__ws__corner:{corner}"]
        with pytest.raises(KeyError):
            timing_pass(data)
        return
    assert not timing_pass(data)


@pytest.mark.parametrize("passes", [True, False])
def test_bounded_followup_checks_fresh_result_without_retry(tmp_path, monkeypatch, passes):
    import json
    from pathlib import Path
    import placement_route
    calls = []
    data = fixture()
    data['after_state'] = str(tmp_path / 'repaired-state.json')
    if not passes:
        corner = CORNERS[0]
        data['corners'][corner]['after'][f'timing__hold__ws__corner:{corner}'] = -0.001
    def fake_screen(config, state, output, pdk_root, **kwargs):
        calls.append(kwargs)
        (output / 'comparison.json').write_text(json.dumps(data))
    monkeypatch.setattr(placement_route, 'screen', fake_screen)
    if passes:
        assert placement_route.hold_followup('config', 'state', tmp_path, 'pdk') == Path(data['after_state'])
    else:
        with pytest.raises(ValueError, match='routing refused'):
            placement_route.hold_followup('config', 'state', tmp_path, 'pdk')
    assert calls == [{'sdc': Path('src/signoff.sdc'), 'repair_corners': CORNERS}]


@pytest.mark.parametrize('failure', [None, 'repair', 'antenna', 'fresh-timing'])
def test_postantenna_recovery_is_single_pass_and_rechecks_both_gates(tmp_path, monkeypatch, failure):
    import json
    from pathlib import Path
    import placement_route
    calls = []
    def repair(*args):
        calls.append('repair')
        if failure == 'repair':
            raise ValueError('repair fails')
        return Path('repaired-state')
    def antenna(state):
        assert state == Path('repaired-state')
        calls.append('antenna')
        if failure == 'antenna':
            raise ValueError('dirty antenna')
        return Path('antenna-checked-state')
    def fresh(config, before, output, pdk, **kwargs):
        assert before == Path('repaired-state')
        assert kwargs == {'repaired': Path('antenna-checked-state'), 'sdc': Path('src/signoff.sdc')}
        calls.append('fresh-timing')
        output.mkdir()
        data = fixture()
        if failure == 'fresh-timing':
            data['corners'][CORNERS[0]]['after'][f'timing__hold__ws__corner:{CORNERS[0]}'] = -0.001
        (output / 'comparison.json').write_text(json.dumps(data))
    monkeypatch.setattr(placement_route, 'hold_followup', repair)
    monkeypatch.setattr(placement_route, 'screen', fresh)
    if failure:
        with pytest.raises(ValueError):
            placement_route.postantenna_followup('config', 'state', tmp_path, 'pdk', antenna)
    else:
        assert placement_route.postantenna_followup('config', 'state', tmp_path, 'pdk', antenna) == Path('antenna-checked-state')
    assert calls.count('repair') == 1
    assert calls == ['repair', 'antenna', 'fresh-timing'][:{'repair': 1, 'antenna': 2}.get(failure, 3)]


@pytest.mark.parametrize('kind', ['hold', 'setup'])
@pytest.mark.parametrize('corner', CORNERS)
def test_postantenna_recovery_only_accepts_hold_only_failures(kind, corner):
    from placement_route import hold_only_failure
    data = fixture()
    assert not hold_only_failure(data)
    data['corners'][corner]['after'][f'timing__{kind}__ws__corner:{corner}'] = -0.001
    assert hold_only_failure(data) == (kind == 'hold')


@pytest.mark.parametrize('hold_margin', [0.10, 0.125, 0.15])
@pytest.mark.parametrize('failure', [None, 'headroom', 'setup', 'hold-count'])
def test_headroom_requires_fresh_all_corner_pass_and_fast_budget(tmp_path, monkeypatch, failure, hold_margin):
    import json
    from pathlib import Path
    import placement_route
    data = fixture()
    data['after_state'] = 'measured-state'
    fast = data['corners'][CORNERS[0]]['after']
    fast[f'timing__hold__ws__corner:{CORNERS[0]}'] = 0.08
    if failure == 'headroom':
        fast[f'timing__hold__ws__corner:{CORNERS[0]}'] = 0.049
    elif failure == 'setup':
        c = CORNERS[1]
        data['corners'][c]['after'][f'timing__setup__ws__corner:{c}'] = -0.001
    elif failure == 'hold-count':
        fast[f'timing__hold_vio__count__corner:{CORNERS[0]}'] = 1
    calls = []
    def fake(*args, **kwargs):
        calls.append(kwargs)
        (tmp_path / 'comparison.json').write_text(json.dumps(data))
    monkeypatch.setattr(placement_route, 'screen', fake)
    if failure:
        with pytest.raises(ValueError, match='routing refused'):
            placement_route.hold_headroom('config', 'state', tmp_path, 'pdk', hold_margin=hold_margin)
    else:
        assert placement_route.hold_headroom('config', 'state', tmp_path, 'pdk', hold_margin=hold_margin) == Path('measured-state')
    assert calls == [{'sdc': Path('src/signoff.sdc'), 'setup_margin': 0.0,
                      'repair_corners': CORNERS, 'hold_margin': hold_margin}]


@pytest.mark.parametrize('variant', ['bs-event-late', 'bs-event-rx-shared', 'bs-event-pin-banked', 'bs-event-rx-timer', 'placement', 'bs-event-drop-qual'])
@pytest.mark.parametrize('target', ['source', '0.10', '0.125', '0.15', '0.12'])
def test_only_reviewed_source_target_pairs_allow_headroom(variant, target):
    from placement_route import selected_hold_margin
    if target == 'source':
        assert selected_hold_margin(variant, target) is None
    elif target in {'0.10', '0.125', '0.15'} and (variant == 'bs-event-late' or (variant == 'bs-event-rx-shared' and target == '0.125')):
        assert selected_hold_margin(variant, target) == float(target)
    else:
        with pytest.raises(ValueError):
            selected_hold_margin(variant, target)
