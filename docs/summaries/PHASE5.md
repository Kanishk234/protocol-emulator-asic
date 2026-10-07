# Phase 5 summary: evidence and documentation

**Status:** in progress (updated 2026-10-07). Evidence and software improvements are grouped into authorized commits; hosted validation is being launched. The README flow and all local checks passed from a source export and fresh venv on the development machine; the phase checklist still asks for a clean machine or container. Separate checkpoint experiments do not close that requirement.

Compact37516794406 now reaches zero native router/antenna violations, but later
physical checks fail. All248 KLayout markers associate with inserted decaps;
the first exclusion attempt left the separate decap selector active. Corrected
37648945387 verifies zero decaps, then reports KLayout0/LVS12/Magic6350.
Magic boxes all overlap plain fillers, and the pinned KLayout pSD deck lacks
that rule. Bounded routing cleanup37652533986 and isolated library screening
investigate the remaining errors. Same-old-wire driver screen37651173629
reduces nine slew failures to zero; fresh physical/configured timing remains open.
Regenerated native LUT netlists pass real SPI-loaded UART and USER_RESET in
37553717299; matched original-LUT resynthesis37553979644 also passes, so the
new primitive alone is not established as the fix. Copied physical views do
not qualify either regenerated mapping. G1 stays frozen. See the
[closure plan](../reports/compact_acceptance_and_competitors.md).

Host capture decoding now handles wrap, quantization and observed overflow
explicitly; checked channel reads distinguish valid zero from empty. Loader
validation rejects negative chunk sizes and truncating fields. These work on
the fallback, with31 local host tests passing and hosted unit37651173601 green.

## Goal
Make WARP's design choice, results, limits and use understandable to a judge, and make the simulation results reproducible from a clean source tree.

## What we did
- Filled the Phase 4 CI run IDs into the claims and evidence report; closed Phase 4 after its `gds`, precheck, `gl_test`, `fabric`, `unit`, `lint`, `test` and `docs` runs passed.
- Wrote the user guide, evidence report and prior-art comparison, and updated the README and Tiny Tapeout datasheet for the frozen G1 chip.
- Added an independent shell transaction model and a pyuvm environment. Local seed 1 compared 2,288 SPI transactions, 2,851 response bytes, 228 configuration words and 137 design-side bytes with no mismatches; its coverage closure reached 79/79 bins. Added the depth-2 and depth-4 F3 FIFO proof, which passes locally with `abc pdr`.
- Reproduced the README from a clean export of commit 14e7063 with the Phase 5 source files under test copied in. The fresh venv run passed all 30 fabric RTL chip tests, the UART co-simulation, a deterministic rebuild of all 11 bitstreams and the candidate `check_all.sh` including pyuvm. The run exposed a non-executable fetch command, a sandbox-only sigrok initialization failure, and a stale simulator build reused when switching from the idle fabric to the fabric RTL (BUGS #20). The README now invokes the fetch command with `bash`; the Makefile separates those simulator builds.

## What we found
- The pinned FABulous release requires Python 3.12 or newer; the README and agent guidance now say so.
- All Phase 4 tests reached green CI, but the new F3 and pyuvm checks still need CI evidence after the current changes are committed and pushed.
- The evidence report still needs a final pass over local-only measurements and their reproducible source references before its checklist item can be ticked.

## October 5 milestone

The unchanged fallback can now run UART and an independent event monitor
together, and a second bitstream adds externally timed corruption of selected
TX bits. The latter uses38/88 logic cells. Real SPI-loaded RTL and synthesized
shell tests pass normal RX/errors, injected corruption, recovery, monitoring,
reset and STOP parking. These remain local RTL-fabric tests without new CI,
SDF or silicon evidence; exact reports are `docs/reports/g1_uart_monitor.md`
and `docs/reports/g1_uart_fault_monitor.md`.

Compiler seed, control-mapping and FSM screens retain default settings;
no overall improvement is established. Strict port checking and structured
failure diagnostics make mistakes easier to find, including invalidating
stale success reports. Compiler/board unit checks pass315tests in local run
`compiler_host_unit_final_20261005`. Scratch compact hardware remains a separate
unpromoted experiment; its routing failures do not block these G1 improvements.

Compiler reports now bind listed sources/models to the emitted image with
fingerprints, and an audit checks those files plus image CRC/architecture/length.
Actual tools reject an owned source changed during compilation. This improves
evidence traceability without claiming hermetic reproduction or chip timing.
The historical G1 CI archive was searched for missing original tile parasitics;
it contains chip-level extraction only, so that reproduction gap remains open.
Details: `docs/reports/compiler_provenance.md` and `docs/reports/reproduction.md`.

G1 also runs UART alongside a two-entry soft timestamp queue. Its83-cell
version records one-clock ticks with64-clock wrap; an85-cell option gives
four-clock ticks with256-clock wrap. Real loaded RTL and synthesized-shell
tests cover concurrent TX/capture, quantization/wrap, overflow/order,
backpressure, RX, reset and STOP. These local results preserve the same
RTL-fabric/no-SDF limits and do not replace the open clean-machine/CI gates.
Evidence: `docs/reports/g1_uart_capture.md`.

## What's left
- Repeat in a clean machine or container to satisfy the checklist literally.
- Finish the numerical-source audit in `docs/EVIDENCE.md` and run CI for the new verification and documentation changes.
- Tick the remaining Phase 5 exit items only after that evidence exists.

## One-line takeaway
The frozen chip's Phase 4 claims now have green CI evidence; Phase 5 is turning the local verification and documentation into a reproducible, reviewable submission package.
