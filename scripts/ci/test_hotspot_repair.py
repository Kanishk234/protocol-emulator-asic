import json
from pathlib import Path
import pytest

from hotspot_repair import repair_config, followup_source, main


def test_disable_mirroring_changes_only_disposable_config(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    source = Path("src/config_merged.json")
    original = {"CLOCK_PERIOD": 20, "PL_TARGET_DENSITY_PCT": 56, "PL_OPTIMIZE_MIRRORING": True}
    source.write_text(json.dumps(original))
    trial = repair_config(True)
    assert trial != source
    assert json.loads(source.read_text()) == original
    assert json.loads(trial.read_text()) == dict(original, PL_OPTIMIZE_MIRRORING=False)
    assert repair_config(False) == source


@pytest.mark.parametrize("bad", [None, "state", "critical_branch", "disable_mirroring", "antenna"])
def test_followup_requires_audited_clean_branch(tmp_path, bad):
    state = tmp_path / "antenna/3-openroad-checkantennas-1/state_out.json"
    state.parent.mkdir(parents=True)
    gates = {"state": str(state), "critical_branch": True, "disable_mirroring": True,
             "estimated_timing_and_antenna_pass": False}
    antenna = {"antenna__violating__nets": 0, "antenna__violating__pins": 0}
    if bad == "state":
        gates["state"] = "wrong"
    elif bad == "antenna":
        antenna["antenna__violating__pins"] = 1
    elif bad:
        gates[bad] = False
    (tmp_path / "gates.json").write_text(json.dumps(gates))
    state.with_name("or_metrics_out.json").write_text(json.dumps(antenna))
    if bad:
        with pytest.raises(ValueError):
            followup_source(tmp_path)
    else:
        assert followup_source(tmp_path) == state


@pytest.mark.parametrize("mirroring,branch", [(False, False), (True, True)])
def test_followup_refuses_reinsertion_or_mirroring(mirroring, branch):
    with pytest.raises(ValueError):
        main(disable_mirroring=mirroring, critical_branch=branch, postantenna=True)
