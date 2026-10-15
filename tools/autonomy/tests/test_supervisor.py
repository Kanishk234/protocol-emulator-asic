"""Campaign safety and independent artifact rejection without cloud costs."""
import hashlib
import json
from pathlib import Path

import pytest

from autonomy import supervisor as s

REV = "a" * 40


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def xml(path, content='<testsuite><testcase name="executed"/></testsuite>'):
    path.write_text(content)


@pytest.mark.parametrize("body", [
    '<testsuite/>', '<testsuite><testcase><skipped/></testcase></testsuite>',
    '<testsuite><testcase><error/></testcase></testsuite>',
    '<testsuite><testcase><failure/></testcase></testsuite>',
    '<testsuite><testcase/><testcase/></testsuite>',
    '<testsuite failures="1"><testcase/></testsuite>',
])
def test_reject_false_green_xml(tmp_path, body):
    path = tmp_path / "results.xml"
    xml(path, body)
    with pytest.raises(ValueError):
        s.strict_xml(path)


def image_bundle(directory):
    xml(directory / "loaded_results.xml", '<testsuite><testcase name="test_active_window_cancel_loaded"/></testsuite>')
    image = directory / "trigger.wbit"
    image.write_bytes(b"actual downloaded image")
    report = {"arch": "warp_g1", "arch_version": "0x0003",
              "params": {"COUNTER_BITS": 9, "WINDOW_CYCLES": 256, "DELAY_CYCLES": 4},
              "provenance": {"bitfile": "/cloud/build/trigger.wbit",
                             "bitfile_sha256": hashlib.sha256(image.read_bytes()).hexdigest()}}
    write(directory / "report.json", report)
    return report


def test_loaded_image_matches_report_and_actual_parameters(tmp_path):
    report = image_bundle(tmp_path)
    result = s.validate_evidence(tmp_path, "cancel", REV)
    assert result["physical_acceptance"] is result["timing_acceptance"] is False
    assert "trigger.wbit" in result["files_sha256"]
    report["params"]["WINDOW_CYCLES"] = 4
    write(tmp_path / "report.json", report)
    with pytest.raises(ValueError, match="parameters"):
        s.validate_evidence(tmp_path, "cancel", REV)
    (tmp_path / "trigger.wbit").write_bytes(b"stale other build")
    with pytest.raises(ValueError, match="differs"):
        s.validate_evidence(tmp_path, "cancel", REV)


def test_seed_matrix_rejects_duplicates_even_with_green_summary(tmp_path):
    rows = [{"design": design, "seed": seed, "fits": True, "returncode": 0, "timed_out": False}
            for design in ("uart", "spi_ctrl", "i2c_ctrl") for seed in range(3)]
    summary = {"passed": True, "inputs_unchanged": True, "commit": REV, "trials": rows}
    write(tmp_path / "summary.json", summary)
    assert s.validate_evidence(tmp_path, "seeds", REV)["compiled_trials"] == 9
    rows[-1] = rows[0]
    write(tmp_path / "summary.json", summary)
    with pytest.raises(ValueError, match="matrix"):
        s.validate_evidence(tmp_path, "seeds", REV)


class FakeGitHub:
    def __init__(self, revision=REV, runs=None, fail_dispatch=False, actual_runs=None,
                 artifacts=None):
        self.revision, self.runs = revision, runs or []
        self.fail_dispatch = fail_dispatch
        self.actual_runs = actual_runs
        self.artifacts = artifacts
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append(args)
        if args[:2] == ("run", "list"):
            return self.runs
        if args[0] == "api":
            if args[1].split("?", 1)[0].endswith("/artifacts"):
                artifacts = self.artifacts if self.artifacts is not None else [artifact_record()]
                return {"total_count": len(artifacts), "artifacts": artifacts}
            if "/actions/runs/" in args[1]:
                if self.actual_runs is not None:
                    return self.actual_runs[int(args[1].rsplit("/", 1)[1])]
                run = self.runs[0]
                return {"head_sha": run["headSha"], "head_branch": "efpga", "id": run["databaseId"],
                        "path": ".github/workflows/trigger_cancel_loaded.yaml", "status": run["status"],
                        "conclusion": run["conclusion"], "html_url": run["url"], "run_attempt": 1,
                        "run_started_at": "2026-10-15T00:00:00Z"}
            return {"object": {"sha": self.revision}}
        if args[:2] == ("workflow", "run"):
            if self.fail_dispatch:
                raise OSError("ambiguous timeout")
            return ""
        if args[:2] == ("run", "download"):
            destination = Path(args[args.index("--dir") + 1])
            image_bundle(destination)
            return ""
        raise AssertionError(args)


def run_record(sha=REV, status="completed", conclusion="success"):
    return {"headSha": sha, "databaseId": 123, "status": status, "conclusion": conclusion,
            "createdAt": "2026-10-15T00:00:00Z", "url": "https://example.test/run/123"}


