# Phase 5 summary: evidence and documentation

**Status:** in progress (2026-09-28). The evidence, tests and reproduction fixes are in the working tree; CI has not run on them yet. The README flow and all local checks passed from a source export and fresh venv on the development machine; the phase checklist still asks for a clean machine or container.

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

## What's left
- Repeat in a clean machine or container to satisfy the checklist literally.
- Finish the numerical-source audit in `docs/EVIDENCE.md` and run CI for the new verification and documentation changes.
- Tick the remaining Phase 5 exit items only after that evidence exists.

## One-line takeaway
The frozen chip's Phase 4 claims now have green CI evidence; Phase 5 is turning the local verification and documentation into a reproducible, reviewable submission package.
