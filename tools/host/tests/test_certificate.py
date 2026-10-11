import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from compile.bitfile import BitFile
from host.certificate import certificate, operating_summary
from host.protocol import SYNC_WORD


@pytest.fixture
def evidence(tmp_path):
    architecture = tmp_path / "arch.yaml"
    architecture.write_text("name: warp_g1\narch_version: 3\nluts: 88\nprimitives:\n  wp_timer: 2\n  wp_shift: 2\n")
    source = tmp_path / "user.v"
    source.write_text("module user; endmodule\n")
    image = tmp_path / "user.wbit"
    bitfile = BitFile(3, [SYNC_WORD, 1 << 20])
    bitfile.save(image)
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    report = {"design": "user", "arch": "warp_g1", "arch_version": "0x0003",
        "params": {"DIV": 16}, "tools": {"yosys": "test-fixture version"},
        "build_options": {"seed": 1, "min_ctrl": 4, "strict_ports": True},
        "words": 2, "crc32": f"0x{bitfile.crc:08X}", "fmax_mhz": 60.0,
        "meets_50mhz": True, "timing_corner": "nom_slow_1p08V_125C",
        "utilisation": {"FABULOUS_LC": {"used": 80, "available": 88},
            "wp_timer": {"used": 2, "available": 2}, "wp_shift": {"used": 1, "available": 2}},
        "pins": {"FAB_IN0": {"i": "event_i"}}, "unmapped_inputs_tied_0": [],
        "unmapped_outputs_open": [],
        "provenance": {"inputs": [{"path": str(path), "sha256": digest(path)}
            for path in (source, architecture)], "bitfile": str(image), "bitfile_sha256": digest(image)}}
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report))
    budget = {"clock_hz": 50000000, "sck_hz": 1000000, "arrival_bytes_s": 1000}
    return report_path, architecture, report, budget, source


def test_certificate_keeps_estimates_separate_and_hashes_exact_input(evidence):
    report_path, architecture, _, budget, _ = evidence
    result = certificate(report_path, architecture, budget)
    assert result["compile_report_sha256"] == hashlib.sha256(report_path.read_bytes()).hexdigest()
    assert result["compiler_estimate"]["requested_clock_within_estimate"] is True
    assert result["host_budget"]["queue_sufficient_under_model"] is True
    assert result["physical_timing_verified"] is False
    assert result["board_rate_measured"] is False


def test_unknown_and_insufficient_model_timing_are_preserved(evidence):
    report_path, architecture, report, budget, _ = evidence
    report.update(fmax_mhz=None, meets_50mhz=False)
    report_path.write_text(json.dumps(report))
    assert certificate(report_path, architecture, budget)["compiler_estimate"]["requested_clock_within_estimate"] is None
    report.update(fmax_mhz=40, meets_50mhz=False)
    report_path.write_text(json.dumps(report))
    assert certificate(report_path, architecture, budget)["compiler_estimate"]["requested_clock_within_estimate"] is False


@pytest.mark.parametrize("field,value,message", [
    ("arch", "another", "name"), ("arch_version", "0x0004", "disagrees"),
    ("fmax_mhz", float("nan"), "finite"), ("fmax_mhz", True, "finite"),
    ("meets_50mhz", False, "contradicts"),
])
def test_contradictory_metadata_rejected(evidence, field, value, message):
    report_path, architecture, report, budget, _ = evidence
    report[field] = value
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match=message):
        certificate(report_path, architecture, budget)


@pytest.mark.parametrize("used,available,message", [(89, 88, "over capacity"), (80, 90, "capacity disagrees"), (True, 88, "integer")])
def test_resource_contradictions_rejected(evidence, used, available, message):
    report_path, architecture, report, budget, _ = evidence
    report["utilisation"]["FABULOUS_LC"] = {"used": used, "available": available}
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match=message):
        certificate(report_path, architecture, budget)


def test_changed_sources_and_unlisted_architecture_rejected(evidence):
    report_path, architecture, report, budget, source = evidence
    report["provenance"]["inputs"] = report["provenance"]["inputs"][:1]
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="hashed compiler input"):
        certificate(report_path, architecture, budget)
    source.write_text("changed")
    with pytest.raises(ValueError, match="audit failed"):
        certificate(report_path, architecture, budget)


def test_host_failure_does_not_disappear_and_fictitious_queue_is_rejected(evidence):
    report_path, architecture, _, budget, _ = evidence
    budget["arrival_bytes_s"] = 1000000
    result = certificate(report_path, architecture, budget)
    assert result["host_budget"]["strict_service_margin"] is False
    assert result["host_budget"]["queue_sufficient_under_model"] is False
    budget["queue_bytes"] = 16
    with pytest.raises(ValueError, match="only two"):
        certificate(report_path, architecture, budget)


def test_missing_or_extra_budget_arguments_rejected(evidence):
    report_path, architecture, _, budget, _ = evidence
    budget["invented"] = 1
    with pytest.raises(ValueError, match="arguments"):
        certificate(report_path, architecture, budget)


def test_cli_writes_scoped_artifact_from_audited_compile_inputs(evidence, tmp_path):
    report_path, architecture, _, budget, _ = evidence
    budget_path = tmp_path / "budget.json"
    budget_path.write_text(json.dumps(budget))
    env = os.environ | {"PYTHONPATH": str(Path(__file__).resolve().parents[2])}
    command = [sys.executable, "-m", "host.certificate", str(report_path),
               str(architecture), str(budget_path)]
    run = subprocess.run(command, env=env, text=True, capture_output=True)
    assert run.returncode == 0, run.stderr
    result = json.loads(run.stdout)
    assert result["schema"] == "warp_planning_certificate_v1"
    assert result["physical_timing_verified"] is False
    assert result["board_rate_measured"] is False
    assert result["resources"]["wp_timer"] == {"used": 2, "available": 2}
    text = subprocess.run(command + ["--format", "text"], env=env, text=True, capture_output=True)
    assert text.returncode == 0, text.stderr
    assert "Physical timing: unverified. Board rate: unmeasured." in text.stdout
    assert "FAB_IN0.i: event_i" in text.stdout
    assert '"DIV": 16' in text.stdout


@pytest.mark.parametrize("field,value,message", [
    ("params", {"DIV": [16]}, "parameters"),
    ("params", {"DIV": float("inf")}, "parameters"),
    ("tools", {"yosys": 123}, "tool versions"),
    ("build_options", None, "build options"),
    ("pins", {"FAB_IN0": {"bad": "event_i"}}, "pin mapping"),
    ("pins", {"FAB_IN0": {"i": None}}, "pin mapping"),
    ("unmapped_outputs_open", "tx", "unmapped"),
])
def test_malformed_user_facing_metadata_rejected(evidence, field, value, message):
    report_path, architecture, report, budget, _ = evidence
    report[field] = value
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match=message):
        certificate(report_path, architecture, budget)


def test_summary_reports_unknown_timing_and_failed_host_model(evidence):
    report_path, architecture, report, budget, _ = evidence
    report.update(fmax_mhz=None, meets_50mhz=False)
    report_path.write_text(json.dumps(report))
    budget["arrival_bytes_s"] = 1000000
    text = operating_summary(certificate(report_path, architecture, budget))
    assert "Compiler clock estimate: unknown; requested clock unknown." in text
    assert "service margin False; queue sufficient False" in text
    assert "Physical timing: unverified. Board rate: unmeasured." in text
