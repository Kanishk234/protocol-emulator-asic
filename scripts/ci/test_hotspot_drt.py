import json
from pathlib import Path

import pytest

from hotspot_drt import validate
from postgrt_timing import CORNERS


def prepare(monkeypatch, tmp_path, root_name="hotspot-repair"):
    monkeypatch.chdir(tmp_path)
    root = Path("runs") / root_name
    state = root / "antenna/3-openroad-checkantennas-1/state_out.json"
    def write(p, data):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data))
    Path("checkpoint").write_text("saved")
    write(state, {key: "checkpoint" for key in ("odb", "def", "nl", "pnl", "sdc")})
    write(root / "gates.json", {"state": str(state), "disable_mirroring": True,
                               "estimated_timing_and_antenna_pass": True})
    write(root / "timing/repair/1-openroad-resizertimingpostgrt/config.json", {
        "PL_OPTIMIZE_MIRRORING": False, "GRT_ADJUSTMENT": 0.16, "OPENROAD_THREADS": 4,
        "GRT_RESIZER_SETUP_SLACK_MARGIN": 0, "PNR_SDC_FILE": str(Path("src/signoff.sdc").resolve())})
    write(root / "postantenna-sta/comparison.json", {"after_state": str(state), "corners": {
        corner: {"after": {key: value for kind in ("setup", "hold") for key, value in (
            (f"timing__{kind}__ws__corner:{corner}", 0.0),
            (f"timing__{kind}_vio__count__corner:{corner}", 0))}} for corner in CORNERS}})
    write(state.with_name("or_metrics_out.json"), {"antenna__violating__nets": 0,
                                                  "antenna__violating__pins": 0})
    return root, state, write


@pytest.mark.parametrize("root_name", ["hotspot-repair", "branch-followup"])
def test_valid_saved_state(monkeypatch, tmp_path, root_name):
    root, state, _ = prepare(monkeypatch, tmp_path, root_name)
    assert validate(root) == state


@pytest.mark.parametrize("failure", ["negative_timing", "dirty_antenna", "missing_odb"])
def test_invalid_state_is_refused(monkeypatch, tmp_path, failure):
    root, state, write = prepare(monkeypatch, tmp_path)
    if failure == "negative_timing":
        p = root / "postantenna-sta/comparison.json"
        d = json.loads(p.read_text())
        d["corners"][CORNERS[1]]["after"][f"timing__setup__ws__corner:{CORNERS[1]}"] = -0.1
        write(p, d)
    elif failure == "dirty_antenna":
        write(state.with_name("or_metrics_out.json"), {"antenna__violating__nets": 1,
                                                       "antenna__violating__pins": 1})
    else:
        Path("checkpoint").unlink()
    with pytest.raises(ValueError):
        validate(root)
