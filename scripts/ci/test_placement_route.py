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
