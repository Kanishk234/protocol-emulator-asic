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


@pytest.mark.parametrize("text,util,category", [
    ("ERROR: Unable to place cell 'x', no BELs remaining to implement cell type 'FABULOUS_LC'",
     {"FABULOUS_LC": {"used": 95, "available": 88}}, "resource_capacity"),
    ("ERROR: Unable to place cell 'x', no BELs remaining to implement cell type 'FABULOUS_LC'",
     {"FABULOUS_LC": {"used": 70, "available": 88}}, "placement"),
    ("ERROR: Unable to place cell 'x'", {}, "placement"),
    ("ERROR: Failed to route net 'x'", {"FABULOUS_LC": {"used": 70, "available": 88}}, "routing"),
    ("Info: routing failed in earlier attempt\nERROR: unsupported device", {}, "unknown"),
    ("ERROR: unknown failure", {}, "unknown"),
])
def test_failure_classification_requires_observed_evidence(text, util, category):
    diagnosis = compiler.diagnose_pnr_failure(text, util)
    assert diagnosis["category"] == category
    assert all(line.startswith("ERROR:") for line in diagnosis["fatal_messages"])
    assert diagnosis["advice"]


def test_routing_failure_keeps_fatal_net_and_seed_in_diagnostic(flow, monkeypatch):
    pins, _, out, arch = flow
    def vendor(cmd, log, cwd, env=None):
        if Path(cmd[0]).name == "nextpnr-generic":
            Path(log).write_text("Info: FABULOUS_LC: 70/ 88 79%\n"
                                 "ERROR: Failed to route net 'event_count[3]'\n")
            raise compiler.CompileError("route failed")
        Path(log).write_text("synthesis stub\n")
    monkeypatch.setattr(compiler, "run", vendor)
    with pytest.raises(compiler.CompileError, match="Routing failed"):
        compiler.compile_design([], pins, arch, out, seed=17)
    failure = json.loads((out / "failure.json").read_text())
    assert failure["seed"] == 17
    assert failure["diagnosis"]["category"] == "routing"
    assert failure["diagnosis"]["fatal_messages"] == ["ERROR: Failed to route net 'event_count[3]'"]
    assert not failure["diagnosis"]["over_capacity"]
    assert not (out / "user.wbit").exists()


@pytest.mark.parametrize("arguments,expected", [
    (["--set", "COUNTER_BITS=9", "WINDOW_CLKS=256"],
     {"COUNTER_BITS": 9, "WINDOW_CLKS": 256}),
    (["--set", "COUNTER_BITS=9", "--set", "WINDOW_CLKS=256"],
     {"COUNTER_BITS": 9, "WINDOW_CLKS": 256}),
    (["--set", "COUNTER_BITS=4", "--set", "COUNTER_BITS=9"],
     {"COUNTER_BITS": 9}),
])
def test_cli_parameter_groups_preserve_every_override(monkeypatch, arguments, expected):
    captured = {}
    def compile_stub(*args, **kwargs):
        captured.update(kwargs["set_params"])
        return Path("unused.wbit"), {
            "words": 1, "crc32": "test", "arch_version": "test",
            "fmax_mhz": None, "timing_corner": "test", "utilisation": {},
            "unmapped_inputs_tied_0": [], "unmapped_outputs_open": [],
        }
    monkeypatch.setattr(compiler, "compile_design", compile_stub)
    assert compiler.main(["user.v", "--pins", "pins.yaml", "-o", "unused",
                          *arguments]) == 0
    assert captured == expected


@pytest.mark.parametrize("value,expected", [
    ("face", "face"), ("dead", "dead"), ("FALSE", "FALSE"),
    ("8'hff", "8'hff"), ("'0", "'0"), ("1.5", "1.5"),
    ("8+1", "8+1"), ("1<<4", "1<<4"), ("8/2", "8/2"),
    ("42", 42), ("08", 8), ("-12", -12), ("+12", 12),
    ("1_024", 1024), ("0xFa_ce", 0xFACE), ("-0x10", -16),
    ("+0b10", 2), ("0o17", 15), ("-0o10", -8),
])
def test_cli_preserves_strings_and_parses_integer_formats(monkeypatch, value, expected):
    captured = {}
    def compile_stub(*args, **kwargs):
        captured.update(kwargs["set_params"])
        raise compiler.CompileError("stop after parameter capture")
    monkeypatch.setattr(compiler, "compile_design", compile_stub)
    assert compiler.main(["user.v", "--pins", "pins.yaml", "-o", "unused",
                          "--set", "VALUE=" + value]) == 1
    assert captured == {"VALUE": expected}


@pytest.mark.parametrize("value", ["0b2", "0o8", "0xGG", "0x", "12oops", "1__2"])
def test_cli_malformed_integer_is_actionable_before_compile(monkeypatch, capsys, value):
    def unexpected_compile(*args, **kwargs):
        pytest.fail("malformed parameter reached compilation")
    monkeypatch.setattr(compiler, "compile_design", unexpected_compile)
    assert compiler.main(["user.v", "--pins", "pins.yaml", "-o", "unused",
                          "--set", "VALUE=" + value]) == 1
    error = capsys.readouterr().err
    assert "compile: error:" in error
    assert "invalid integer literal" in error
    assert "VALUE=" + value in error
    assert "Traceback" not in error