def test_read_only_default_and_advanced_branch_refusal(tmp_path):
    github = FakeGitHub()
    s.tick(tmp_path, REV, ["active-cancel"], client=github)
    assert not any(c[:2] == ("workflow", "run") for c in github.calls)
    github = FakeGitHub(revision="b" * 40)
    campaign = s.tick(tmp_path, REV, ["active-cancel"], launch=True, client=github)
    assert campaign["launches"] == 0
    assert "Branch advanced" in campaign["tasks"]["active-cancel"]["note"]


def test_persist_before_ambiguous_dispatch_prevents_duplicate(tmp_path):
    github = FakeGitHub(fail_dispatch=True)
    with pytest.raises(OSError, match="timeout"):
        s.tick(tmp_path, REV, ["active-cancel"], launch=True, client=github)
    github.fail_dispatch = False
    s.tick(tmp_path, REV, ["active-cancel"], launch=True, client=github)
    assert sum(c[:2] == ("workflow", "run") for c in github.calls) == 1
    assert json.loads((tmp_path / "state.json").read_text())["campaigns"][REV]["launches"] == 1


def test_reuse_exact_revision_and_verify_download_before_accepting(tmp_path):
    github = FakeGitHub(runs=[run_record()])
    campaign = s.tick(tmp_path, REV, ["active-cancel"], launch=True, client=github)
    assert campaign["tasks"]["active-cancel"]["status"] == "verified"
    assert not any(c[:2] == ("workflow", "run") for c in github.calls)
    assert (tmp_path / "evidence/123-1/trigger.wbit").exists()
    assert "No hardware promotion" in (tmp_path / "STATUS.md").read_text()


def test_old_revision_cannot_substitute_for_requested_test(tmp_path):
    github = FakeGitHub(runs=[run_record(sha="b" * 40)])
    campaign = s.tick(tmp_path, REV, ["active-cancel"], client=github)
    assert campaign["tasks"]["active-cancel"]["status"] == "pending"


def test_failure_stays_failure_and_is_never_retried(tmp_path):
    github = FakeGitHub(runs=[run_record(conclusion="failure")])
    campaign = s.tick(tmp_path, REV, ["active-cancel"], launch=True, client=github)
    assert campaign["tasks"]["active-cancel"]["status"] == "workflow_failed"
    s.tick(tmp_path, REV, ["active-cancel"], launch=True, client=github)
    assert not any(c[:2] == ("workflow", "run") for c in github.calls)


def test_campaign_respects_parallel_and_total_budget(tmp_path):
    github = FakeGitHub()
    campaign = s.tick(tmp_path, REV, list(s.TASKS), launch=True, max_launches=1, client=github)
    assert campaign["launches"] == 1
    assert sum(c[:2] == ("workflow", "run") for c in github.calls) == 1


def test_single_writer_lock(tmp_path):
    with s.locked(tmp_path):
        with pytest.raises(BlockingIOError):
            with s.locked(tmp_path):
                raise AssertionError("second writer admitted")


def actual_record(**overrides):
    result = {"head_sha": REV, "head_branch": "efpga", "id": 123,
              "path": ".github/workflows/trigger_cancel_loaded.yaml",
              "status": "completed", "conclusion": "success",
              "html_url": "https://example.test/run/123", "run_attempt": 1,
              "run_started_at": "2026-10-15T00:00:00Z"}
    result.update(overrides)
    return result


def artifact_record(**overrides):
    result = {"id": 456, "name": "baseline-trigger-cancel-123", "expired": False,
              "created_at": "2026-10-15T00:00:01Z"}
    result.update(overrides)
    return result


def test_recorded_run_missing_from_latest_fifty_is_queried_by_id(tmp_path):
    github = FakeGitHub(runs=[run_record(status="in_progress", conclusion=None)],
                        actual_runs={123: actual_record(status="in_progress", conclusion=None)})
    initial = s.tick(tmp_path, REV, ["active-cancel"], launch=True, client=github)
    assert initial["tasks"]["active-cancel"]["status"] == "running"
    github.runs = [dict(run_record(sha="b" * 40), databaseId=1000 + i)
                   for i in range(50)]
    github.actual_runs[123] = actual_record()
    github.calls.clear()
    resumed = s.tick(tmp_path, REV, ["active-cancel"], launch=True, client=github)
    assert resumed["tasks"]["active-cancel"]["status"] == "verified"
    assert ("api", f"repos/{s.REPO}/actions/runs/123") in github.calls
    assert any(call[:3] == ("run", "download", "123") for call in github.calls)
    assert not any(call[:2] == ("workflow", "run") for call in github.calls)


