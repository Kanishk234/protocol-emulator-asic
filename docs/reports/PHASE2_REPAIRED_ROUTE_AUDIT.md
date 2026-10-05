# Repaired routing result and hotspot audit

Evidence: [routing continuation 37187027878](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37187027878), saved antenna state, six fresh single-corner reports, intermediate iteration-50 DRC report, and job 111391024983 log. Candidate remains R4 SHA `3393eea9a58c5cad9077cc360a8515d0e5ec8284`, 20 ns, 56% density, GRT adjustment 0.16, four threads. Candidate RTL/config are unchanged.

## Timing survived antenna repair

| Corner | Setup WS (ns) | Hold WS (ns) | Setup / hold violations | Slew / fanout / cap violations |
|---|---:|---:|---:|---:|
| Fast | 0 | +0.0897432 | 0 / 0 | 0 / 181 / 0 |
| Slow | 0 | +0.366301 | 0 / 0 | 1 / 181 / 0 |
| Typical | 0 | +0.190121 | 0 / 0 | 0 / 181 / 0 |

These use signoff constraints and global-route-estimated parasitics, not extracted final-route parasitics. Zero setup WS includes latch checks; it does not demonstrate positive timing margin. Remaining slow slew violation is SRAM `A_MEN`: limit 0.595200 ns, slew 0.695871 ns, excess 0.100671 ns. The earlier NOR/A21OI slew failures are absent at this checkpoint. Fanout count rose from 164 to 181 during antenna repair.

## Routing plateau

Routing entered optimization iteration 0 at 07:59:34 UTC. It completed iteration 50 at 12:43:17 and timed out during iteration 51 at 13:21:59. The combined antenna/STA/DRT step hit its 330-minute limit; DRT itself ran about 322 minutes. Iterations 47–50 each ended with 108 violations. No detailed-routing `state_out.json` was saved, so the extraction diagnostic must remain undispatched.

| Iteration-50 snapshot | Earlier unmodified replay 37165048635 | Repaired continuation 37187027878 |
|---|---:|---:|
| Marker records | 215 | 108 |
| Shorts | 157 | 80 |
| Metal spacing | 58 | 28 |
| Metal2 / Metal3 / Metal4 | 184 / 20 / 11 | 103 / 3 / 2 |

These are intermediate, potentially overlapping marker records. The lower count is encouraging but does not establish clean routing or isolate which of the repair's cell, sizing, pin-swap or rerouting changes caused it.

## Current geometry

At 50 µm midpoint bins, 95/108 records fall in x=500–700, y=300–350 µm: 40 in x=600–650, 29 in x=550–600, 22 in x=650–700, and 4 in x=500–550. Another 9 lie in x=600–650, y=350–400. This substantially overlaps the earlier horizontal hotspot, but the most implicated nets changed.

| Current net | Marker records | Placed connections (component origins) |
|---|---:|---|
| Lane 0 output token bit 3 | 9 | `_46524_/Q` at (762.24,230.58), eight loads including three at x=565.92–581.76, y=325.08–355.32 |
| `net1580` | 9 | `fanout1580/X` at (578.88,336.42), six loads in x=578.88–593.76, y=317.52–347.76 |
| `net1468` | 8 | `fanout1468/X` at (682.56,306.18), eight loads in x=628.32–680.16, y=298.62–332.64 |
| `_18767_` | 8 | `_24339_/Y` at (581.28,340.20), three loads at (579.36,298.62), (631.20,302.40), (631.68,351.54) |

Coordinates describe cell origins, not pins or routed wire length. Even short local fanout branches appear repeatedly; long-wire splitting alone is not a sufficient diagnosis. The earlier U0 token-bit-16 net is no longer the top marker contributor.

`scripts/ci/routing_audit.py REPORT --placement DEF` reproduces marker type/layer/bin/net summaries and maps named nets to placed cell origins. It refuses incomplete marker parsing and labels intermediate evidence explicitly. It matched both actual snapshots (108 and 215 records) and the router's type/layer totals. Raw output remains under `/tmp`/CI artifacts.

