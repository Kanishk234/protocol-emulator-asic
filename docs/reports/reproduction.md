# Phase 5 clean-source reproduction

**Date:** 2026-09-28. **Environment:** Ubuntu/WSL, Python 3.12.4 in a newly created project venv, Icarus 12.0, Verilator 5.020, Yosys 0.66+179 (OSS CAD Suite 2026-06-29), nextpnr 0.11.1-34 (OSS CAD Suite 2026-09-27), sigrok-cli 0.7.2. The CAD suites and sigrok were already installed on the machine. The pinned tile library was fetched into the export.

**Source:** `git archive HEAD` at 14e7063 extracted to `/tmp/warp-repro.vVyH1n`, with the proposed README and the Phase 5 source files under test copied into that export. A new venv was created there from the candidate `requirements-dev.txt`. This is an isolated source export and fresh venv on the same machine, not a clean machine or container. The working-tree changes still need CI after commit and push.

## Commands and results

| Step | Result |
|---|---|
| `scripts/setup_venv.sh` | Passed in a fresh venv, using the pinned `requirements-dev.txt`; first sandbox attempt could not resolve PyPI, so the rerun used permitted network access. |
| `bash scripts/fetch_nextpnr.sh` | Passed; pinned nextpnr version checked. |
| `scripts/check_all.sh` | Passed in the fresh export: lint, Yosys synthesis sanity, 377 pytest tests, all default protocol RTL suites, 30 idle-fabric chip tests (13 pass, 17 bitstream tests skipped as expected), 2 primitive white-box tests, and the pyuvm shell check. The shell check reported 2,288 transactions, 2,851 response bytes, 228 configuration words, 137 design-side bytes, 0 mismatches and 79/79 coverage bins. |
| UART compile command in README | Passed: 722-word `.wbit`, 29/88 logic cells, 2/2 timers, 2/2 shift registers; nextpnr Fmax estimate 90.71 MHz. |
| `scripts/build_test_bitstreams.sh --check` | Passed: all 11 committed `.wbit` files match fresh builds. |
| `make -C test WARP_FABRIC=rtl` | Passed: 30 tests, 30 pass, 0 fail, 0 skipped, including the six-protocol showcase. The first attempt found BUGS #20; this result is after the fix and a fresh fabric RTL compile. |
| `make -C test_internal/cosim` | Passed: 1 test, 1 pass, 0 fail, 0 skipped. |

## Gaps found and fixed

1. `scripts/fetch_nextpnr.sh` is mode 0644 in the committed tree, so the original README command failed. The README and user guide now invoke it with `bash` (as CI already does).
2. Sigrok-cli could not initialize libusb inside the execution sandbox; the same executable and protocol tests passed outside it. This is an environment restriction, not a design failure.
3. The default idle-fabric run and `WARP_FABRIC=rtl` shared `test/sim_build/rtl`, so the second command reused the first run's executable (BUGS #20). `test/Makefile` now uses separate build paths for `stub` and `rtl`.
4. The README said Python 3.11+, while pinned FABulous 2.2.0 needs 3.12+. The README and agent guidance now state 3.12+ and list sigrok-cli.

## Remaining verification

- Repeat the source export in a clean machine or container to satisfy the phase checklist literally.
- Confirm the same results in CI on the committed Phase 5 changes.
