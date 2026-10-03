# Phase 2: building and fitting the chip

**Status:** in progress (updated 2026-10-03). The current 2-lane, 4-pin-unit R4 build is a measured candidate, not a team decision on final chip size. The plan and checklist are in [`PHASE2_RTL_CORE.md`](../design/phases/PHASE2_RTL_CORE.md).

## The goal

Turn the written design into Verilog, compare it against the independent software model clock by clock, and make a real 6x4 chip layout that keeps the 20 ns clock and protocol features.

## What we've done

- Built the chip's lanes, shared data fabric, SRAM routine memory, host interface, and configurable pin units.
- Compared the R4 candidate against the software model for 1,000,000 clocks with no mismatches. Two deliberate RTL bugs were detected by the injection checks.
- Passed the UART, SPI, and I2C L3 suite on exact candidate RTL `3393eea9a58c5cad9077cc360a8515d0e5ec8284` under both Icarus and Verilator, and on its hardened gate-level netlist under Icarus 13. All four L3 cases passed with reference-model and sigrok checks on RTL and passed again on the hardened netlist. See [RTL unit run 36799356039](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799356039) and [gate-level run 36952644578](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36952644578).
- Expanded `test_internal/chip/test_l3.py` from twelve to 22 cases to cover PS/2, 1-Wire, SWD, JTAG, SMBus, HDLC, LIN, CAN and IR NEC repeat reception on the same R4 candidate. All ten additions pass under Icarus and Verilator in direct reference-model checks. The sigrok-enabled unit and hardened-netlist workflows exposed two assertion mismatches: sigrok reports the 1-Wire `Read ROM` command but not the slave ROM bytes, and labels LIN's six-bit frame ID separately from the protected ID. The RTL/reference checks had passed. The assertions are corrected locally; focused 1-Wire and LIN tests pass on both simulators with sigrok skipped. CI sigrok and hardened-netlist reruns are pending. The IR test also exposed uninitialized SRAM scratch words in `ir_nec.trw`; the program now clears them before receiving edges, recorded as bug #58. See [`PHASE2_PROTOCOL_COVERAGE.md`](../reports/PHASE2_PROTOCOL_COVERAGE.md).
- Full hardening run [37037880327](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37037880327) used `GRT_ADJUSTMENT=0.16` on the unchanged candidate, completed global routing with zero overflow, then timed out in detailed routing at 330 minutes. DRT had 1,246 spacing/short violations remaining after 13 completed optimization rounds; the timeout skipped precheck and gate-level tests, and the run produced no final routed timing, GDS signoff, or viewer. The earlier DRT-only continuation [36951141285](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36951141285) completed in 3 h 45 min from a checkpoint before antenna repair, so it does not establish that the post-antenna netlist can route. See [`PHASE2_GDS_EXPERIMENTS.md`](../reports/PHASE2_GDS_EXPERIMENTS.md).
- The expanded 22-case L3 suite on the earlier hardened netlist from run 36799356107 failed only at the two sigrok assertions in workflow [37101678657](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37101678657). The assertions are fixed locally and require a CI rerun. This netlist matches the candidate RTL but misses the project's slow-corner timing and congestion goals.
- Post-antenna DRT continuation [37102837764](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37102837764) validated the stage 43 checkpoint, then timed out after 330 minutes with 277 route markers remaining. It began with 32,500, completed 35 optimization rounds, and partially entered round 36. The resolved flow had `OPENROAD_THREADS=null`; the continuation workflow now has an explicit four-thread setting prepared for a same-checkpoint replay. This route-only test does not constitute full signoff.
- The WS2812 test exposed that byte-at-a-time host input could not maintain the wire rate. The firmware now sends each LED's 24 GRB bits as two 12-bit length-in-token words and uses legal upper-tolerance timings; the updated program passes the candidate RTL pad decoder.
- The IR NEC test exposed that decoder state in SRAM was never initialized. The firmware now clears its last-edge timestamp, bit accumulator, frame count and leader flag before accepting pin edges; this also removes simulator dependence on power-up contents.
- A timing audit found the standalone whole-chip pre-layout STA helper false-pathed every latch output, hiding a legal live pin-configuration-to-state path under D-066. The helper now keeps latch outputs timed. On the exact R4 candidate, pre-layout slow slack is +3.344 ns from U0 config word 0 bit 1 to U0 TX `eq[14]`, versus +4.828 ns on the SRAM path with the old false path. This has no placement or route parasitics and is not signoff timing. The bug is logged as #57.
- The bug ledger is complete through entry #59, including the new L3 decoder-assertion issue, which is fixed locally but awaits CI rerun.
- Completed a standard full-chip GDS workflow on candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284`: 2 lanes, 4 pin units, U0 full, 20 ns clock, 56% placement target. The counts are experimental, not approved final hardware counts.
- The workflow's GDS, Tiny Tapeout precheck, gate-level test, and viewer jobs all passed. Detailed routing reached zero route DRC in 3 h 15 min; precheck passed all 9 checks; all 4 gate-level tests passed; the viewer rendered the actual design. See [run 36799356107](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799356107) and the measured values in [`AREA.md`](../reports/AREA.md).
- Main `test`, `docs`, and `lint` pass on the expanded-test commits through `2a3845b`; the latest runs are 37102835114, 37102835372, and 37102835113. Unit runs 37102835070 and 37103768779 failed on the same 1-Wire and LIN sigrok assertions. In 37103768779, the tripsim/model job passed while both RTL simulator jobs failed on those annotations. The local test fix needs a new green `unit` run before this gate is satisfied.

## What we found

An earlier full hardening completed detailed routing in 3 h 15 min and passed its downstream physical checks, but it had 821 global-route overflow and −10.698 ns slow-corner setup slack. The later 16% flow experiment got zero GRT overflow, but did not complete detailed routing or any final signoff checks.

The latest GRT-adjustment run shows that zero global-route overflow alone does not guarantee that detailed routing completes. The full run's DRT input had 33,755 instances after antenna repair inserted 141 diodes and jumpers. Its post-antenna continuation reached 277 route markers after 35 complete optimization rounds, then timed out before saving a final route state. The only timing artifact from that hardening is pre-DRT typical-corner timing (setup slack +7.817 ns, hold slack +0.171 ns); it has no routed parasitics or slow/fast signoff, so it does not establish the 20 ns timing gate. The last fully routed result's worst slow path starts at U0's `idle` configuration latch and ends at `dropped[16]`, with −10.698 ns slack; that live configuration path remains timed under D-066.

## What's left

- Trace and improve the `idle`-to-`dropped` timing path without changing protocol behavior, allowing a false path, or relaxing the 20 ns clock.
- Use the congestion map to target the Metal3 hotspots; evaluate one hardware or flow change per hardening.
- Obtain team sign-off on the agreed L3 scope.
- Replay the validated post-antenna checkpoint with explicit `OPENROAD_THREADS=4`; the previous DRT continuation ran with this unset. This tests routing runtime/convergence only. A successful replay still needs a complete hardening for all-corner timing, DRC/LVS/antenna, precheck, gate-level tests, and viewer output.
- Push the local L3 assertion correction, rerun `unit` with sigrok, and repeat the 22-case suite on the matching hardened netlist. Later repeat it again on the netlist from a fully passing hardening. The earlier successful GDS run still has 821 global-route overflow and −10.698 ns slow-corner setup slack.
- Restore green `test`, `unit`, `lint`, and `docs` workflows on `main`; test/docs/lint are green, while the latest unit run failed on the two fixed assertions.
- Finish the area/count decision with the team and keep `main`'s CI green through the eventual hardware switch.

## In one line

The real 6x4 candidate now routes and passes the named typical-corner and precheck gates at 20 ns, but congestion and slow-corner timing still need work before Phase 2 can close.
