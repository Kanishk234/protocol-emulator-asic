# TRIPWIRE: immediate priorities and capability restoration

## Recommendation

For the immediate next step, strengthen the submission on the hardware that
already closes timing. This does **not** mean abandoning capability restoration.

Calling a second PULSE unit a “small hardware extension” understates the
uncertainty. It is plausible, but its incremental area, routability and timing
have not been measured on the qualified design.

## Suggested sequence

1. **Finish one demanding end-to-end showcase**, starting with the I2C memory
   target. Validate its deadlines, independent interoperability and resource usage.
2. **Use that workload to identify the most valuable missing resource.** Does it
   need another lane, memory offload or another advanced pin unit?
3. **Run one hardware experiment on a separate branch**, retaining the qualified
   design as the fallback.

The immediate work is more than adding demos. It includes fixing the ACK setup
checker, establishing timing bounds and testing recovery behavior.

## Parallel hardware feasibility study

If undertaking a hardware experiment alongside submission work, investigate
**PULSE capability on a second pin unit** first.

- Measure added area and routing/timing impact before committing to adoption.
- Optional pin-unit features are currently grouped together; adding PULSE alone
  may require separating their implementation controls.
- Pair the extension with a specific simultaneous workload that the current chip
  cannot perform. Do not add it solely to increase the feature count.
- Preserve existing functionality and rerun appropriate verification and physical
  qualification. No claim is made that the extension fits or retains closure.

## Baseline context

This recommendation follows the November 18, 2026 review of upstream main at
`f1dbbaf5dd0e0cf67d507ecd1a9f3d619fe42d72`.

The qualified physical baseline uses 8×4 CMOS5L tiles, two lanes, four pin units
(U0 full; U1–U3 lean), 512×16 SRAM and a 20 ns clock. Official run
[44189196098](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44189196098)
passed under its documented SRAM signoff policy. The worst reported functional
setup reserve is approximately 163 ps at the slow corner; this is not a guarantee
that any hardware extension will retain closure.

The ACK checker issue identified in that review can overstate setup time by
retaining the first SDA-low observation even when SDA returns high before SCL
rises. That is a reproduced test-oracle weakness, not evidence of an observed
chip failure. Check whether upstream has fixed it before starting duplicate work.

This document is a recommendation and handoff, not an architectural approval or
an instruction to merge, replace the baseline or adopt an unqualified extension.
