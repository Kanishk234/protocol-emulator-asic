# R1 exact mapped LUT physical preflight

D106 freezes the audited LUT cell netlist from39696703659, including438configuration latches and210signal bits. The new preparer exports it without synthesis, checks source identity, and generates a pin order from a disposable copy. Original model hashes must remain exact. Scalar carry-port print metadata is normalized while cell/port connectivity is asserted unchanged. The physical API's single-tile pin format is converted explicitly to the pinned I/O adapter's format.

Two fixed widths219.84and154.08µm at185.22µm height use the same mapped cells, margins and I/O policy. This is a floorplan/pin hypothesis, not a chip-outline decision. Pinned LibreLane stages import the netlist, create floorplan rows, connect power metadata and place signal pins. Native checks require all210ports with positive nonoverlapping same-layer rectangles inside the die, exact cell counts/438latches, and cell area no larger than the actual placeable core. Six admission-check tests pass locally; final input preparation succeeds under build/r1_physical_prepared_native.

No local Docker/native physical run is claimed. Hosted workflow pending. CLOCK_PORT=null and absence of placement/PDN/routing stages mean no timing, power-grid connectivity, routed/signoff or chip-fit acceptance. Per-column PG phase, actual routing/buffers, loaded mapped behavior and real-shell integration remain later gates. No full-chip hardening attempt used.


## First native run and bounded adapter correction

39986366251 at01604c9 passes source preparation and six checker cases, then imports the frozen cells and completes floorplan setup. Strict custom I/O placement stops before its result because the generated policy names UserCLK/UserCLKo although DisableUserCLK is true. Narrowed geometry is not reached; this is a pin-policy compatibility failure, not an architectural fit result. Native artifacts retained under build/r1_physical_hosted. BUG119.

The owned adapter now removes only those two exact disabled/absent entries, validates every other policy pattern against the full mapped interface, and requires each real pin once. Eight focused checker cases pass; fixed local preparation preserves original model hashes and records exactly those two removals. Native unmatched checks remain both. Retry uses identical cells, footprints, margins and tools; no budget/seed/graph change.


## Second native run and mapped-cell validation

39987539298 at4e1934e imports/floorplans the same reference-width cells and matches the real pin names, then the legacy I/O placer cannot fit the32-bit frame-data group into its31-slot equal-sized side segment. The new API emitted per-bus groups; overall side capacity has not failed. BUG120 merges only identical-policy groups into one ordered side group, preserving bus/pattern order. Differing spacing policies are rejected, not discarded. Nine admission tests now pass,81combined local checks pass. Cells/footprints/tools remain unchanged for retry.

Optional configured smoke replaces the LUT tile module with its exact exported mapped netlist (SHA b743335546eb7cbecd98d9fd129a26855e900ca4f868caea2f5a43167faf6b1a), so all16LUT tile instances use actual CMOS5L cell models. Initial Icarus12 fails on PDK delayed timing-check nets; documented Icarus13 backend binding fixes this without model/PDK edits (BUG121). Local build/r1_mapped_lut_smoke_iv13/results.xml has1executedPASS for the identical loaded UART TX/RX+SPI/backpressure/rate test. Source/PDK/image hashes retained. Primitive and I/O tiles remain RTL; this is mixed mapped/RTL functional evidence, not whole-fabric gate-level, SDF, management-shell or physical acceptance. Hosted physical workflow now retains this independent check even if native pin geometry fails.
