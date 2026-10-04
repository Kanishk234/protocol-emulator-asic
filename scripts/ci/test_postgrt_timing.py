"""Regressions for route-free execution and fresh per-corner evidence."""
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

spec = importlib.util.spec_from_file_location("postgrt_timing", Path(__file__).with_name("postgrt_timing.py"))
timing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(timing)


@pytest.mark.parametrize("reuse_repair", [True, False])
@pytest.mark.parametrize("explicit_sdc", [False, True])
def test_matched_corner_processes_and_saved_repair(tmp_path, reuse_repair, explicit_sdc):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"CLOCK_PERIOD": 20, "GRT_ADJUSTMENT": 0.3,
                                  "DIE_AREA": "0 0 1289.28 710.64"}))
    before = tmp_path / "before.json"
    repaired = (tmp_path / "repaired.json" if reuse_repair else
                tmp_path / "result/repair/01-openroad-resizertimingpostgrt/state_out.json")
    calls = []

    def fake_run(command, check):
        cfg = json.loads(Path(command[-1]).read_text())
        assert cfg["meta"]["version"] == 1
        assert cfg["DIE_AREA"] == "0 0 1289.28 710.64"
        if explicit_sdc:
            assert cfg["PNR_SDC_FILE"] == str((tmp_path / "signoff.sdc").resolve())
            assert cfg["GRT_RESIZER_SETUP_SLACK_MARGIN"] == 0
        step = cfg["meta"]["flow"]
        assert step in (["OpenROAD.STAMidPNR"], ["OpenROAD.ResizerTimingPostGRT"])
        assert len(cfg["PNR_CORNERS"]) == 1
        checkpoint = command[command.index("--with-initial-state") + 1]
        root = Path(command[command.index("--force-run-dir") + 1])
        assert checkpoint == str(before if root.name.startswith("before-") or root.name == "repair" else repaired)
        calls.append((root.name, checkpoint))
        assert root.is_dir(), "LibreLane requires --force-run-dir to exist"
        resolved = dict(cfg)
        if step == ["OpenROAD.STAMidPNR"]:
            # Pinned one-step STA discards config variables unused by the step.
            resolved.pop("GRT_ADJUSTMENT")
        (root / "resolved.json").write_text(json.dumps(resolved))
        stage = root / ("01-openroad-resizertimingpostgrt" if root.name == "repair" else "01-openroad-stamidpnr")
        stage.mkdir()
        if root.name == "repair":
            (stage / "state_out.json").write_text("{}")
        corner = cfg["PNR_CORNERS"][0]
        metrics = {f"timing__{kind}__{field}__corner:{corner}": 1
                   for kind in ("setup", "hold") for field in ("ws", "wns", "tns")}
        (stage / "or_metrics_out.json").write_text(json.dumps(metrics))

    with patch.object(timing.subprocess, "run", side_effect=fake_run):
        timing.screen(config, before, tmp_path / "result", "/pdk", repaired if reuse_repair else None,
                      tmp_path / "signoff.sdc" if explicit_sdc else None, 0 if explicit_sdc else None)
    assert len(calls) == (6 if reuse_repair else 7)
    result = json.loads((tmp_path / "result/comparison.json").read_text())
    assert set(result["corners"]) == set(timing.CORNERS)


def test_inherited_metrics_cannot_replace_missing_fresh_corner(tmp_path):
    stage = tmp_path / "01-openroad-stamidpnr"
    stage.mkdir()
    (stage / "or_metrics_out.json").write_text("{}")
    (stage / "state_out.json").write_text(json.dumps({"metrics": {
        f"timing__setup__ws__corner:{timing.CORNERS[1]}": 5}}))
    with pytest.raises(ValueError, match="Missing fresh metric"):
        timing.fresh_metrics(tmp_path, "openroad-stamidpnr", timing.CORNERS[1])
