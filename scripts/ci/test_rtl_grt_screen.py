import json
from pathlib import Path

import pytest

from rtl_grt_screen import checkpoint, timing_placement, repair_margin


def test_every_workflow_experiment_is_registered_in_patch_and_runner():
    import yaml
    from timing_trial import PATCHES

    path = Path(__file__).resolve().parents[2] / '.github/workflows/gds-drop-counter-screen.yaml'
    workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
    inputs = workflow['on']['workflow_dispatch']['inputs']
    for variant in inputs['experiment']['options']:
        assert variant in PATCHES or variant == 'setup-margin'
        assert timing_placement(variant)
        assert repair_margin(variant) == (2.0 if variant == 'setup-margin' else 0.0)
    for variant in inputs['comparison_baseline']['options']:
        assert timing_placement(variant)


@pytest.mark.parametrize("failure", [None, "missing_odb", "drt", "second_grt"])
def test_screen_requires_unique_complete_preroute_state(tmp_path, failure):
    source = tmp_path / "35-openroad-globalrouting/state_out.json"
    source.parent.mkdir()
    data = tmp_path / "saved"
    data.write_text("fixture")
    state = {key: str(data) for key in ("odb", "def", "nl", "pnl", "sdc")}
    if failure == "missing_odb":
        state["odb"] = str(tmp_path / "absent")
    source.write_text(json.dumps(state))
    if failure == "drt":
        (tmp_path / "44-openroad-detailedrouting").mkdir()
    if failure == "second_grt":
        other = tmp_path / "36-openroad-globalrouting/state_out.json"
        other.parent.mkdir()
        other.write_text(json.dumps(state))
    if failure:
        with pytest.raises(ValueError):
            checkpoint(tmp_path)
    else:
        assert checkpoint(tmp_path) == source


def test_placement_override_is_isolated_and_unknown_variants_refused():
    assert timing_placement("timing-placement") is True
    assert timing_placement("cts-cluster8") is True
    assert timing_placement("drop-counter") is True
    for variant in ("baseline", "rx-factor", "pad-mux", "load-select", "input-decode", "cached-input"):
        assert timing_placement(variant) is False
    with pytest.raises(ValueError):
        timing_placement("unknown")


@pytest.mark.parametrize("variant", ["drop-qual", "bs-resync", "bs-csa", "bs-event-late", "bs-event-drop-qual", "bs-event-rx-timer", "bs-event-rx-shared", "bs-event-pin-banked", "bs-load-flat", "setup-margin"])
def test_new_trials_keep_timing_placement_and_only_margin_trial_adds_headroom(variant):
    assert timing_placement(variant)
    assert repair_margin(variant) == (2.0 if variant == "setup-margin" else 0.0)
    assert repair_margin("timing-placement") == 0
    with pytest.raises(ValueError):
        repair_margin("unknown")