@pytest.mark.parametrize("overrides", [
    {"head_sha": "b" * 40}, {"head_branch": "main"},
    {"path": ".github/workflows/c_host_loaded.yaml"}, {"id": 999},
])
def test_actual_api_identity_overrides_green_snapshot_and_never_dispatches(tmp_path, overrides):
    github = FakeGitHub(runs=[run_record()], actual_runs={123: actual_record(**overrides)})
    with pytest.raises(ValueError, match="identity"):
        s.tick(tmp_path, REV, ["active-cancel"], launch=True, client=github)
    assert not any(call[:2] in (("workflow", "run"), ("run", "download"))
                   for call in github.calls)


@pytest.mark.parametrize("artifacts", [
    [], [artifact_record(expired=True)],
    [artifact_record(created_at="2026-10-14T23:59:59Z")],
    [artifact_record(name="baseline-trigger-cancel-999")],
    [artifact_record(), artifact_record(id=789)],
])
def test_stale_missing_expired_or_duplicate_artifact_cannot_verify_green_run(tmp_path, artifacts):
    github = FakeGitHub(runs=[run_record()], artifacts=artifacts)
    try:
        campaign = s.tick(tmp_path, REV, ["active-cancel"], launch=True, client=github)
    except ValueError:
        pass
    else:
        assert campaign["tasks"]["active-cancel"]["status"] != "verified"
    assert not any(call[:2] in (("workflow", "run"), ("run", "download"))
                   for call in github.calls)


def test_verified_run_rerun_in_progress_invalidates_old_attempt_evidence(tmp_path):
    github = FakeGitHub(runs=[run_record()], actual_runs={123: actual_record()})
    assert s.tick(tmp_path, REV, ["active-cancel"], client=github)["tasks"]["active-cancel"]["status"] == "verified"
    github.actual_runs[123] = actual_record(run_attempt=2, status="in_progress", conclusion=None)
    github.calls.clear()
    resumed = s.tick(tmp_path, REV, ["active-cancel"], launch=True, client=github)
    assert resumed["tasks"]["active-cancel"]["status"] == "running"
    assert resumed["tasks"]["active-cancel"]["attempt"] == 2
    assert not any(call[:2] in (("workflow", "run"), ("run", "download"))
                   for call in github.calls)


def test_completed_new_attempt_collects_current_evidence_in_separate_directory(tmp_path):
    github = FakeGitHub(runs=[run_record()], actual_runs={123: actual_record()})
    assert s.tick(tmp_path, REV, ["active-cancel"], client=github)["tasks"]["active-cancel"]["status"] == "verified"
    github.actual_runs[123] = actual_record(run_attempt=2, run_started_at="2026-10-15T00:10:00Z")
    github.artifacts = [artifact_record(id=789, created_at="2026-10-15T00:10:01Z")]
    github.calls.clear()
    resumed = s.tick(tmp_path, REV, ["active-cancel"], launch=True, client=github)
    assert resumed["tasks"]["active-cancel"]["status"] == "verified"
    assert resumed["tasks"]["active-cancel"]["attempt"] == 2
    assert (tmp_path / "evidence/123-1/trigger.wbit").exists()
    assert (tmp_path / "evidence/123-2/trigger.wbit").exists()
    assert sum(call[:2] == ("run", "download") for call in github.calls) == 1
    assert not any(call[:2] == ("workflow", "run") for call in github.calls)


@pytest.mark.parametrize("kind", ["cancel", "c-host"])
def test_passing_unrelated_testcase_does_not_substitute_for_loaded_integration(tmp_path, kind):
    image_bundle(tmp_path)
    xml(tmp_path / "loaded_results.xml", '<testsuite><testcase name="unrelated_smoke"/></testsuite>')
    with pytest.raises(ValueError):
        s.validate_evidence(tmp_path, kind, REV)


@pytest.mark.parametrize("tamper", ["image", "xml", "missing", "manifest"])
def test_resumed_verified_evidence_is_rechecked_before_reusing_status(tmp_path, tamper):
    github = FakeGitHub(runs=[run_record()])
    initial = s.tick(tmp_path, REV, ["active-cancel"], launch=True, client=github)
    assert initial["tasks"]["active-cancel"]["status"] == "verified"
    evidence = tmp_path / "evidence/123-1"
    if tamper == "image":
        (evidence / "trigger.wbit").write_bytes(b"changed after first verification")
    elif tamper == "xml":
        xml(evidence / "loaded_results.xml", '<testsuite><testcase name="other"/></testsuite>')
    elif tamper == "missing":
        (evidence / "loaded_results.xml").unlink()
    else:
        state_path = tmp_path / "state.json"
        state = json.loads(state_path.read_text())
        entry = state["campaigns"][REV]["tasks"]["active-cancel"]
        entry["evidence"]["files_sha256"]["trigger.wbit"] = "0" * 64
        write(state_path, state)
    github.calls.clear()
    resumed = s.tick(tmp_path, REV, ["active-cancel"], launch=True, client=github)
    assert resumed["tasks"]["active-cancel"]["status"] == "evidence_rejected"
    assert not any(call[:2] in (("workflow", "run"), ("run", "download"))
                   for call in github.calls)
