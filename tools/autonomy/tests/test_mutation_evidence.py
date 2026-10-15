"""Mutation evidence fixtures; no simulator or formal executable is run."""
import importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

spec = importlib.util.spec_from_file_location("mutation_evidence", Path(__file__).resolve().parents[3] / "scripts/mutation.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def bundle(repo, command="make -C test_internal", failure=None, skipped=None, error=None):
    expected = m.expectation(command)
    root = ET.Element("testsuite")
    for name in sorted(expected["required"] | expected["skips"]):
        case = ET.SubElement(root, "testcase", name=name)
        if name in expected["skips"] or name == skipped:
            ET.SubElement(case, "skipped")
        if name == failure:
            ET.SubElement(case, "failure")
        if name == error:
            ET.SubElement(case, "error")
    path = repo / expected["xml"]
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(path)
    return path


def test_pristine_requires_exact_executed_cases(tmp_path):
    bundle(tmp_path)
    assert m.classify(tmp_path, "make -C test_internal", 0, "")[0] == "pass"


@pytest.mark.parametrize("kind", ["missing", "empty", "malformed", "error", "skip", "wrong_case", "counter", "compile", "timeout", "signal"])
def test_setup_and_harness_failures_never_kill(tmp_path, kind):
    path = bundle(tmp_path)
    code, text, timeout = 1, "", False
    if kind == "missing":
        path.unlink()
    elif kind == "empty":
        path.write_text("<testsuite/>")
    elif kind == "malformed":
        path.write_text("<testsuite")
    elif kind == "error":
        bundle(tmp_path, error="test_timer_matches_model")
    elif kind == "skip":
        bundle(tmp_path, skipped="test_timer_matches_model")
    elif kind == "wrong_case":
        path.write_text('<testsuite><testcase name="unrelated"/></testsuite>')
    elif kind == "counter":
        path.write_text(path.read_text().replace("<testsuite>", '<testsuite failures="1">'))
        code = 0
    elif kind == "compile":
        bundle(tmp_path, failure="test_timer_matches_model")
        text = "ImportError: no module"
    elif kind == "timeout":
        timeout = True
    elif kind == "signal":
        code = -9
    assert m.classify(tmp_path, "make -C test_internal", code, text, timeout)[0] == "error"


def test_actual_assertion_rejection_kills(tmp_path):
    bundle(tmp_path, failure="test_timer_matches_model")
    assert m.classify(tmp_path, "make -C test_internal", 2, "AssertionError: bad period")[0] == "rejected"


def test_mixed_assertion_and_setup_exception_is_not_killed(tmp_path):
    bundle(tmp_path, failure="test_timer_matches_model")
    assert m.classify(tmp_path, "make -C test_internal", 2,
                      "AssertionError: setup guard\nImportError: missing simulation package")[0] == "error"


def test_contradictory_skip_and_failure_is_not_a_pass(tmp_path):
    command = "COCOTB_TEST_FILTER=test_logic4 make -C test WARP_FABRIC=rtl"
    path = bundle(tmp_path, command)
    root = ET.parse(path).getroot()
    case = next(c for c in root.iter("testcase") if c.get("name") != "test_logic4")
    ET.SubElement(case, "failure")
    ET.ElementTree(root).write(path)
    assert m.classify(tmp_path, command, 0, "")[0] == "error"


def test_known_filtered_cases_may_skip_but_target_must_execute(tmp_path):
    command = "COCOTB_TEST_FILTER=test_logic4 make -C test WARP_FABRIC=rtl"
    bundle(tmp_path, command)
    assert m.classify(tmp_path, command, 0, "")[0] == "pass"
    bundle(tmp_path, command, skipped="test_logic4")
    assert m.classify(tmp_path, command, 0, "")[0] == "error"


@pytest.mark.parametrize("status,code,output,engine,expected", [
    (None, 127, "sby: command not found", "", "error"),
    ("ERROR", 1, "DONE (ERROR)", "", "error"),
    ("FAIL", 1, "DONE (FAIL)", "solver unavailable", "error"),
    ("PASS", 0, "DONE (PASS)", "", "pass"),
    ("FAIL", 1, "DONE (FAIL)", "Assert failed in tt_um_warp: isolation", "rejected"),
])
def test_formal_requires_actual_property_status(tmp_path, status, code, output, engine, expected):
    directory = tmp_path / "formal/f1_isolation"
    (directory / "engine_0").mkdir(parents=True)
    if status is not None:
        (directory / "status").write_text(status)
    (directory / "engine_0/logfile.txt").write_text(engine)
    assert m.classify(tmp_path, "cd formal && sby -f f1_isolation.sby", code, output)[0] == expected


@pytest.mark.parametrize('status,code,output,expected',[
    ('PASS 0 0',0,'DONE (PASS, rc=0)','pass'),
    ('FAIL 0 1',1,'DONE (FAIL, rc=1)','rejected'),
    ('PASS garbage',0,'DONE (PASS, rc=0)','error'),
])
def test_actual_sby_status_counters_and_split_engine_logs(tmp_path,status,code,output,expected):
    directory=tmp_path/'formal/f1_isolation'
    (directory/'engine_0').mkdir(parents=True)
    (directory/'status').write_text(status+'\n')
    (directory/'engine_0/logfile_basecase.txt').write_text('Assert failed in tt_um_warp: isolation')
    assert m.classify(tmp_path,'cd formal && sby -f f1_isolation.sby',code,output)[0]==expected


@pytest.mark.parametrize("control_verdict,expected_calls", [("pass", 3), ("error", 1)])
def test_controls_deduplicated_and_failed_control_blocks_mutants(tmp_path, monkeypatch, control_verdict, expected_calls):
    monkeypatch.setattr(m, "ROOT", tmp_path)
    monkeypatch.setattr(m, "WORK", tmp_path / "campaign")
    monkeypatch.setattr(m.sys, "prefix", str(tmp_path / ".venv"))
    monkeypatch.setenv("WARP_TILES", "/already/fetched")
    monkeypatch.setattr(m.subprocess, "check_output", lambda *a, **k: "a" * 40 + "\n")
    command = "make -C test_internal"
    definition = ("test mutation", [("design.v", "before", "after")], command, "primitive tests")
    monkeypatch.setattr(m, "MUTANTS", {"one": definition, "two": definition})
    calls = []

    def copy(repo):
        repo.mkdir()
        (repo / "design.v").write_text("before")

    def run(repo, command, env, log):
        calls.append(repo.name)
        return {"verdict": control_verdict if repo.name.startswith("control") else "rejected", "detail": "fixture"}

    monkeypatch.setattr(m, "copy_repo", copy)
    monkeypatch.setattr(m, "run_check", run)
    assert m.main([]) == (0 if control_verdict == "pass" else 1)
    assert len(calls) == expected_calls
    assert not (tmp_path / "docs/reports/mutation.md").exists()
