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

## October 5 routed primitive timing artifact gap

A fresh path-audit attempt finds the historic PRIM2T2S run netlist/SPEF path
no longer present (`build/primitive_path_audit_20261005/audit.log`). The
committed G1 primitive-tile netlist exists, but matching extracted SPEF is
not available locally. This does not invalidate the recorded historical
comparison; it prevents reproducing it from the current local artifacts.
No fresh routed timing pass is claimed. Restore matching archived artifacts
or rebuild the same tile with pinned tools before repeating the check.
`tools/timing/tile_check.sh` now checks for both artifacts explicitly and
fails with recovery instructions. Netlist-only timing is not substituted for
routed parasitics. This is another open item in the phase5 reproduction audit.

Follow-up: newer experimental PRIM2T2S netlists/SPEFs do exist, but none of
the completed local run netlists is byte-identical to committed G1. The default
audit previously chose the newest experiment. It now selects only matching
netlists (BUGS#29); explicit variants require
`WARP_TIMING_ALLOW_VARIANT=1` and are labeled experimental. Byte differences
are not proof of semantic differences, but no equivalence has been established
for substituting those artifacts. The missing evidence is the matching G1
archive, not every PRIM2T2S parasitic file. Default rejection is recorded in
`build/primitive_path_audit_20261005/default_missing_artifact_check.log`.

## Historical CI archive search, October 5

Queried historical G1 run36342012141 and downloaded unexpired `GDS_logs`
artifact10939348491 to an ignored local archive. Its909members include only
chip-level `tt_um_warp.nom.spef` (stage/final copies), with no PRIM2T2S netlist
or extracted tile parasitics. This archive cannot refresh the missing original
primitive-tile comparison. Inventory evidence:
`build/g1_timing_archive_audit_20261005.txt`; archive
`build/g1_gds_logs_36342012141.zip`. No remote/history change or substituted
experimental timing evidence. Further restoration must use the original
local tile archive or a separately identified matching source/artifact set.

## Fresh hosted README reproduction prepared, October7

Separate clean_reproduction workflow starts with a pristine checkout, fresh
project venv and no reused build or simulator output. Only pinned binary tools
are cached. It records the README hash and exact command line references,
checks actual tool/package versions, then executes check_all, deterministic
bitstream rebuild comparison, the documented UART compile plus report audit,
the complete actual-loaded RTL-fabric suite and source-versus-fabric cosim.
XML validation rejects empty suites, failures/errors and skipped loaded/cosim
cases; known default idle/UART-divider skips remain explicitly limited to the
initial check_all suites. Tracked source must remain unchanged.

Standard hosted job190min, verification step180min, with individual command
bounds and retained incremental result/log/runtime/XML evidence for3days.
This targets the open README reproduction gate; it does not replace physical
checks, SDF/native mapping evidence or every CI parameter variant. No checklist
box is ticked until an actual successful run is inspected. Missing historic
G1 tile parasitics remain a separate unresolved timing reproduction gap.
