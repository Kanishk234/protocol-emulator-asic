# Independent terminal collector integration review — October 19

Read-only review of `test_internal/cloud_route_force_repair.py` and
`tools/autonomy/repair_evidence.py`. No concrete blocker found for bounded
hosted qualification. The terminal parser's schema/semantic correctness is a
separate author/review task; this review checks orchestration and provenance,
not a completed actual terminal join. Build `39333325323` remains active at
review time. No EDA, source/test edits or dispatch was performed.

The generic native-export Tcl builder strictly allows only corridor/terminal and
initial/final values. It rejects inherited directory overrides, missing APIs and
preexisting export directories, creates a fresh directory, catches native errors
and unsets its override before propagating them. Before permission handoff it
requires the expected output to be a regular nonsymlink file. Only that completed
known file becomes readable0644; it does not recursively chmod arbitrary paths.

Each case captures corridor then terminal initial exports after same-process
exact121 segment/grid and physical-census hash guards, before any force call.
Final corridor and terminal exports occur after retained failure/segments/grid/
guide/geometry observations and before the native error is rethrown. This gives
six distinct terminal files for the three cases. Corridor and terminal controls
remain separate; no inherited environment value silently enables observation.

`qualify_native_terminals` requires the three exact cases and previously qualified
controls/raw ledger. It invokes `native_checkpoint.audit` on all six raw resource
files before terminal parsing: unchanged initial/default bytes, complete raw
capacity/reduction/real-capacity equality and internal coarse-pin census remain
mandatory. Each terminal snapshot requires the correctly ordered completion
witness suffix, exact one-file directory inventory, nonsymlink directory/file and
regular-file status. A terminal parser exception aborts collection. Raw/terminal
file hashes are checked before/after each membership audit, and the three initial
terminal hashes plus default final must be identical. Changed repair finals are
retained rather than forced to equal their initial state.

Successful collection does not depend on a true physical-access/solver graph
claim: unsupported terminal access remains diagnostic, while malformed exports
or failed prerequisite raw controls cannot become a completed collection.
Returned scope explicitly keeps native-input authentication and physical
acceptance false and describes coarse membership/access observation only.

The portable auditor requires explicit `--native-terminals`, which in turn
requires native-corridor and candidate modes. It refuses silently handling a
terminal-bearing result without that mode, binds the fourth patch hash to exact
Git source bytes, reruns ordinary stage/native-corridor controls and then reruns
terminal qualification. Stored terminal JSON must equal freshly recomputed JSON.
Existing full run/attempt/source identity checks, successful diagnostic status,
false physical acceptance and recursive rejection of symlinked downloaded
evidence remain in place. Absolute hosted witness prefixes are not required to
match the local moved-artifact path; exact case/stage/phase/file suffixes are,
which preserves portability without guessing run identity.

Independently executed in the project venv:

```sh
PYTHONPATH=tools:test_internal pytest -q tools/compile/tests/test_route_force_repair.py tools/autonomy/tests/test_repair_evidence.py
```

**133 passed in 0.86 s**, no skips. Focused coverage includes terminal API/path
separation and permission handoff, original native-error propagation, failed raw
ledger before terminal interpretation, completion/malformed-schema/identity
failure, explicit adapter mode, exact fourth-patch provenance and re-audit of
stored terminal results. These tests include mocked schema audits and therefore
do not replace the pending real parser/hosted terminal qualification.

Reviewed SHA256:

- Runner: `25c3874b36824b8044dc358cb18addc7179d69e5d0ccf1317d66c92e97c649bb`.
- Portable auditor: `8840dfc49ac7363ee41c1767b2da16fdb6ed032865ceab57e9efa0ca09d32862`.

Actual native execution, completion witnesses, all six parsed terminal joins and
source/control identities still require inspecting the selected hosted result.
No collector test count or build launch establishes that outcome.
