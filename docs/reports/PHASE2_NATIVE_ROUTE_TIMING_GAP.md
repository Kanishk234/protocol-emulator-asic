# Native clean route: physical checks pass, extracted timing does not

Route [39149073496](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39149073496), head `5867ea0688b4443a44f7e2d5851245cdfe0f33dc`, completes detailed routing and extraction but fails its strict extracted gate. Source screen [39141162581](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39141162581) passed every estimated gate. Keep the earlier passing extracted checkpoint 38784492656 as a separate baseline; it is not clean-build reproduction.

| Check | Screen | Extracted route |
| --- | --- | --- |
| Slow setup worst slack | 0 ns | −4.218641555 ns |
| Fast hold worst slack | +0.0819512 ns | +0.042531646 ns |
| Typical hold worst slack | +0.188140 ns | +0.131662907 ns |
| Slow hold worst slack | +0.364049 ns | +0.281998433 ns |
| Electrical violations, each corner | 0 slew / 0 fanout / 0 capacitance | 0 / 0 / 0 |
| Antenna violations | 0 nets / 0 pins | 0 / 0 |
| Detailed-route DRC | Not run | 0 after iteration 8 |

Setup is nonnegative at fast and typical corners. Fast hold is positive but misses the unchanged 50 ps acceptance gate by about 7.47 ps. Route instance area is 592372.68 µm² on a 902417 µm² core (65.64%, including SRAM). This is not Magic DRC, LVS, precheck or official GDS evidence.

The preserved effective signoff SDC hash is `63a9ac8dc9d00741c26ea37cf8ee01345c2ebf178e1c408dd213619e080d0ffa`, identical to the intended fully timed constraints. The failure is not a changed SDC.

## Critical paths and limits of the inference

Worst slow setup starts at configuration latch `_48225_`, unit 0 configuration word 0 bit 0, and ends at `_47215_`, mapped by the routed NL to `u_chip.dropped[14]`. The latch-to-counter path traverses pin-unit and fabric logic. Data arrival is 25.567234 ns against required 21.348593 ns. Its data section includes 49 buffer output arcs totaling about 10.790404 ns out of 19.025774 ns total cell delay. These are measured path delays, not a claim that deleting buffers preserves electrical constraints or recovers that entire delay.

Worst fast hold starts at configuration latch `_47933_` (unit 1 configuration word 5 bit 15), ending at `_46696_`, `u_chip.g_unit[1].u_unit.u_tx.er[7]`.

