# Baseline software audit, 2026-10-15

The frozen G1 remains the working baseline; compact routing improvements are
experimental. Phase 5 still has unchecked evidence/report completeness, final CI
and phase-summary exit items. This audit does not close those gates or change
hardware, architecture, generated sources, template workflows or protocol RTL.

## Concrete transport robustness repair

`tools/board/warp.py::Warp.xfer` previously asserted CS before any pin I/O and
released it only on normal completion. A transport exception from `write_ui`,
`read_uo` or `wait` could leave CS low. A later command could then continue the
interrupted transaction rather than start a new opcode. The earlier partial
command may already have changed device state.

The transfer now attempts CS-high/SCK-low/MOSI-low idle cleanup on every
exception, including interruption, preserves FAB_IN values, and re-raises the
original exception even if cleanup also fails. It never retries a command or
claims that the earlier command was rolled back. Cleanup remains best effort
when the transport itself cannot drive pins; callers must recover their
transport/device state before further operation in that case.

Regression tests inject an exception before each of the 86 individual
read/write/wait operations of a two-byte transaction, from CS assertion through
termination. They require idle cleanup, unchanged FAB_IN, original exception
identity, no command retry, and a successful fresh transaction afterward. A
separate case verifies that a second cleanup error does not mask the original.
These are software pin-adapter tests, not board measurements or loaded-chip
fault-injection evidence.

Local validation used the project venv, without EDA:

- `python -m pytest -q tools/board/tests/test_warp.py`: 378 passed in 1.07 s.
- `python -m pytest -q tools/board/tests tools/host/tests`: 542 passed in 2.98 s.

Suggested BUGS entry: **Python board SPI exception retains active transaction**.
Symptom: pin transport exception leaves CS asserted and the next operation can
continue the old command. Root cause: termination occurred only on the successful
path. Coverage: exhaustive operation-boundary exceptions plus secondary cleanup
failure in `tools/board/tests/test_warp.py`.

## Fresh cloud baseline priorities

Read-only GitHub inspection found current `6a44252e6c6ab253a033aa7f160d6bd95a62eaad`
baseline workflows successful: unit38676688256, test38676688290,
lint38676688348, docs38676688261 and fabric38676688411. Diagnostic
route_trace38676688402 also succeeded as a collector; that status alone says
nothing about physical acceptance.

After landing current software changes, a fresh manual `clean_reproduction.yaml`
run is the highest-value broader baseline check: it rebuilds from a fresh hosted
checkout and retains strict loaded/cosim result evidence. Current push-triggered
unit/fabric/test checks should run first; dispatch formal only when its bounded
property freshness is needed. Do not launch a redundant full GDS merely because
software or agent instructions changed. Continue physical work only from the
authenticated control and measured trace findings.

One independent infrastructure weakness was repaired after coordinator review:
`unit.yaml` protocol loops use `! grep -q failure results.xml`. Missing XML makes
grep exit 2, which the negation converts to success; empty or skipped suites and
`<error>` records also need strict checks. All eight loops now call
`tools/autonomy/check_xml.py`, which requires at least one testcase, rejects
failure/error/skipped elements and nonzero or malformed corresponding suite
counters, and rejects absent/malformed XML. Multi-suite results are accepted and
an optional minimum-case count can strengthen particular callers. Both unit jobs
now install and run Python packages through a project `.venv`.

The reusable helper has 24 passing focused tests, including CLI execution from
a protocol-like working directory, missing/empty/error/skipped XML, contradictory
suite counters and minimum-case rejection. Actual hosted execution remains
pending the next push; no cloud success is claimed from these local fixtures.
