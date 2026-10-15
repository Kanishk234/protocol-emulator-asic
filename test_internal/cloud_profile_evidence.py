"""Fresh pinned design-set synthesis profile with retained provenance.

This does not replace historical measurements or qualify area/timing. Only the
four already-profiled design-set workloads enter the sweep; held-out inputs
are never discovered or read. Native tools run on the hosted runner.
"""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from profiling import workload

OUT = ROOT / "build/profile_evidence"
DESIGNS = {"uart", "spi_ctrl", "i2c_ctrl", "i2c_target"}
VARIANTS = {"LUT3", "LUT4", "LUT6", "LUT3+carry", "LUT4+carry", "LUT6+carry"}


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_profile(data):
    if set(data) != DESIGNS:
        raise ValueError("Incomplete or unapproved workload set")
    functions = set(workload.FUNCTIONS) | {"shared", "unused"}
    aggregate = Counter()
    for design, variants in data.items():
        if set(variants) != VARIANTS:
            raise ValueError("Incomplete or duplicated variant matrix")
        for variant, row in variants.items():
            for field in ("luts", "ffs"):
                if type(row[field]) is not int or row[field] <= 0:
                    raise ValueError("Invalid LUT/FF census")
            for field, total in (("lut_by_fn", row["luts"]), ("ff_by_fn", row["ffs"])):
                counts = row[field]
                if (not set(counts) <= functions or
                        any(type(v) is not int or v < 0 for v in counts.values()) or
                        sum(counts.values()) != total):
                    raise ValueError("Attribution does not conserve cell count")
            if row['ff_by_fn'].get('counter',0) <= 0 or row['ff_by_fn'].get('shift',0) <= 0:
                raise ValueError('Expected timing/shift state is unclassified; review role map')
            if variant == "LUT4":
                aggregate.update(row["lut_by_fn"])
    return {"trials": 24, "lut4_total": sum(aggregate.values()),
            "lut4_by_function": dict(aggregate),
            "lut4_by_design": {name: rows["LUT4"]["luts"] for name, rows in data.items()}}


def run_bounded(command):
    with (OUT / "profile.log").open("w") as log:
        child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                 start_new_session=True, env=dict(os.environ, PYTHONPATH=str(ROOT / "tools")))
        try:
            code = child.wait(timeout=600)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
            raise
        if code:
            raise RuntimeError(f"Profile subprocess failed with exit {code}; inspect retained profile.log")


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("Synthesis evidence refresh runs on the hosted runner")
    if {p.name for p in workload.PROTOCOLS} != DESIGNS or {v[0] for v in workload.VARIANTS} != VARIANTS:
        raise ValueError("Profiling inputs differ from approved matrix")
    OUT.mkdir(parents=True, exist_ok=False)
    result = {"passed": False, "physical_acceptance": False, "timing_acceptance": False}
    def save():
        (OUT / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    save()
    try:
        paths = {"tools/profiling/workload.py", "test_internal/cloud_profile_evidence.py",
                 ".github/workflows/profile_evidence.yaml", "requirements-dev.txt", "test/requirements.txt"}
        for protocol in workload.PROTOCOLS:
            if any(not name.startswith("protocols/" + protocol.name + "/") for name in protocol.files):
                raise ValueError("Profiling source escaped declared design set")
            paths.update(protocol.files)
        before = {name: sha(ROOT / name) for name in sorted(paths)}
        executable = shutil.which("yosys")
        if executable is None:
            raise RuntimeError("Pinned Yosys executable unavailable")
        yosys = Path(executable)
        version = subprocess.check_output([str(yosys), "-V"], text=True, timeout=10).strip()
        if not version.startswith("Yosys 0.66+179") or "e74db6dea" not in version:
            raise ValueError("Unpinned Yosys version")
        result.update(commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                      input_sha256=before, yosys_version=version, yosys_sha256=sha(yosys),
                      python_version=sys.version, python_executable=sys.executable,
                      workflow_run=os.environ.get("GITHUB_RUN_ID"),
                      workflow_attempt=os.environ.get("GITHUB_RUN_ATTEMPT"),
                      parameters={p.name: p.params for p in workload.PROTOCOLS},
                      attribution_roles={p.name: p.roles for p in workload.PROTOCOLS})
        save()
        command = [sys.executable, "-m", "profiling.workload", "--json", str(OUT / "profile.json"),
                   "--markdown", str(OUT / "tables.md"), "--workdir", str(OUT / "synthesis")]
        result["command"] = command
        run_bounded(command)
        result["summary"] = validate_profile(json.loads((OUT / "profile.json").read_text()))
        if before != {name: sha(ROOT / name) for name in sorted(paths)}:
            raise ValueError("Profile inputs changed during measurement")
        result.update(inputs_unchanged=True, passed=True,
                      output_sha256={name: sha(OUT / name) for name in ("profile.json", "tables.md")})
    except Exception as exc:
        result["error"] = str(exc)
        raise
    finally:
        save()


if __name__ == "__main__":
    main()
