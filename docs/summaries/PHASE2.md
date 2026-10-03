# Phase 2: building and fitting the chip

**Status:** in progress (updated 2026-10-03). The current 2-lane, 4-pin-unit R4 build is a measured candidate, not a team decision on final chip size. The plan and checklist are in [`PHASE2_RTL_CORE.md`](../design/phases/PHASE2_RTL_CORE.md).

## The goal

Turn the written design into Verilog, compare it against the independent software model clock by clock, and make a real 6x4 chip layout that keeps the 20 ns clock and protocol features.

## What we've done

- Built the chip's lanes, shared data fabric, SRAM routine memory, host interface, and configurable pin units.
- Compared the R4 candidate against the software model for 1,000,000 clocks with no mismatches. Two deliberate RTL bugs were detected by the injection checks.
- Passed the UART, SPI, and I2C L3 suite on exact candidate RTL `3393eea9a58c5cad9077cc360a8515d0e5ec8284` under both Icarus and Verilator, and on its hardened gate-level netlist under Icarus 13. All four L3 cases passed with reference-model and sigrok checks on RTL and passed again on the hardened netlist. See [RTL unit run 36799356039](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799356039) and [gate-level run 36952644578](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36952644578).
- Expanded `test_internal/chip/test_l3.py` from twelve to 22 cases to cover PS/2, 1-Wire, SWD, JTAG, SMBus, HDLC, LIN, CAN and IR NEC repeat reception on the same R4 candidate. All ten additions pass under Icarus and Verilator. The existing tripsim IR frame/repeat regression also passes after the test exposed uninitialized SRAM scratch words in `ir_nec.trw`; the program now clears them before receiving edges, recorded as bug #58. These new cases have RTL evidence only; they have not run with sigrok in CI or on a hardened netlist. The original twelve cases remain the only expanded suite with hardened-netlist evidence (run 37051434072). See [`PHASE2_PROTOCOL_COVERAGE.md`](../reports/PHASE2_PROTOCOL_COVERAGE.md).
- Full hardening run [37037880327](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37037880327) used `GRT_ADJUSTMENT=0.16` on the unchanged candidate, completed global routing with zero overflow, then timed out in detailed routing at 330 minutes. DRT had 1,246 spacing/short violations remaining after 13 completed optimization rounds; the timeout skipped precheck and gate-level tests, and the run produced no final routed timing, GDS signoff, or viewer. The earlier DRT-only continuation [36951141285](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36951141285) completed in 3 h 45 min from a checkpoint before antenna repair, so it does not establish that the post-antenna netlist can route. See [`PHASE2_GDS_EXPERIMENTS.md`](../reports/PHASE2_GDS_EXPERIMENTS.md).
- The expanded 22-case L3 suite is running on the earlier hardened netlist from run 36799356107 in workflow [37101678657](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37101678657). It matches the same RTL candidate and can establish functional coverage, but that layout still misses the project's slow-corner timing and congestion goals.
- Post-antenna DRT continuation attempt [37102555758](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37102555758) stopped at artifact download because the workflow expected the wrong name. The artifact exists as `GDS_logs-37037880327`; the workflow has been corrected and needs a retry. This route-only test would not constitute full signoff.
- The WS2812 test exposed that byte-at-a-time host input could not maintain the wire rate. The firmware now sends each LED's 24 GRB bits as two 12-bit length-in-token words and uses legal upper-tolerance timings; the updated program passes the candidate RTL pad decoder.
- The IR NEC test exposed that decoder state in SRAM was never initialized. The firmware now clears its last-edge timestamp, bit accumulator, frame count and leader flag before accepting pin edges; this also removes simulator dependence on power-up contents.
- A timing audit found the standalone whole-chip pre-layout STA helper false-pathed every latch output, hiding a legal live pin-configuration-to-state path under D-066. The helper now keeps latch outputs timed. On the exact R4 candidate, pre-layout slow slack is +3.344 ns from U0 config word 0 bit 1 to U0 TX `eq[14]`, versus +4.828 ns on the SRAM path with the old false path. This has no placement or route parasitics and is not signoff timing. The bug is logged as #57.
- The bug ledger is complete through entry #58, including issues that still need fixes or experiments; this closes its Phase 2 checklist item.
- Completed a standard full-chip GDS workflow on candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284`: 2 lanes, 4 pin units, U0 full, 20 ns clock, 56% placement target. The counts are experimental, not approved final hardware counts.
- The workflow's GDS, Tiny Tapeout precheck, gate-level test, and viewer jobs all passed. Detailed routing reached zero route DRC in 3 h 15 min; precheck passed all 9 checks; all 4 gate-level tests passed; the viewer rendered the actual design. See [run 36799356107](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799356107) and the measured values in [`AREA.md`](../reports/AREA.md).
- Main test, docs, lint, and unit passed on `3720983` (runs 37066391043, 37066391070, 37066391039, and 37066391060). New runs for the pushed expanded tests and evidence at `a9b9f26` are in progress (37101626363, 37101626299, 37101626351, and 37101626314).

## What we found

An earlier full hardening completed detailed routing in 3 h 15 min and passed its downstream physical checks, but it had 821 global-route overflow and −10.698 ns slow-corner setup slack. The later 16% flow experiment got zero GRT overflow, but did not complete detailed routing or any final signoff checks.

The latest GRT-adjustment run shows that zero global-route overflow alone does not guarantee that detailed routing completes. Its remaining 1,246 DRT markers were mostly on Metal2 (1,042: 697 shorts and 345 spacing markers). Antenna repair had inserted 141 diodes and jumpers before DRT. The only later STA artifact is pre-DRT typical-corner timing (setup slack +7.817 ns, hold slack +0.171 ns); it has no routed parasitics or slow/fast signoff, so it does not establish the 20 ns timing gate. The earlier successful route's slow path from U0's `idle` configuration latch to `dropped[16]` remains a known timed path under D-066.

## What's left

- Trace and improve the `idle`-to-`dropped` timing path without changing protocol behavior, allowing a false path, or relaxing the 20 ns clock.
- Use the congestion map to target the Metal3 hotspots; evaluate one hardware or flow change per hardening.
- Obtain team sign-off on the agreed L3 scope.
- Retry the corrected continuation from run 37037880327 and check whether detailed routing completes with zero violations inside the limit.
- Review expanded L3 gate-level run 37101678657 against the earlier matching candidate netlist, then repeat the full suite against the netlist from a passing hardening. The earlier successful GDS run still has 821 global-route overflow and −10.698 ns slow-corner setup slack.
- Review the pushed main `test`, `unit`, `lint`, and `docs` runs, including sigrok-enabled cases for the new protocols.
- Finish the area/count decision with the team and keep `main`'s CI green through the eventual hardware switch.

## In one line

The real 6x4 candidate now routes and passes the named typical-corner and precheck gates at 20 ns, but congestion and slow-corner timing still need work before Phase 2 can close.