## Functional evidence and next experiment boundary

[Repaired-netlist L3 37187473289](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37187473289) passed 22 cases, with zero JUnit failures, errors or skips. This covers the repaired pre-antenna netlist functionally; it is not SDF timing simulation or final routed-netlist verification.

Do not launch another unchanged replay or extraction from a timeout artifact. The next routing hypothesis should target local Metal2 access/spacing in this band. Before editing placement or routing guides, inspect actual cell pin shapes, power-grid/routing obstructions and guide occupancy for these branches. A controlled flow experiment can then change local placement spacing or route resource allocation, recheck global overflow, antenna and all-corner timing, and compare marker geometry. Increasing density or blanket buffering is not justified by these markers alone. The remaining SRAM-enable slew and clock fanout require their own electrical checks; no library limit is relaxed.

## Bounded local-resource screen

Pinned PDK revision `2bbec755dc67ca3db0261c3d6163e15735d66710` cell LEF confirms the implicated `buf_1`, `a21oi_1` and `a221oi_1` expose pins/obstructions on Metal1, not Metal2. SRAM LEF size is 236.8×191.34 µm at origin (12,40); its footprint is outside the x=500–700 hotspot. These facts narrow the investigation but do not prove the cause of the Metal2 markers. The saved DEF has power-grid via entries on Metal2 as well; without intermediate routed geometry, exact route/via interference remains unestablished.

Separate `gds-hotspot-screen.yaml` runs two fresh GlobalRouting/CheckAntennas flows from the identical repaired post-antenna checkpoint, then six independent corner reports using signoff constraints. Baseline retains global adjustment 0.16. Variant additionally sets `set_global_routing_region_adjustment {500 280 700 380} -layer Metal2 -adjustment 0.30` immediately before routing. The rectangle covers the persistent marker band with vertical margin. The value is a trial resource reservation, not a measured optimum or extra physical tracks. The hypothesis is that local Metal2 reservation changes guide allocation to reduce the detailed router's pressure in this band. [OpenROAD documents this region command and resource-reduction meaning](https://openroad.readthedocs.io/en/latest/main/src/grt/README.html#set-global-routing-region-adjustment).

The screen keeps placement, netlist, macros, clock, density and four threads fixed. It changes no candidate files and stops before antenna repair or DRT. Existing diodes remain in both states; new antenna violations, if any, are measured rather than silently repaired. A pinned custom image wraps only `grt.tcl` and fails if the command is absent; the helper verifies its execution marker and resolved routing inputs. Negative timing or nonzero overflow/antenna output must be assessed before any routing continuation. A completed diagnostic is not timing or physical closure. Eleven local helper checks pass, including same-source/matched-image orchestration and negative source timing blocking routing; workflow YAML, embedded Python and shell syntax parse.

### Completed screen 37219355996

[The diagnostic completed successfully](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37219355996). Both variants have zero GRT overflow and 33,775 instances. Baseline capacity/demand is 601,423/261,161; local reservation 599,647/259,788. Wirelength changes 2,530,396→2,518,898 µm (~−0.45%). This measures guide reallocation, not fewer detailed-route markers.

Region slow setup WS is −0.0447979 ns, TNS −0.180505 ns, with seven violations; baseline setup WS/TNS/count is 0/0/0 in every corner. Fast/typ region setup also remains 0/0/0. Hold WS baseline→region: fast +0.0732134→+0.0550778 ns, slow +0.327096→+0.312531 ns, typical +0.165298→+0.140381 ns. Slew count baseline→region is fast 0→0, slow 13→14, typical 1→0. Fanout remains 181 and cap 0.

