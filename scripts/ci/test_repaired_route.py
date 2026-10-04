"""Ensure the continuation routes only the post-antenna state after fresh STA."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import repaired_route


@pytest.mark.parametrize("negative_slack", [False, True])
def test_postantenna_timing_gate(tmp_path, monkeypatch, negative_slack):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PDK_ROOT", "/pdk")

    def write(path, data):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))

    write("src/config_merged.json", {"CLOCK_PERIOD": 20, "PL_TARGET_DENSITY_PCT": 56})
    write("runs/wokwi/39-openroad-globalrouting/config.json", {"GRT_ADJUSTMENT": 0.16})
    root = Path("runs/postgrt-timing/repair/1-openroad-resizertimingpostgrt")
    write(root / "config.json", {"GRT_ADJUSTMENT": 0.16, "GRT_RESIZER_SETUP_SLACK_MARGIN": 0,
          "RSZ_CORNERS": ["nom_slow_1p08V_125C"], "PNR_SDC_FILE": str(tmp_path / "src/signoff.sdc")})
    state = {}
    for key in ("odb", "def", "sdc", "pnl", "nl"):
        path = root / key
        write(path, {})
        state[key] = str(path)
    write(root / "state_out.json", state)
    metrics = {f"timing__{kind}__ws__corner:slow": 0 for kind in ("setup", "hold")}
    write("runs/postgrt-timing/comparison.json", {"corners": {"slow": {"after": metrics}}})
    calls = []

    def run(command, check):
        cfg = json.loads(Path(command[-1]).read_text())
        calls.append(cfg["meta"]["flow"])
        out = Path(command[command.index("--force-run-dir") + 1])
        assert out.is_dir()
        if len(calls) == 1:
            write(out / "3-openroad-checkantennas-1/state_out.json", state)
        else:
            assert command[command.index("--with-initial-state") + 1].endswith("3-openroad-checkantennas-1/state_out.json")

    def sta(config, before, output, pdk, repaired, sdc):
        assert repaired != before
        assert sdc == Path("src/signoff.sdc")
        after = dict(metrics)
        after["timing__setup__ws__corner:slow"] = -1 if negative_slack else 0
        write(output / "comparison.json", {"corners": {"slow": {"after": after}}})

    with patch.object(repaired_route.subprocess, "run", side_effect=run), patch.object(repaired_route, "screen", side_effect=sta):
        if negative_slack:
            with pytest.raises(ValueError, match="DRT not launched"):
                repaired_route.main()
        else:
            repaired_route.main()
    assert len(calls) == (1 if negative_slack else 2)
    if not negative_slack:
        assert calls[-1] == ["OpenROAD.DetailedRouting"]
