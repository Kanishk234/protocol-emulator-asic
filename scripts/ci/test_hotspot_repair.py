import json
from pathlib import Path

from hotspot_repair import repair_config


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