Fresh global routing reintroduces antenna violations even though the input already contains repaired diodes: baseline 86 nets/95 pins; region 84 nets/97 pins. Therefore neither fresh route can proceed as an antenna-clean result, and the region state additionally needs timing repair. Inspect the seven slow paths before selecting a controlled timing/antenna repair trial. Any such trial must retain the same local override through every reroute (including antenna repair), then recheck overflow, antenna, electrical and all-corner timing before DRT. Diagnostic job success does not mean the region trial passed physical gates.

### Region repair screen

Six negative paths start at latch `_49036_`, ending at `_48142_`–`_48147_`; the seventh is `_49012_`→`_47080_`. All misses are between 0.016378 and 0.044798 ns. Separate `gds-hotspot-repair.yaml` restores the region checkpoint and applies slow-corner signoff-aware margin-zero timing repair, then antenna repair and six matched corner checks. It reports gates and stops before DRT even if they pass. The source artifact remains immutable.

The wrapper now covers `grt.tcl`, `rsz_timing_postgrt.tcl` and `antenna_repair.tcl` so their reroutes preserve the trial reservation. Actual repair logs must show the wrapper marker. Four Tcl execution tests verify reservation before routing in all three entry points and unchanged STA execution; fifteen helper/wrapper checks pass. Local Tcl was unpacked under `/tmp`, with no system package installation. No timing closure is claimed before this screen's measured result.

Repair 37220414494 failed the antenna reservation guard. Pinned `antenna_repair.tcl` invokes `repair_antennas` directly; internal reroutes bypass the Tcl `global_route` hook. The wrapper is corrected to set the same region immediately before `repair_antennas`, with a regression invoking that actual command. This is bug #64, not evidence that antenna repair itself failed: the saved final antenna checks have zero violating nets/pins after 88 inserted diodes and 65 jumpers. No valid matched post-antenna STA was produced before the guard stopped the run.

Timing repair inserted eight buffers, upsized four cells and swapped nine pins. Its internal estimate reached zero violations, but legalization/mirroring and fresh rerouting resulted in slow WS −0.114909 ns, TNS −1.61488 ns and 22 violations (fast/typ setup and all hold checks remained nonnegative). The legalization log reports 14,932 mirrored instances. This is evidence of downstream regression, not proof that mirroring alone caused it. Correct the hook and measure post-antenna timing before proposing another single flow change.

### Corrected baseline and mirroring hypothesis

[Corrected repair 37221292614](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37221292614) passed orchestration and confirmed the antenna reservation marker. Post-antenna antenna violations are zero. Slow setup WS is −0.124212 ns, TNS −1.33337 ns, with fifteen violations: fourteen start at `_49036_`, one at `_49139_` and ends at `_47080_`. Fast/typ setup and all hold checks are nonnegative. Slew fast/slow/typ is 0/1/1, fanout 193, cap 0. The artifact explicitly records timing/antenna gate failure and no DRT launch. The fix inserted 89 antenna diodes and 66 jumpers; these are different from the prior uncorrected run.

