import json
from pathlib import Path

import pytest

import hotspot_screen


def prepare(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PDK_ROOT", "/pdk")
    def write(path, data):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
    write("src/config_merged.json", {"CLOCK_PERIOD": 20, "PL_TARGET_DENSITY_PCT": 56})
    source = "runs/repaired-route/antenna/3-openroad-checkantennas-1/state_out.json"
    Path("checkpoint").write_text("saved")
    write(source, {key: "checkpoint" for key in ("odb", "def", "nl", "pnl", "sdc")})
    write("runs/repaired-route/postantenna-sta/comparison.json", {
        "after_state": source,
        "corners": {"slow": {"after": {"timing__setup__ws__corner:slow": 0,
                                       "timing__hold__ws__corner:slow": 0.1}}}})
    return write


def test_screen_compares_same_checkpoint_without_drt(monkeypatch, tmp_path):
    write = prepare(monkeypatch, tmp_path)
    calls = []
    def run(args, check):
        cfg = json.loads(Path(args[-1]).read_text())
        assert cfg["meta"]["flow"] == ["OpenROAD.GlobalRouting", "OpenROAD.CheckAntennas"]
        assert cfg["GRT_ADJUSTMENT"] == 0.16
        calls.append((args[args.index("--with-initial-state") + 1],
                      hotspot_screen.os.environ.get("LIBRELANE_IMAGE_OVERRIDE")))
        output = Path(args[args.index("--force-run-dir") + 1])
        write(output / "1-openroad-globalrouting/or_metrics_out.json", {})
        write(output / "1-openroad-globalrouting/config.json", cfg)
        (output / "1-openroad-globalrouting/openroad-globalrouting.log").write_text("TRIPWIRE hotspot screen:")
        write(output / "2-openroad-checkantennas/state_out.json", {})
        write(output / "2-openroad-checkantennas/or_metrics_out.json", {})
    monkeypatch.setattr(hotspot_screen.subprocess, "run", run)
    screens = []
    monkeypatch.setattr(hotspot_screen, "screen", lambda *a, **kw: screens.append((a, kw)))
    hotspot_screen.main()
    assert calls[0][0] == calls[1][0]
    assert [c[1] for c in calls] == [None, "tripwire-hotspot:local"]
    assert screens[0][0][1] == Path("runs/hotspot-screen/baseline/2-openroad-checkantennas/state_out.json")
    assert screens[0][1]["repaired"] == Path("runs/hotspot-screen/region/2-openroad-checkantennas/state_out.json")


def test_bad_source_timing_blocks_routing(monkeypatch, tmp_path):
    write = prepare(monkeypatch, tmp_path)
    p = Path("runs/repaired-route/postantenna-sta/comparison.json")
    data = json.loads(p.read_text())
    data["corners"]["slow"]["after"]["timing__setup__ws__corner:slow"] = -1
    write(p, data)
    monkeypatch.setattr(hotspot_screen.subprocess, "run", lambda *a, **kw: pytest.fail("Routing started"))
    with pytest.raises(ValueError, match="Source failed"):
        hotspot_screen.main()