The estimated top-1000 slow setup paths are dominated by latch endpoints; the actual routed critical latch-to-flop pair is absent from that report. Zero global setup WS therefore does not show useful positive setup reserve or enumerate every potentially critical path. Add read-only FF-capture setup/hold reports alongside all original gates. OpenSTA supports selecting these pins with `all_registers -edge_triggered -data_pins`; use the pinned LibreLane corner-report fields and explicit current corner. [OpenSTA command source](https://github.com/The-OpenROAD-Project/OpenSTA/blob/master/sdc/Sdc.tcl).

## Bounded next test

Prepare `gds-native-wire150-hold125-screen`: change the native wire-length repair limit from 100 to 150 µm and hold repair target from 100 to 125 ps, retaining clean synthesis, CTS100/clock8, electrical55, antenna50 and the final native antenna pass. This tests whether reducing buffer-chain cost improves setup headroom while extra hold target compensates the measured erosion. It is a coupled policy trial, not attribution to one setting or guaranteed timing improvement.

All 20 ns signoff, 50 ps final fast-hold, zero electrical/antenna/overflow and 0.45 estimated electrical reserve gates remain fixed. No DRT until the new screen passes all gates. If electrical reserve fails, inspect offenders rather than waive the guard. If setup headroom remains inadequate, prioritize general carry/telemetry and configuration fanout paths using the measured capture reports; no RTL/ISA/latency change is authorized by this test.

Protocol replay for route39149073496 remains blocked because the route does not qualify. No Phase 2 boxes ticked.

## Wire150/hold125 screen result

[Screen39177724036](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39177724036), exact head `e7117101dd77e87cc7c1099c156b77c89e9cc54e`, passes all existing gates. Independently downloaded early artifact receipts and capture reports show:

| Corner | Global setup WS | Worst reported FF-capture setup slack | Hold WS |
| --- | --- | --- | --- |
| Fast | 0 ns | +12.175408 ns | +0.108167 ns |
| Typical | 0 ns | +8.205976 ns | +0.220712 ns |
| Slow | 0 ns | +1.483047 ns | +0.417586 ns |

All-corner electrical slew/fanout/capacitance violations remain zero; antenna nets/pins zero; estimated electrical reserve passes. Maximum slow slew utilization is0.448249980 against0.45, so that guard has little remaining room. The 20-path capture reports expose actual positive estimated FF-capture setup headroom; they do not establish positive global setup slack or guarantee extracted closure.

Prepared `native_wire150_route.py` and separate manual `gds-native-wire150-hold125-route`, bound to the exact successful screen. Shared continuation retains full independent source/config/hardware/readback/gate audits, repeats no repair, requalifies before DRT, and rejects extracted slow setup below zero, fast hold below50ps or any electrical/antenna/route-DRC violations. The prior failing route's protocol replay remains undispatched. Only extracted measurements of this new checkpoint can establish whether the policy addresses the gap.

## Wire150/hold125 extracted result: setup is the remaining blocker

[Route39278561678, attempt2](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39278561678/attempts/2) completed routing/extraction and failed the strict extracted gate solely on slow setup. Source remains screen39177724036; rerun uses exact head07aa6b3dbe2bda7ba81007f0d1d35dd069ce149c. Independently downloaded the early gate artifact and confirmed:

| Extracted check | Wire100/hold100 route39149073496 | Wire150/hold125 route39278561678 attempt2 |
| --- | --- | --- |
| Slow setup WS | −4.218641555 ns | −1.608071943 ns |
| Fast hold WS | +0.042531646 ns | +0.107658663 ns |
| Typical hold WS | +0.131662907 ns | +0.219348990 ns |
| Slow hold WS | +0.281998433 ns | +0.417386360 ns |
| Electrical/antenna/route DRC violations | 0 / 0 / 0 | 0 / 0 / 0 |
| Instance area including macro | 592373 µm² | 574597 µm² |
| Instances | 42698 | 39113 |

Fast/typical setup WS remains0. The coupled policy improves slow setup by2.610570ns, clears the50ps fast-hold gate, and reduces instance area by about17776µm² and count by3585. These are paired physical results, not isolated attribution to either parameter. Slow setup still fails; do not launch the gated protocol replay or claim Phase2/official signoff. Next inspect the newly critical extracted slow path and compare its estimated timing before choosing a targeted setup correction, while preserving the electrical/antenna/hold gains.

## Targeted native setup-reserve trial

Inspected exact attempt2 extracted slow `max.rpt` and final NL from artifact12210790306. Of1000reported worst paths,108are negative, driven by only two startpoints: `_48179_` (unit0configuration word0bit4) and `_48093_` (unit0word4bit2). Worst endpoint remains `_47215_`/`u_chip.dropped[14]`. Its extracted worst path has−1.608072ns; the estimated report's worst path to that endpoint has+1.611147ns, from the other latch. This is a roughly3.219ns endpoint-level estimate-to-extracted gap, not a same-path delay decomposition; startpoint ordering changes.

Prepare `gds-native-wire150-setup4-screen`, changing only `GRT_RESIZER_SETUP_SLACK_MARGIN` from0to4ns on wire150/hold125. The exact pinned LibreLane timing Tcl forwards this setting as `-setup_margin` to native `repair_timing` for setup and hold repair. [OpenROAD's primary repair-timing documentation](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html#repair-timing) describes the additional setup margin; no current-only optimizer flags are assumed available in the pinned image.

After all original strict screen checks pass, require the actual slow-corner FF-capture setup report minimum to be at least3.5ns. Missing/malformed reports, wrong path types or latch endpoints fail closed; original qualification cannot be restored after another gate failed. The guard uses measured reports, not global WS0 or the requested optimizer target. Preserve the20ns fully timed SDC,125ps hold repair target,50ps final hold acceptance, wire150/CTS100/clock8/electrical55/antenna50 and final native antenna pass.

This stronger screen is motivated by the measured endpoint gap, not proof that3.5ns will cover every future routed path. Native repair may fail to reach it, consume electrical reserve or increase area/congestion. No new DRT until it passes. Early artifacts include actual post-GRT timing-repair config/log/metrics to verify margin consumption and repair activity. Main hardware/config/template jobs remain unchanged.

## Setup4 timeout and a bounded synthesis-mapping follow-up

[Setup4 screen39304947404](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39304947404) did not produce final qualification evidence. Its watchdog returned124at6900seconds (115minutes), at OpenROAD.ResizerTimingPostGRT, with about4350seconds in that stage. Heartbeats show300–387%CPU/~1.975GiB RAM and repeated last-output table rows at0.0ns for `_47655_/D`. That original instance maps to a unit3configuration latch (word4bit15), not one of the two critical FF-capture launch latches. The native repair log file is empty at interruption; the captured console heartbeat is the available progress evidence. No final STA/capture/electrical/antenna result exists, so do not label the stronger guard as a measured failure or the design as newly regressed.

A global positive setup target is demonstrably expensive on this latch-heavy design and may spend effort on zero-slack latch endpoints. The exact optimizer state is not proven from a last-output row. Do not extend the deadline or repeat this recipe unchanged. Keep the current3.5ns measured FF-capture guard, but return global repair setup margin to0.

Prepare `gds-native-delay0-setup-reserve-screen`, changing only synthesis strategy from AREA1toDELAY0against the measured wire150/hold125 source policy. The exact pinned LibreLane3.1.0.dev3 schema includes DELAY0and synthesize.py passes SYNTH_STRATEGY to ABCScriptCreator.generate_abc_script. CI preflight checks the actual installed schema; names/recipe/artifacts identify DELAY0. The baseline environment remains AREA1only to construct and validate the source config before the reviewed final transform; generated physical config and recipe carry the actual DELAY0selection.

This tests mapping rather than stronger global latch slack repair. Same complete2/4RTL,20ns constraints, hold125target, wire150/CTS100/clock8/electrical55/antenna50/final antenna repair and every measured acceptance guard. Faster mapping is not guaranteed: area, fanout/capacitance, placement, synthesis runtime and routing may worsen. The existing900second synthesis and6900second total watchdogs remain. No DRT until all old gates and measured slow capture≥3.5ns pass. Preserve the−1.608072ns extracted baseline and the prior passing checkpoint independently.

## DELAY0 result and verified RTL combination

[DELAY0 screen39331886305](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39331886305) completed in3968.54seconds without timeout, but failed the existing0.45electrical reserve gate. Actual all-corner electrical violations and antenna violations remain0. Slow slew utilization0.454083513 on `_07413_`; SRAM DOUT9cap utilization peaks0.460984375 at fast (0.029503pF against0.064pF limit). Slow FF-capture setup is+1.615422ns, only~0.132375ns above AREA1wire150, and independently short of the3.5ns guard even though execution stopped at the earlier reserve rejection. Fast hold is+0.107021ns. No DRT is justified; mapping alone did not supply adequate setup headroom.

Return to AREA1wire150/hold125 and test the existing `bs_resync_event.patch` combination (D-071/D-072). It adds the resync arithmetic simplification to the currently used event-late optimization: compare period/boundary directly for nonzero elapsed time and cancel saturated correction before the25-bit sample-time arithmetic. No new state, ISA operation, protocol-specific block or cycle is added. The frozen candidate remains3393eea9a58c5cad9077cc360a8515d0e5ec8284 with exactly one patched RTL file, trw_pin_bs.v; main source remains untouched.

Fresh isolated verification at `/tmp/tripwire-native-resync-event-20261019`:892bit-clock equivalence points proven,21pin tests passed,5chip tests passed,2048lockstep clocks passed. Raw outputs remain outside Git. Expanded protocol RTL replay is required before launch and recorded below when complete. This is reuse/reverification of a prior prototype, not a claim of new extracted timing evidence.

The prepared `gds-native-resync-event-setup-reserve-screen` applies the exact existing combined patch and otherwise retains the source-bound physical recipe and all original acceptance gates, including measured slow FF-capture setup≥3.5ns. Source variant is explicitly recorded asbs-resync-event in the recipe; unknown variants are rejected. The patch may increase area or alter routing/hold/electrical behavior; the earlier ideal-wire gains are only motivation for a matched physical measurement.

Further extracted-path evidence for later work: the incoming paths to critical configuration latches48093/48179begin at45841/45843, whose routed Q nets are named `u_chip.g_lane[0].u_slots.wdata_q[2]`/`[4]`. Their data arrival times are5.369921/4.960792ns; latch reports show4.006943/3.549371ns borrowed at those endpoints. This is consistent with synthesis merging identical unconditional write-data registers into a shared broadcast; verify that topology before editing it. A general banked, write-enabled configuration input staging scheme could reduce distribution delay without adding architectural cycles, but needs separate equivalence/phase-boundary checks, reset/carrier-active handling and area/hold/physical evidence. This is an investigation lead, not an implemented fix or an approval to change the timing contract.

The first expanded replay attempt mixed current test_l3with frozen Sep30programs, producing a WS2812 packed-token mismatch. Fixed verify_timing_trial to archive current firmware together with current tests/tools while retaining frozen RTL/spec/resource tables. Added actual archive/patch regression coverage (BUG125). Preserved the invalid run log; the corrected suite uses the same RTL hash and current firmware. The prior21pin/5chip/2048L2evidence is retained; the chip regression's only loaded UARTfirmware is byte-identical between frozen/current revisions.

Corrected expanded Verilator replay completes **21/22**: SWD WAIT/retry returns only WAIT. Paired standalone Icarus12 RTL checks reproduce exactly the same failure at 2995280 ns on both event-late baseline and resync/event candidate. This is not solely a Verilator issue and does not establish a resync-specific regression. This initial failure blocked full-suite qualification; BUG126 is diagnosed and corrected below. Pinned Icarus13 cannot elaborate these frozen RTL forward declarations, so that attempted check is compile failure only, not protocol evidence.

### SWD firmware scheduling correction (local, 2026-10-19)

Baseline white-box diagnostics show13SWCLK rises, the target idle after WAIT, U1 WAIT active/OE released, and the retry routine blocked. The WAIT/FAULT turnaround issues CLK2 and then loads constants before arming its final WAIT; the short burst can finish first. Preloading WAITF/CLK2/OE1 before the command sequence removes those loads from the active burst. This preserves protocol commands and clock count, changes no RTL, and uses two fewer routine words. The independently timed model passed even the original sequence, so model-only evidence was insufficient here.

`programs/swd.trw` implements the scheduling fix. Both model and pin-level RTL WAIT/retry regressions now cover periods6/10/20/50; no speed reduction or assertion waiver. The frozen2/4 resync/event candidate passes all four periods with DPIDR/parity, no contention, target protocol checks and independent sigrok decode under **Icarus12 and Verilator**. Model/assembler regression: **44passed**. Native helper checks: **72passed**. Logs/XML stay in /tmp/tripwire-native-resync-event-20261019. Current-main RTL also passes the four-period SWD check under Icarus. SRAM usage falls from 105 to 103 words. The fresh complete Verilator replay passes **22/22 with no failures or skips**, in **341.28 seconds**, with independent decoders enabled. Evidence: `test_internal/chip/results_l3_resync_fixed.xml`, `l3-fixed.log` and `verification_receipt.json` in the isolated trial directory. Source hashes bind the tested firmware and test module to the current working tree. Functional verification is clean for these exercised cases; this supplies no new physical timing or official GDS evidence.

### Routed configuration staging topology confirmed

A buffer-only traversal of the exact route 39278561678 attempt2 netlist confirms that `u_chip.g_lane[0].u_slots.wdata_q[2]` reaches critical latch `_48093_` through a tree containing **51 buffers**, while bit4 reaches `_48179_` through **49 buffers**. Each tree has **154 non-buffer terminals: 153 latch D pins and one NOR4 input**. Latch outputs identify 52 sinks in lane0, 52 in lane1, 22 in full unit0, and nine each in units1–3. This establishes shared distribution across all six banks; it is stronger evidence than the earlier source/net-name inference. It does not attribute every reported buffer delay to this incoming path or prove a future timing gain.

A separately controlled unit-local, write-enabled staging trial could restrict each full-unit data bit to its 22 unit latches instead of all 153. Its costs include additional data flops and enable muxes; buffer removal and net area require synthesis/physical measurement. It must preserve reset, high/low latch phase behavior, live reconfiguration and the carrier predicate contract. No such RTL change is implemented or adopted here. Raw traversal receipt: /tmp/tripwire-config-staging-broadcast-39278561678.json.

Verified SWD firmware SHA256: `567e2c4e3ebd304363448a0e79d3db251381d5fbcfa11baba85476577551c77c`. Expanded test module SHA256: `bfd414a15fb5094b7ae2e2fc383c2dd770b409026681404f5a4d012415ef3339`. Full-suite XML SHA256: `8b6333ae95b944585b5c63d0069ca37ae1e41b34c31e3f89448189f817f4cee0`. These are simulation provenance, not physical signoff hashes.

## Native resync/event result — 2026-10-20

[Screen 39369398106](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39369398106), head `ecc54d4`, completes without timeout in 3969.64 seconds but **fails the measured setup reserve only**. All-corner electrical counts are zero, antenna nets/pins are zero, and electrical reserve checks pass (maximum slow slew utilization 0.415918481). Fast/typical/slow hold is +91.5819/+202.331/+392.965 ps; global setup WS is 0 at all corners.

Actual minimum FF-capture setup is +11.737211 ns fast, +7.481034 ns typical and **+0.164620 ns slow**, below the fixed +3.5 ns screening guard. Slow estimated headroom is 1.318427 ns lower than the original AREA1 wire150 event-late screen. These are pre-route measurements; no extracted WNS or routeability improvement is established. Do not route this candidate or weaken the guard to qualify it. All companion lint/test/unit/docs runs passed.

The worst reported slow path runs from configuration latch `_48493_` in U0 word0 to FF `_47526_`; source-bound netlist inspection is needed for exact bit/endpoint mapping. Instance IDs from older netlists cannot be reused. Keep the known event-late physical baseline while preparing a separately verified unit-local staging experiment against the established shared write-data broadcast. Artifact evidence remains local at `/tmp/tripwire-resync-gates-39369398106`; no raw logs committed.

The separate unit-local staging prototype, clocked-host proof scope, mapping costs and planned unchanged physical gates are documented in [PHASE2_CFG_STAGING.md](PHASE2_CFG_STAGING.md). It returns to the event-late baseline; the resync rewrite is excluded so that the staging change is isolated.
