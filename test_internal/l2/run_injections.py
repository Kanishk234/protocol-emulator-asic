"""Run L2-INJECT against isolated copies of one explicit RTL candidate."""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
RTL_DIR = pathlib.Path(os.environ.get("RTL_DIR", "/tmp/r4-bitsync-work/src")).resolve()
RTL_REV = os.environ.get("RTL_REV", "unknown")
MAKE = ["make", "-C", "test_internal/l2", "SIM=verilator"]


def mutate_file(tree: pathlib.Path, filename: str, before: str, after: str) -> None:
    path = tree / filename
    source = path.read_text()
    if source.count(before) != 1:
        raise RuntimeError(f"expected one mutation anchor in {path}, found {source.count(before)}")
    path.write_text(source.replace(before, after, 1))


def cursor_mutation(source: str) -> tuple[str, str]:
    """Inject the same normal-cursor increment fault in either reviewed form."""
    forms = (
        ("wire [15:0] q_inc  = (r_wrap && (qn != 16'h7fff)) ? qn + 16'd1 : qn;",
         "wire [15:0] q_inc  = (r_wrap && (qn != 16'h7fff)) ? qn + 16'd2 : qn;"),
        ("wire [15:0] base_inc = (base_wrap && (q_b != 16'h7fff)) ? q_b + 16'd1 : q_b;",
         "wire [15:0] base_inc = (base_wrap && (q_b != 16'h7fff)) ? q_b + 16'd2 : q_b;"),
    )
    found = [pair for pair in forms if source.count(pair[0]) == 1]
    if len(found) != 1 or any(source.count(pair[0]) > 1 for pair in forms):
        raise RuntimeError('Expected exactly one reviewed cursor mutation form')
    return found[0]


def isolated_make(directory: pathlib.Path) -> list[str]:
    """Source paths alone do not invalidate a newer compiled Verilator model."""
    return MAKE + [f'SIM_BUILD={directory / "sim_build"}',
                   f'COCOTB_RESULTS_FILE={directory / "results.xml"}']


def run_baseline(scenario: str, clocks: int = 1024) -> None:
    """Require the untouched candidate to pass before crediting a mutation."""
    env = os.environ.copy()
    env.update({
        "RTL_DIR": str(RTL_DIR),
        "RTL_REV": RTL_REV,
        "L2_SCENARIO": scenario,
        "L2_CYCLES": str(clocks),
    })
    with tempfile.TemporaryDirectory(prefix=f'tripwire-l2-baseline-{scenario}-') as tmp:
        result = subprocess.run(isolated_make(pathlib.Path(tmp)), cwd=ROOT, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode != 0 or "first lockstep divergence" in result.stdout:
        print(result.stdout[-6000:])
        raise SystemExit(f"L2-INJECT {scenario}: clean RTL baseline failed; mutation evidence is invalid")
    print(f"L2-INJECT {scenario}: unmodified RTL baseline passed")


def run_mutation(name: str, relative_file: str, before: str, after: str,
                 scenario: str, clocks: int = 1024) -> None:
    with tempfile.TemporaryDirectory(prefix=f"tripwire-l2-{name}-") as tmp:
        mutated = pathlib.Path(tmp) / "src"
        shutil.copytree(RTL_DIR, mutated)
        mutate_file(mutated, relative_file, before, after)
        env = os.environ.copy()
        env.update({
            "RTL_DIR": str(mutated),
            "RTL_REV": f"{RTL_REV}-inject-{name}",
            "L2_SCENARIO": scenario,
            "L2_CYCLES": str(clocks),
        })
        result = subprocess.run(isolated_make(pathlib.Path(tmp)), cwd=ROOT, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode == 0:
            raise SystemExit(f"L2-INJECT {name}: mutation escaped; RTL/model comparison passed")
        if "first lockstep divergence" not in result.stdout:
            print(result.stdout[-6000:])
            raise SystemExit(f"L2-INJECT {name}: simulator failed without a scoreboard divergence")
        lines = [line.strip() for line in result.stdout.splitlines()
                 if "first lockstep divergence" in line]
        print(f"L2-INJECT {name}: DETECTED ({'; '.join(lines[-2:])})")


def main() -> None:
    if not (RTL_DIR / "trw_lane.v").is_file():
        raise SystemExit(f"RTL candidate missing: {RTL_DIR}")
    run_baseline("rx", 1024)
    run_mutation(
        "priority-flip", "trw_lane.v",
        "wire [11:0] onehot = cand & (~cand + 12'd1);",
        "wire [11:0] onehot = cand & ~(cand >> 1 | cand >> 2 | cand >> 3 | cand >> 4 | "
        "cand >> 5 | cand >> 6 | cand >> 7 | cand >> 8 | cand >> 9 | cand >> 10 | cand >> 11);",
        "rx", 1024,
    )
    run_baseline("cursor", 1024)
    before, after = cursor_mutation((RTL_DIR / 'trw_pin_tx.v').read_text())
    run_mutation(
        "cursor-off-by-one", "trw_pin_tx.v",
        before, after,
        "cursor", 1024,
    )


if __name__ == "__main__":
    main()
