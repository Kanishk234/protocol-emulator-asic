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
