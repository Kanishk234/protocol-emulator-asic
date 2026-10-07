from pathlib import Path
import pytest
import timing_trial


@pytest.mark.parametrize("failure", ["wrong-head", "dirty", "wrong-file", "unknown"])
def test_trial_refuses_untrusted_source_or_unexpected_mutation(monkeypatch, failure):
    replies = [timing_trial.CANDIDATE, "", "src/trw_chan_port.v"]
    if failure == "wrong-head":
        replies[0] = "wrong"
    elif failure == "dirty":
        replies[1] = "src/trw_pin_bs.v"
    elif failure == "wrong-file":
        replies[2] = "src/trw_chan_port.v\nsrc/config.json"
    mutations = []
    monkeypatch.setattr(timing_trial.subprocess, "check_output", lambda *a, **k: replies.pop(0))
    monkeypatch.setattr(timing_trial.subprocess, "run", lambda cmd, **k: mutations.append(cmd))
    with pytest.raises(ValueError):
        timing_trial.apply_trial("unknown" if failure == "unknown" else "drop-qual")
    assert len(mutations) == (1 if failure == "wrong-file" else 0)


@pytest.mark.parametrize("variant", ["timing-placement", "setup-margin", *timing_trial.PATCHES])
def test_trial_only_applies_selected_patch(monkeypatch, variant):
    expected = timing_trial.PATCHES.get(variant)
    sources = expected[1] if expected else ""
    changed = sources if isinstance(sources, str) else "\n".join(sources)
    replies = [timing_trial.CANDIDATE, "", changed]
    mutations = []
    monkeypatch.setattr(timing_trial.subprocess, "check_output", lambda *a, **k: replies.pop(0))
    monkeypatch.setattr(timing_trial.subprocess, "run", lambda cmd, **k: mutations.append(cmd))
    timing_trial.apply_trial(variant)
    assert mutations == ([["git", "apply", str(Path("workflow-src/spikes/r4_floorplan") / expected[0])]] if expected else [])

@pytest.mark.parametrize("changed", ["src/trw_pin_bs.v", "src/trw_chan_port.v", "src/trw_pin_bs.v\nsrc/trw_chan_port.v\nsrc/config.json"])
def test_combination_requires_both_exact_modules(monkeypatch, changed):
    replies = [timing_trial.CANDIDATE, "", changed]
    monkeypatch.setattr(timing_trial.subprocess, "check_output", lambda *a, **k: replies.pop(0))
    monkeypatch.setattr(timing_trial.subprocess, "run", lambda *a, **k: None)
    with pytest.raises(ValueError, match="unexpected files"):
        timing_trial.apply_trial("bs-event-drop-qual")
