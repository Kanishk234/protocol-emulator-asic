# Phase 2: building and fitting the chip

**Status:** in progress (updated 2026-10-02). The current 2-lane, 4-pin-unit R4 build is a measured candidate, not a team decision on final chip size. The plan and checklist are in [`PHASE2_RTL_CORE.md`](../design/phases/PHASE2_RTL_CORE.md).

## The goal

Turn the written design into Verilog, compare it against the independent software model clock by clock, and make a real 6x4 chip layout that keeps the 20 ns clock and protocol features.

## What we've done

- Built the chip's lanes, shared data fabric, SRAM routine memory, host interface, and configurable pin units.
- Compared the R4 candidate against the software model for 1,000,000 clocks with no mismatches. Two deliberate RTL bugs were detected by the injection checks.
- Passed the UART, SPI, and I2C L3 suite on exact candidate RTL `3393eea9a58c5cad9077cc360a8515d0e5ec8284` under both Icarus and Verilator, and on its hardened gate-level netlist under Icarus 13. All four L3 cases passed with reference-model and sigrok checks on RTL and passed again on the hardened netlist. See [RTL unit run 36799356039](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799356039) and [gate-level run 36952644578](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36952644578).
- Extended local candidate RTL checks to eleven protocol cases: UART and MIDI; SPI and I2C controllers and targets; DMX512-A; WS2812; DShot150/300/600/1200; and servo PWM. All eleven passed locally across Icarus and Verilator. New cases still need CI sigrok where applicable and hardened-netlist runs. See [`PHASE2_PROTOCOL_COVERAGE.md`](../reports/PHASE2_PROTOCOL_COVERAGE.md).
- A DRT-only continuation from the 16% GRT checkpoint completed in 3 h 45 min with zero final router violations (run 36951141285). It skipped post-route STA/parasitic extraction and all downstream signoff checks, so it does not establish timing closure or a green GDS workflow. The next physical run should be a full hardening at 16% with all hardware inputs fixed; see [`PHASE2_GDS_EXPERIMENTS.md`](../reports/PHASE2_GDS_EXPERIMENTS.md).
- The WS2812 test exposed that byte-at-a-time host input could not maintain the wire rate. The firmware now sends each LED's 24 GRB bits as two 12-bit length-in-token words and uses legal upper-tolerance timings; the updated program passes the candidate RTL pad decoder.
- The bug ledger is complete through entry #55, including issues that still need fixes or experiments; this closes its Phase 2 checklist item.
- Completed a standard full-chip GDS workflow on candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284`: 2 lanes, 4 pin units, U0 full, 20 ns clock, 56% placement target. The counts are experimental, not approved final hardware counts.
- The workflow's GDS, Tiny Tapeout precheck, gate-level test, and viewer jobs all passed. Detailed routing reached zero route DRC in 3 h 15 min; precheck passed all 9 checks; all 4 gate-level tests passed; the viewer rendered the actual design. See [run 36799356107](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799356107) and the measured values in [`AREA.md`](../reports/AREA.md).

## What we found

The layout is physically routable at this size and finishes within the Phase 2 detailed-routing time target. LVS, antenna, KLayout DRC, and hold checks pass. Typical-corner setup has no violating paths.

The result still has two serious limits: global routing reports 821 overflow, mostly on Metal3, and slow-corner setup is −10.698 ns with 1,132 violating paths. The worst slow path starts at U0's `idle` configuration latch and ends at `dropped[16]`. That path must stay timed because live reconfiguration is part of the design contract (D-066). The workflow's green status therefore records a useful milestone, not all-corner timing closure or Phase 2 completion.

## What's left

- Trace and improve the `idle`-to-`dropped` timing path without changing protocol behavior, allowing a false path, or relaxing the 20 ns clock.
- Use the congestion map to target the Metal3 hotspots; evaluate one hardware or flow change per hardening.
- Obtain team sign-off on the agreed L3 scope.
- Run the expanded L3 suite with sigrok in CI and on the matching hardened netlist; add tests for remaining model-verified programs before claiming RTL or GDS coverage for them.
- Complete a full hardened run at the 16% GRT adjustment with acceptable routing and timing evidence; the prior successful GDS run still has 821 global-route overflow and −10.698 ns slow-corner setup slack.
- Finish the area/count decision with the team and keep `main`'s CI green through the eventual hardware switch.

## In one line

The real 6x4 candidate now routes and passes the named typical-corner and precheck gates at 20 ns, but congestion and slow-corner timing still need work before Phase 2 can close.
