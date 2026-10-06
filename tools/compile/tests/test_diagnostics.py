"""Compiler boundary checks with only vendor executions replaced."""
import json
from pathlib import Path

import pytest
import yaml

from compile import compile as compiler


@pytest.fixture
def flow(tmp_path, monkeypatch):
    pins = tmp_path / "pins.yaml"
    spec = {"top": "user", "pins": {"clk": "clk", "rx_i": "FAB_IN0", "tx_o": "FAB_OUT0"}}
    pins.write_text(yaml.safe_dump(spec))
    monkeypatch.setenv("WARP_TILES", str(tmp_path / "tiles"))
    monkeypatch.setattr(compiler, "user_ports", lambda *a, **k: {
        "clk": ("input", 1), "rx_i": ("input", 1), "tx_o": ("output", 1)})
    monkeypatch.setattr(compiler, "tool", lambda name: name)
    monkeypatch.setattr(compiler, "tool_versions", lambda: {"vendor": "test stub"})
    monkeypatch.setattr(compiler, "fingerprint_inputs", lambda paths: [])
    out = tmp_path / "build"
    arch = compiler.ROOT / "arch/warp_g1"
    return pins, spec, out, arch


@pytest.mark.parametrize("missing,label", [("rx_i", "inputs tied to zero"),
                                           ("tx_o", "outputs left open")])
def test_strict_ports_reject_before_vendor_synthesis(flow, monkeypatch, missing, label):
    pins, spec, out, arch = flow
    del spec["pins"][missing]
    pins.write_text(yaml.safe_dump(spec))
    def unexpected_vendor(*args, **kwargs):
        pytest.fail("vendor synthesis ran despite an unmapped port")
    monkeypatch.setattr(compiler, "run", unexpected_vendor)
    with pytest.raises(compiler.CompileError, match=f"{label}: {missing}"):
        compiler.compile_design([], pins, arch, out, strict_ports=True)
    assert not (out / "synth.ys").exists()


@pytest.mark.parametrize("used,advice", [(95, "Resource capacity exceeded"),
                                         (70, "shared reset/enable groups")])
def test_failed_rebuild_has_current_diagnostic_not_stale_success(flow, monkeypatch, used, advice):
    pins, spec, out, arch = flow
    # Default omitted-input behavior must still reach placement/routing.
    del spec["pins"]["rx_i"]
    pins.write_text(yaml.safe_dump(spec))
    out.mkdir()
    (out / "report.json").write_text('{"old_success": true}')
    (out / "failure.json").write_text('{"old_failure": true}')
    (out / "user.wbit").write_bytes(b"previous loadable image")
    (out / "other.wbit").write_bytes(b"separate design")

    def vendor(cmd, log, cwd, env=None):
        if Path(cmd[0]).name == "nextpnr-generic":
            Path(log).write_text(f"Info: FABULOUS_LC: {used}/ 88 100%\nERROR: placement failed\n")
            raise compiler.CompileError("placement failed")
        Path(log).write_text("synthesis stub\n")

    monkeypatch.setattr(compiler, "run", vendor)
    with pytest.raises(compiler.CompileError, match=advice):
        compiler.compile_design([], pins, arch, out)
    assert not (out / "report.json").exists()
    assert not (out / "user.wbit").exists()
    assert (out / "other.wbit").read_bytes() == b"separate design"
    failure = json.loads((out / "failure.json").read_text())
    assert failure["design"] == "user"
    assert failure["stage"] == "place_route"
    assert failure["utilisation"]["FABULOUS_LC"] == {"used": used, "available": 88}
    assert "old_failure" not in failure


def test_missing_placer_keeps_the_original_tool_error(flow, monkeypatch):
    pins, _, out, arch = flow
    monkeypatch.setattr(compiler, "run", lambda *a, **k: None)
    def missing_tool(name):
        if name == "nextpnr-generic":
            raise compiler.CompileError("nextpnr installation missing")
        return name
    monkeypatch.setattr(compiler, "tool", missing_tool)
    with pytest.raises(compiler.CompileError, match="nextpnr installation missing"):
        compiler.compile_design([], pins, arch, out)
    assert not (out / "failure.json").exists()
