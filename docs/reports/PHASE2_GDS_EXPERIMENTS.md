# Phase 2 fit and timing experiments

**Status checked:** 2026-09-30 (America/Chicago)
**Candidate under test:** `spike/r4-floorplan` at `3393eea9a58c5cad9077cc360a8515d0e5ec8284`
**Candidate shape:** 2 lanes, 4 pin units, U0 full; 20 ns clock; 56% placement density

This report tracks the experiments intended to get a complete Phase 2 hardening without lowering the 20 ns clock target or removing UART, SPI, I2C, or other implemented protocol behavior. The 2-lane/4-unit shape is the current protocol-floor candidate under test; these measurements do not approve the final hardware counts. The R4 branch uses D-056's 0.10 ns hold uncertainty for branch measurement (setup remains 0.25 ns); adopting that setting on `main` remains conditional on full hold and gate-level evidence. See [Phase 2 exit criteria](../design/phases/PHASE2_RTL_CORE.md) and [the related decisions](../DECISIONS.md).

## Constraints for the experiments

- Keep `CLOCK_PERIOD` at 20 ns and preserve the supported protocol behavior and firmware interface.
- Keep live pin reconfiguration legal. Under D-066, configuration latch-to-state paths remain timed; do not add a false-path exception.
- Change one hardware or flow variable per hardening and compare timing, global-route congestion, route runtime, and signoff together.
- Treat branch-only floor and hold settings as measurements, not approval to change final counts or move settings to `main`.
- Do not push hardware files while a hardening is running; the GDS path filter may cancel it.

## Experiment record

| Experiment | Controlled idea | Result and evidence | Status / decision |
|---|---|---|---|
| Placement density, 59% → 56% (D-067) | Reduce placement target while preserving the protocol-floor resources and 20 ns clock; see whether spreading the cells lowers routing congestion. | The 59% run [36526332067](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36526332067) reported 1,503 global-route overflow and WNS −0.934 ns typical / −13.336 ns slow. The later 56% candidate reported 143 overflow, but its RTL revision differs (`9138ee6` vs. `cfc41e1`), so the change cannot be credited to density alone. At 56%, the pre-cache run [36605194167](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36605194167) had 1,090 overflow; the carrier-cache run [36656975727](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36656975727) had 143 overflow but timed out during detailed routing. | Keep 56% for the current candidate. The evidence is confounded across RTL revisions and lower density may worsen wire delay. No new density change is justified by these results. |
| Explicit OpenROAD threads = 4 | Test whether an explicit thread count avoids the invalid `openroad -threads None` invocation and reduces route time, with the `cfc41e1` candidate and 56% density. | The isolated four-thread hardening [36759109179](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36759109179) completed in about 3 h 48 min, including about 2 h 44 min of detailed routing. It still reported 143 global-route overflow (142 M3), setup WNS −2.213 ns typical / −15.684 ns slow, and max-slew/max-cap violations. Antenna and LVS passed; detailed-route DRC reported 0, but Magic reported 57,924 SRAM-exception markers, KLayout DRC was skipped, and 10 illegal overlaps remained. | Faster route time alone did not meet signoff. The run is diagnostic, not a passing hardening; see its artifact under `build/ci/r4/thread4/`. |
| Five local RTL rewrites | Screen fabric one-hot selection, indexed selection, RX edge factoring, parallel saturating-counter toggles, and carrier-output Boolean factoring using mapped area and pre-layout STA, while keeping D-066 paths timed. | All five worsened the measured area/slack tradeoff against baseline area 390,666.74 µm² and slow slack +2.717 ns: one-hot 391,177.19 / +1.004 ns; indexed 392,077.93 / +2.176 ns; RX edge factoring 391,948.73 / +1.660 ns; parallel counter 392,327.94 / +2.690 ns; Boolean carrier factoring 391,046.18 / +1.759 ns. Reports are recorded in the [worklog](../WORKLOG.md). | Rejected; none was copied into the candidate. Do not spend another hardening on these forms. |
| Register carrier enable at the pin clock | Add one register for the carrier output gate so pad feedback no longer takes the combinational route from the live configuration latch through the output and RX path. Leave TX timer behavior and the timed configuration latch-to-register path intact. | Pre-layout STA improved from +8.858 to +9.154 ns typical and +2.717 to +3.344 ns slow. Mapped area increased by 445.70 µm² (390,666.74 → 391,112.44). Full/lean pin suites passed 60/60; exact-revision L2 passed 1,000,000 clocks with zero divergences in 555.36 s, and both RTL injections were detected on commit `3393eea`. | Current experiment. Standard GDS run [36799356107](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799356107) is still in `Build GDS`; routed timing, congestion, DRC, and complete signoff are not known yet. |
| Placement density, 56% → 58% (proposed D-068) | Hypothesis was that tighter placement might reduce long routes or route-pass effort. | The 56% route data showed a difficult detailed-route search despite lower overflow, fewer guides, and shorter wirelength; aggregate congestion does not establish that tighter placement will help. | **Paused.** D-068 says do not change `src/config.json` or start this experiment without a more specific congestion-map or timing hypothesis and team approval. |
| Global-route layer adjustment | If the current candidate still shows overflow, use the artifact's congestion map to choose one targeted routing-layer adjustment while leaving RTL, density, counts, and clock fixed. | Not yet run. Prior global-route warnings suggested changing layer adjustment, but this is only a flow hypothesis; it does not prove a physical fit. | Possible follow-up only after reviewing the current candidate's routing reports. Keep it separate from any RTL or density change and preserve complete timing/signoff checks. |

## Current progress

- The current candidate retains the 20 ns clock and the protocol-floor resources. No protocol feature or firmware support was removed.
- Exact-revision L2 is complete and checked in the phase checklist: 1,000,000 clocks, zero divergences; priority-flip and cursor off-by-one RTL mutations detected. Candidate counts remain experimental, not a final-count decision.
- `test`, `lint`, `docs`, and `unit` passed for both the R4 candidate and the recent `main` commit. The R4 GDS run above is the only remaining active workflow from that push.
- The GDS workflow's precheck, gate-level test, and viewer jobs follow hardening. They are still required if hardening succeeds; a completed route is not, by itself, Phase 2 signoff.

## What qualifies as progress toward Phase 2 exit

Record the hardening's global-route overflow/congestion, detailed-route runtime, all-corner setup and hold, and DRC/LVS/antenna evidence. The Phase 2 checklist also requires Tiny Tapeout precheck, gate-level protocol tests, viewer output for the real design, a full-design AREA row, and green `test`/`docs`/`lint`/`unit` workflows on `main`. The current candidate has not passed the physical gates yet. Do not mark Phase 2 complete until every checklist item has its own evidence.

### Next action

Wait for run 36799356107. If it fails, diagnose its artifact before selecting a single next experiment. Keep the clock, protocol support, and candidate counts fixed while testing that hypothesis; do not start the paused 58% density proposal by default.
