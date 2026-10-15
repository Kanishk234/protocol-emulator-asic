"""Supervise approved GitHub checks; never edit hardware or promote a candidate.

Run from the project venv with PYTHONPATH=tools. State, downloads and logs stay
under build/. A dry tick is read-only on GitHub. --launch explicitly enables a
finite campaign on one exact efpga revision. This is a test supervisor, not an AI
process: the active Codex session supplies research, implementation and review.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

from autonomy.check_xml import check_xml

ROOT = Path(__file__).resolve().parents[2]
REPO = "Kanishk234/protocol-emulator-asic"
TASKS = {
    "uart-phase": ("uart_phase_stress.yaml", "loaded-uart-phase", "phase"),
    "active-cancel": ("trigger_cancel_loaded.yaml", "baseline-trigger-cancel", "cancel"),
    "c-host": ("c_host_loaded.yaml", "baseline-c-host-loaded", "c-host"),
    "compiler-seeds": ("seed_robustness.yaml", "frozen-g1-seed-robustness", "seeds"),
}
TERMINAL = {"verified", "workflow_failed", "evidence_rejected", "dispatch_uncertain"}


def gh(*args, structured=True):
    command = ["gh", *args]
    if args[0] != "api":
        command.extend(["--repo", REPO])
    result = subprocess.run(command, cwd=ROOT,
                            text=True, capture_output=True, check=True, timeout=90)
    return json.loads(result.stdout) if structured else result.stdout


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def one(directory, name):
    paths = list(directory.rglob(name))
    if len(paths) != 1:
        raise ValueError(f"Expected exactly one {name}; found {len(paths)}")
    return paths[0]


def strict_xml(path):
    names = check_xml(path)
    if len(names) != 1:
        raise ValueError("Expected one executed passing test, no failures/errors/skips")
    return names[0]


def compiled_image(directory):
    report = json.loads(one(directory, "report.json").read_text())
    if report.get("arch") != "warp_g1" or report.get("arch_version") != "0x0003":
        raise ValueError("Unexpected compiled architecture")
    provenance = report["provenance"]
    image = one(directory, Path(provenance["bitfile"]).name)
    if sha(image) != provenance["bitfile_sha256"]:
        raise ValueError("Downloaded loadable image differs from compile report")
    return report


def validate_evidence(directory, kind, revision):
    result = {"scope": kind, "physical_acceptance": False, "timing_acceptance": False}
    if kind == "phase":
        result["test"] = strict_xml(one(directory, "results.xml"))
        trace = json.loads(one(directory, "phase_trace.json").read_text())
        if result["test"] != "uart_phase_and_read_delay" or trace.get("passed") is not True or len(trace.get("cases", [])) != 48:
            raise ValueError("Incomplete phase sweep")
    elif kind in ("cancel", "c-host"):
        result["test"] = strict_xml(one(directory, "loaded_results.xml"))
        expected_test = "test_active_window_cancel_loaded" if kind == "cancel" else "test_portable_c_host_loaded"
        if result["test"] != expected_test:
            raise ValueError("Wrong executed loaded test")
        report = compiled_image(directory)
        if kind == "cancel" and any(report["params"].get(k) != v for k, v in
                {"COUNTER_BITS": 9, "WINDOW_CYCLES": 256, "DELAY_CYCLES": 4}.items()):
            raise ValueError("Wrong active-cancellation scheduler parameters")
        result["image_sha256"] = report["provenance"]["bitfile_sha256"]
    elif kind == "seeds":
        summary = json.loads(one(directory, "summary.json").read_text())
        rows = summary.get("trials", [])
        pairs = [(row["design"], row["seed"]) for row in rows]
        expected = {(design, seed) for design in ("uart", "spi_ctrl", "i2c_ctrl") for seed in range(3)}
        if (summary.get("commit") != revision or summary.get("passed") is not True or
                summary.get("inputs_unchanged") is not True or len(pairs) != 9 or
                set(pairs) != expected or any(row.get("fits") is not True or
                row.get("returncode") != 0 or row.get("timed_out") is not False for row in rows)):
            raise ValueError("Incomplete, mismatched or failing compiler seed matrix")
        result["compiled_trials"] = 9
    else:
        raise ValueError("Unknown evidence kind")
    files = sorted(p for p in directory.rglob("*") if p.is_file())
    if not files or any(p.is_symlink() for p in directory.rglob("*")):
        raise ValueError("Empty or linked evidence bundle")
    result["files_sha256"] = {str(p.relative_to(directory)): sha(p) for p in files}
    return result


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


@contextmanager
def locked(directory):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "supervisor.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def matching_runs(runs, revision):
    return sorted((r for r in runs if r["headSha"] == revision),
                  key=lambda r: (r["createdAt"], r["databaseId"]), reverse=True)


def tick(directory, revision, tasks, launch=False, max_launches=4, parallel=2, client=gh):
    state_path = directory / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {"version": 1, "campaigns": {}}
    campaign = state["campaigns"].setdefault(revision, {"launches": 0, "tasks": {}})
    snapshots = {}
    for task in tasks:
        workflow = TASKS[task][0]
        snapshots[task] = client("run", "list", "--workflow", workflow, "--branch", "efpga", "--limit", "50",
            "--json", "databaseId,headSha,event,createdAt,status,conclusion,url")
    active = sum(r["status"] != "completed" for runs in snapshots.values() for r in runs)
    remote_head = None
    for task in tasks:
        workflow, prefix, kind = TASKS[task]
        entry = campaign["tasks"].setdefault(task, {"status": "pending"})
        if entry["status"] in TERMINAL - {"verified"}:
            continue
        runs = matching_runs(snapshots[task], revision)
        run = runs[0] if runs else None
        # Recorded run IDs must not disappear just because a busy workflow's
        # newest fifty entries no longer include them. Query that ID directly.
        run_id = entry.get("run_id") or (run["databaseId"] if run else None)
        if run_id:
            actual = client("api", f"repos/{REPO}/actions/runs/{run_id}")
            if (actual["id"] != run_id or actual["head_sha"] != revision or actual["head_branch"] != "efpga" or
                    actual["path"] != ".github/workflows/" + workflow):
                raise ValueError("Recorded GitHub run identity differs")
            run = {"databaseId": actual["id"], "status": actual["status"],
                   "conclusion": actual["conclusion"], "url": actual["html_url"],
                   "attempt": actual["run_attempt"], "started_at": actual["run_started_at"]}
        if run:
            if entry["status"] == "verified" and entry["attempt"] == run["attempt"]:
                evidence = directory / "evidence" / f"{entry['run_id']}-{entry['attempt']}"
                try:
                    actual_evidence = validate_evidence(evidence, kind, revision)
                    if actual_evidence != entry["evidence"]:
                        raise ValueError("Persisted verified evidence manifest differs")
                except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
                    entry.update(status="evidence_rejected", error=str(exc))
                continue
            entry.update(run_id=run["databaseId"], attempt=run["attempt"], url=run["url"], status="running")
            if run["status"] != "completed":
                continue
            entry["conclusion"] = run["conclusion"]
            if run["conclusion"] != "success":
                entry["status"] = "workflow_failed"
                continue
            # A failed/missing download remains pending collection and can retry
            # next tick, without re-dispatching the experiment.
            entry["status"] = "collecting"
            save(state_path, state)
            evidence = directory / "evidence" / f"{run['databaseId']}-{run['attempt']}"
            artifacts = client("api", f"repos/{REPO}/actions/runs/{run['databaseId']}/artifacts?per_page=100")
            artifacts = [a for a in artifacts["artifacts"] if a["name"] == f"{prefix}-{run['databaseId']}"]
            if (len(artifacts) != 1 or artifacts[0]["expired"] or
                    artifacts[0]["created_at"] < run["started_at"]):
                entry.update(status="evidence_rejected", error="Missing, duplicate, expired or prior-attempt artifact")
                continue
            entry["artifact"] = {k: artifacts[0].get(k) for k in ("id", "name", "digest", "created_at", "expires_at")}
            if not evidence.exists():
                with tempfile.TemporaryDirectory(dir=directory) as staging:
                    client("run", "download", str(run["databaseId"]), "--name", f"{prefix}-{run['databaseId']}",
                           "--dir", staging, structured=False)
                    evidence.parent.mkdir(parents=True, exist_ok=True)
                    Path(staging).rename(evidence)
            try:
                entry["evidence"] = validate_evidence(evidence, kind, revision)
                entry["status"] = "verified"
            except (ValueError, KeyError, TypeError, ET.ParseError) as exc:
                entry.update(status="evidence_rejected", error=str(exc))
        elif entry["status"] == "dispatching":
            # Persist-before-dispatch prevents duplicate launch after a crash or
            # HTTP timeout. Never retry an ambiguous dispatch automatically.
            if time.time() - entry["dispatch_epoch"] > 600:
                entry.update(status="dispatch_uncertain", error="No matching run after ten minutes; investigate before retry")
        elif launch and campaign["launches"] < max_launches and active < parallel:
            if remote_head is None:
                remote_head = client("api", f"repos/{REPO}/git/ref/heads/efpga", structured=True)["object"]["sha"]
            if remote_head != revision:
                entry["note"] = "Branch advanced; refuse dispatch at a different revision"
                continue
            entry.update(status="dispatching", dispatch_epoch=time.time())
            campaign["launches"] += 1
            save(state_path, state)
            client("workflow", "run", workflow, "--ref", "efpga", "-f", f"expected_sha={revision}", structured=False)
            active += 1
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    save(state_path, state)
    dashboard = ["# WARP experiment supervisor", "", f"Revision: `{revision}`", "",
        "Verification below covers individual tests only. No hardware promotion or physical/timing signoff.", "",
        "| Task | State | Run |", "|---|---|---|"]
    for name, entry in campaign["tasks"].items():
        dashboard.append(f"| {name} | {entry['status']} | {entry.get('url', '')} |")
    (directory / "STATUS.md").write_text("\n".join(dashboard) + "\n")
    with (directory / "events.jsonl").open("a") as stream:
        stream.write(json.dumps({"time": state["updated_at"], "revision": revision,
            "tasks": {k: v["status"] for k, v in campaign["tasks"].items()}}) + "\n")
    return campaign


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--state-dir", type=Path, default=ROOT / "build/autonomy")
    parser.add_argument("--tasks", nargs="+", choices=TASKS, default=list(TASKS))
    parser.add_argument("--launch", action="store_true")
    parser.add_argument("--watch-hours", type=float, default=0)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--max-launches", type=int, default=4)
    parser.add_argument("--parallel", type=int, default=2)
    args = parser.parse_args()
    args.tasks = list(dict.fromkeys(args.tasks))
    if (not re.fullmatch(r"[0-9a-f]{40}", args.revision) or not 0 <= args.watch_hours <= 24 or
            not 30 <= args.poll_seconds <= 300 or not 0 <= args.max_launches <= 4 or not 1 <= args.parallel <= 2):
        parser.error("Require exact SHA, <=24h, 30..300s polling, <=4 launches and <=2 parallel checks")
    deadline = time.monotonic() + args.watch_hours * 3600
    with locked(args.state_dir):
        while True:
            if (args.state_dir / "STOP").exists():
                print("STOP file present; no further supervision or launches", flush=True)
                return
            try:
                campaign = tick(args.state_dir, args.revision, args.tasks, args.launch, args.max_launches, args.parallel)
                print(json.dumps({k: v["status"] for k, v in campaign["tasks"].items()}), flush=True)
            except (subprocess.SubprocessError, OSError, ValueError) as exc:
                # A network failure is neither a chip failure nor permission to
                # launch replacement runs. Preserve existing state and report it.
                print(f"Supervisor infrastructure error: {exc}", flush=True)
                if args.watch_hours == 0:
                    raise
            else:
                if all(campaign["tasks"][task]["status"] in TERMINAL for task in args.tasks):
                    return
            if time.monotonic() >= deadline:
                return
            time.sleep(min(args.poll_seconds, max(0, deadline - time.monotonic())))


if __name__ == "__main__":
    main()