Next one-variable screen sets `PL_OPTIMIZE_MIRRORING=false` during repair in a disposable config. [Pinned LibreLane defines this control](https://github.com/librelane/librelane/blob/3.1.0.dev3/librelane/steps/common_variables.py), and its `common/dpl.tcl` still legalizes and checks placement while conditionally skipping only optimize_mirroring. Compare with corrected baseline using the same source and all other settings. Positive margin remains zero to avoid the known latch repair stall. Sixteen helper/Tcl checks pass, including immutable source configuration and the single-field trial override. Do not attribute regression to mirroring before this measurement or dispatch DRT from the current negative-timing state.

Baseline worst path maps `_49036_` to U0 configuration word 4 bit 0 and `_48147_` to `u_chip.dropped[21]`. The fifteenth failing path maps `_49139_` to U0 configuration word 0 bit 0 and `_47080_` to U0 BITSYNC `tb[24]`. This reinforces that configuration and same-cycle feedback must stay timed under D-066; registering those signals or excluding the paths would change the contract rather than close timing.

### No-mirroring result 37360552753

[The controlled no-mirroring run](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37360552753) completed in 13 minutes 13 seconds. Fresh post-antenna setup WS/WNS and setup/hold violation counts are zero in every corner. Hold WS fast/slow/typ is +0.0499802/+0.302909/+0.141023 ns. Antenna violating nets/pins are 0/0. The artifact gate passes estimated timing/antenna and explicitly records no DRT launch. This improves the matched estimated slow result from −0.124212 ns / 15 violations, without changing timing constraints or RTL.

Electrical closure does not pass: slow/typ slew count is 19/1 (fast 0), fanout 189, cap 0. Repair inserted eight buffers and upsized four cells; antenna repair inserted 76 diodes and 63 jumpers. No final route or extracted timing exists for this state. Audit the slew violators and retain this exact state/provenance when preparing any DRT diagnostic. Zero setup WS includes naturally zero-slack latch checks, and the fast hold margin is narrow; neither figure guarantees positive routed margin.

The nineteen slow slew records group around `_39031_` NOR3 and eight loads (nine records, worst slew 2.892918 ns vs 2.507400 ns), `_30323_` NOR4 and its load/diode (three), `_30187_` NAND4 and its buffers/diode (four), `_34785_` O21AI and its load (two), plus SRAM A_MEN (one, 0.865898 ns vs 0.595200 ns). These are measured shared-net targets for a separate electrical repair; avoid indiscriminate buffering or assuming antenna cleanliness also fixes slew.

Separate `gds-hotspot-drt.yaml` restores the exact passing no-mirroring state and dependency artifacts. The helper checks fresh corner setup/hold WS and counts, antenna nets/pins, signoff constraints, margin zero, no-mirroring config and saved state files before one explicit DRT step. Four threads and five-iteration marker reports match the earlier diagnostic; runtime limit is 330 minutes. The wrapper also covers `drt.tcl` for internal antenna reroutes. Electrical violations are explicitly still open: this diagnostic tests routing convergence, not full signoff. Twenty-one local helper/Tcl checks pass, including refusal of negative timing, dirty antenna and missing files. Final extraction and downstream physical/protocol checks are required after any clean completion.

### Completed route 37363064899

[Route diagnostic 37363064899](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37363064899) completed successfully in ~1 h 30 min including setup. The first routing pass reached zero violations, detected 32 antenna violations, repaired antennas and rerouted to zero violations again. Final saved state has `route__drc_errors=0` and `route__antenna_violation__count=0`; ODB, DEF and both netlists are present. Terminal detailed-route wirelength is 1,912,141 µm. No extracted WNS or full signoff claim follows from these metrics alone.

Owned `gds-hotspot-extracted-timing.yaml` restores this route artifact and original source dependencies, validates successful workflow provenance and completed zero-DRC state, then invokes the existing cleanup/connectivity/fill/RCX/STA guard with `--route-root runs/hotspot-drt`. Fresh reports must exist for all three corners. Negative timing remains diagnostic evidence rather than being hidden; full downstream DRC/LVS/precheck and functional final-netlist evidence remain necessary. Twenty-two helper/Tcl checks pass including valid clean-state acceptance and missing-file refusal.

### Extracted timing 37375411729

[Extraction completed successfully as a diagnostic](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37375411729). Routing DRC, critical disconnected-pin and wirelength checks passed; one disconnected pin was classified noncritical by the flow. Timing does not pass:

| Corner | Setup WS (ns) / violations | Hold WS (ns) / violations | Slew violations |
|---|---|---|---:|
| Fast | 0 / 0 | −0.020809 / 4 | 1 |
| Slow | −6.178462 / 902 | +0.198143 / 0 | 179 |
| Typical | 0 / 0 | +0.057654 / 0 | 28 |

Worst slow path is U0 mode configuration word0 bit0 latch `_49139_`→`dropped[26]` flop `_48163_`. Arrival 27.414698 ns exceeds required 21.236235 ns. Departure/borrowing time given to startpoint is 4.038346 ns. Large arcs: `_25365_/Y` O21AI_1 1.905905 ns, `_25366_/Y` O21AI_1 1.379506 ns, `_25128_/Y` NOR4_1 1.372737 ns. These measured load/slew-sensitive cell arcs identify targets for a separately controlled structural/sizing/load-distribution change; constraints and same-cycle feedback must remain intact.

Worst fast hold is U0 configuration word13 bit12 latch `_48986_`→TX `ct[12]` flop `_46495_`, arrival 0.894947 ns vs required 0.915756 ns. Any setup repair must also check all four fast hold failures. The older completed extracted result was −10.698019 ns from another physical run; this is not a matched single-change comparison to that old result. Zero pre-route WNS was insufficient to establish routed closure.

Final routed-netlist L3 37375683211 stopped before simulation because its validator read PL_OPTIMIZE_MIRRORING from a DRT config that omits placement-only variables. Bug #65 fixes this by validating policy against the saved repair config. The corrected validator executed successfully on the actual downloaded artifact and matching SHA256; protocol simulation evidence remains pending.

Corrected verification 37376481257 is active. The critical `_25365_` driver is at (201.12,570.78) µm; `_25366_` and `rebuffer5871` are near (925.92,563.22–567.00), a 724.80 µm x span. Nominal extracted SPEF gives `_19783_` total capacitance 0.156899 pF and 29 resistor segments totaling 1122.8124 Ω; the sum is not source-to-sink equivalent resistance. Following `_19784_` has 0.0560947 pF and eight segments totaling 329.6446 Ω. This is a measured long, capacitive branch between the worst two output arcs and provides a specific distribution/sizing target for a new controlled repair. Placement origin spans and resistor sums alone do not predict the improvement or select a legal buffer location.

On the worst reported slow path, 50 cell-output arcs (including latch Q and buffers) contribute 16.019526 ns of incremental delay, while summed input/net increments contribute 0.084843 ns in this estimated-parasitic report. Largest output arcs include `_30525_/Y` A221OI 0.570740 ns, `_38458_/Y` O21AI 0.526990 ns, `_38425_/Y` NOR3 0.492175 ns and `_38194_/Y` A221OI 0.486931 ns. Cell arcs include dependence on load and input slew; these sums do not prove physical wire delay is negligible, especially before extraction. They identify common-cone cell sizing, load distribution and combinational depth as alternatives to inspect if the no-mirroring trial fails. No RTL or cell edits are made from this audit alone.


### Controlled critical-branch trial prepared (2026-10-05)

The pinned LEF contains O21AI_1 only, so O21AI_2/_4 upsizing is unavailable. A separate `gds-critical-branch-repair` workflow prepares a BUF4 insertion at the initial midpoint (563.52, 570.78) µm between `_25365_/Y` and both remote loads `_25366_/B1` and `rebuffer5871/A`. The saved region-screen checkpoint inherits exactly this three-pin connectivity from repair 37185455158; local netlist inspection confirmed it. A Tcl guard rejects changed connectivity, a changed driver master, missing power nets or repeated insertion before mutation. Power connections are copied from the driver. The wrapper applies the change immediately after reading the pre-route ODB, legalizes before the first GRT pass, and preserves the established region reservation and disabled mirroring. It never edits the final routed ODB.

The trial uses the same pinned R4 hardware, 20 ns clock, density and signoff constraints. Its added buffer is a physical implementation change only. Existing resizer/antenna and independent per-corner reporting remain in place; estimated gates only permit DRT, never establish timing closure. The DRT provenance validator explicitly permits the new workflow only when its artifact records the critical-branch flag. Final extraction and functional verification must still follow successful DRT; close all four actual fast hold failures and electrical violations before promotion. No improvement is claimed until those measurements exist.

Local validation: 24 helper/Tcl tests passed, including both audited load rewiring and rejection of an unexpected load before creating cells. Shell syntax, workflow YAML/embedded Python and diff checks passed. These checks do not execute real OpenDB or establish legal placement/routability. No local Docker/OpenROAD executable is available. The trial is not published or dispatched: the latest supplied AGENTS.md Git rule reserves commit/push for the user.


### Fast hold endpoints and repair-hook validation (2026-10-05)

Audited all four negative paths in extraction 37375411729's fast `min.rpt`, then mapped launch/output signals in the exact final routed netlist:

| Configuration launch | Captured state | Arrival / required (ns) | Hold slack (ns) |
|---|---|---|---|
| U0 word13 bit12, `_48986_` | U0 TX `ct[12]`, `_46495_` | 0.894947 / 0.915756 | −0.020809 |
| U0 word13 bit14, `_48990_` | U0 TX `ct[14]`, `_46497_` | 0.904757 / 0.913878 | −0.009121 |
| U0 word13 bit3, `_48968_` | U0 TX `ct[3]`, `_46511_` | 0.895907 / 0.903980 | −0.008073 |
| U3 word4 bit1, `_48664_` | U3 RX `rt[1]`, `_47897_` | 0.941699 / 0.942055 | −0.000356 |

These short data paths need a separate hold-repair assessment after the controlled setup trial. Do not modify shared clocks or exempt configuration paths. A targeted data-path delay can be investigated against both minimum and maximum extracted timing, but no hold insertion has been made and no result is predicted from the slack alone.

Added executable wrapper tests proving branch insertion follows the one checkpoint load, precedes legalization and first global route, and rejects missing/duplicate checkpoint-load commands before executing the repair. The complete helper suite now passes 27 cases. Unit workflow 37376426740 completed successfully; final routed L3 37376481257 was still running at this check. Trial publication remains pending under AGENTS.md.


### Critical branch screen result 37381107529

Corrected container wrapper executed insertion and legalization; workflow completed. The fresh post-antenna gate is **false**: slow estimated WNS −0.280528 ns, six setup violations, while fast/typ setup pass. Hold WS fast/slow/typ is +0.0503921/+0.281459/+0.132105 ns, with zero violations, and antenna repair terminates at zero violations. Failed setup endpoints are `_49012_`→`_47080_/79/78` (−0.280528/−0.191168/−0.056440 ns) and `_49036_`→`_48163_/66/64` (−0.030042/−0.010495/−0.003588 ns). The checkpoint is not advanced to DRT. These estimated results cannot be compared as routed improvement against −6.178462 ns.

Separately, previous final routed netlist verification 37376481257 passed all 22 JUnit cases with zero failures/errors/skips. It is functional verification of that earlier routed netlist, without SDF, not validation of this branch modification or timing closure. Latest main lint/test/docs/unit on 90e20a2 pass.


### One bounded post-antenna repair follow-up

Matched branch-trial reports show `_49012_`→`_47080_` is already −0.309102 ns immediately after the resizer's placement/routing output; antenna repair changes it to −0.280528 ns. Thus antenna repair is not the sole source of the new deficit. The resizer log's no-violation statement does not describe the final fresh STA outcome. No causal sizing/locality improvement is assumed.

A separate `gds-critical-branch-followup` runs one ordinary signoff-aware, zero-margin repair from the saved clean post-antenna branch ODB using the existing region image, which does not reinsert the branch. It preserves the source artifact in place and writes runs/branch-followup. Original R4 hardware, 20 ns/density56, four threads, region resource reservation and no-mirroring policy remain. Source gates are allowed to have negative timing because this is a repair diagnostic, while source antenna must be clean and branch provenance must match. Fresh per-corner timing/antenna gates still block advancement; this workflow does not run DRT. Local suite 34 passed, including source/provenance/antenna/reinsertion rejection. If final gates remain negative, do not repeat identical follow-ups.
