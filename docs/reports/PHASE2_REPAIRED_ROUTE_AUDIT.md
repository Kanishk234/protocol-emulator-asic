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
