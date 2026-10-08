# Timing closure research: current extracted evidence and next experiments

The target remains the complete2-lane/4-pin candidate at20ns in6x4 tiles, with required protocol behavior, D-066 live reconfiguration, nonnegative extracted setup/hold, positive margin on real constrained endpoints and an actual passing official GDS/precheck/GL run. This report does not establish closure. No phase checklist changes.

## What the current failure actually contains

Clean detailed route37807978035 finishes in55 minutes with0 final routing violations and0 antenna nets/pins. Extraction37815131590 reports slow setup−0.6039080517705893ns and fast hold+0.10929035763504281ns. Fast/typical setup WS0; slow/typical hold+0.38645998606225973/+0.21145952254413386ns. Diagnostic success means the measurements were produced, not that timing passed. Routed22-case GL37815131566 remains active at this snapshot.

Selected slow report from artifact11565909997 has8 printed failing paths, all starting at pin0 configuration word4 bit9 latch48905 and ending at dropped[64..71] registers48112–48119. Worst is48115/dropped[67]. The paths include the live bit-synchronization decision and fabric accounting; a dedicated protocol shortcut or delayed counter update would change the contract.

Worst-path arithmetic: arrival21.593807ns, required20.989899ns. After its timed latch-D start,43 reported mapped output arcs contribute16.737723ns. Net/input arcs add about0.152ns over that portion of the path. This is primarily a long mapped logic cone with poor loaded-cell slew, not a single long wire. Largest cell delays:38387 inverter1.172724ns,44607 O21AI1.102149ns,38386 A21OI0.891646ns,30666 A221OI0.847591ns. Directly available stronger versions must be checked in the pinned library; o21ai_2 and a221oi_2 do not exist. BUG80 forbids accepting black-box probes.

## Independent sizing results on the exact current wires

Read the actual final NL and nominal extracted SPEF using cached OpenSTA and pinned standard-cell/SRAM Liberty files. Fully timed constraints reproduce all six CI setup/hold values within1e-6ns. Every replacement master is checked before link, and missing-cell/black-box/error output is rejected. Raw evidence and comparison manifest stay in `/tmp/tripwire-closure-probes-37815131590`.

| Fixed-wire trial | Slow setup WS(ns) | Added library area(µm²) | Decision |
|---|---:|---:|---|
| Current extracted baseline | −0.603908062 | 0 | Reference |
|38387 INV1→2 | −0.154354751 | 1.8144 | Insufficient alone |
|38387 INV1→4 | −0.041485038 | 5.4432 | Insufficient alone |
|38387 INV1→8 | −0.180703461 | 12.7008 | Reject larger-cell assumption |
|38386 A21OI1→2 | 0 | 5.4432 | First physical trial |
|38386 A21OI1→2 plus38387 INV1→2 | 0 | 7.2576 | Separate follow-up if needed |
|38386 A21OI1→2 plus38387 INV1→4 | 0 | 10.8864 | Lower-priority follow-up |
|30500 A21OI1→2 | −0.432745397 | 5.4432 | Insufficient alone |

All trials retain fast/typical setup WS0 and hold fast+0.109290354ns/slow+0.386459976ns/typical+0.211459517ns on unchanged wires. With38386 alone, the8 formerly failing endpoints measure+0.085911721 to+0.498669565ns. Global WS0 includes transparent-latch paths and is not a positive global WNS claim. These are fixed-wire estimates; rerouting changes capacitance, slew and upstream load. In particular, larger inverter strength becomes worse at8, illustrating why blindly maximizing drive is not the policy.

## External sources checked against the pinned implementation

- [OpenROAD Gate Resizer](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html): setup repair can size, buffer, clone and split loads; hold repair normally avoids creating setup violations. Its current documentation includes newer flags. Our actual LibreLane3.1.0.dev3 wheel invokes `repair_timing` with setup/hold margins, buffering/cloning controls, buffer limits and utilization caps. Do not assume every current upstream flag exists in the pinned OpenROAD.
- [OpenROAD RC correlation](https://openroad-flow-scripts.readthedocs.io/en/latest/tutorials/SetRC.html): inaccurate estimated wire RC can produce inconsistent global-route versus detailed-route timing. This supports measuring correlation on the same paths; it does not justify altering foundry extraction rules to improve the number. Actual extracted capacitance/slew remain the acceptance evidence.
- [LibreLane step configuration](https://librelane.readthedocs.io/en/latest/reference/step_config_vars.html): native setup/hold margin, gate cloning, buffering, repair-TNS and maximum-utilization controls can be used without replacing template jobs. Pinned wheel confirms setup margin default0.025ns, hold0.05ns, cloning/buffering enabled, setup-before-hold default. Existing D-032/BUG63 latch interactions make a large global setup margin risky: it can chase zero-slack latch paths without improving the real endpoints.
- [Yosys ABC](https://yosyshq.readthedocs.io/projects/yosys/en/v0.52/cmd/abc.html): delay target and input-drive/output-load constraints inform mapping. A tighter synthesis target or native sizing is a clean-build option, but must be measured for area, fanout and global overflow; ideal-wire synthesis slack does not predict final closure.
- [Tiny Tapeout action](https://github.com/TinyTapeout/tt-gds-action/blob/ihp-cmos5l/action.yml) and cached support-tools `Project.harden`: the official build merges project/user configuration and invokes ordinary LibreLane. Current diagnostic checkpoint sizing and custom regional routing reservations are not automatically inherited by that build. Keep official jobs unchanged and prove reproducibility independently.

## Selected physical experiment

`gds-drop-driver-screen` starts from successful hold screen37806209914, not the failing extracted result. This preserves its positive hold margin and the audited prior repair chain. Replace only38386 A21OI1→2, exact input/output nets and compatible supplies; no inverter or other cell is sized. Pinned Liberty functions match `!((A1*A2)+B1)`; area increases5.4432µm² before physical effects.

Guard every prior netlist transition, both earlier NOR2 strengths and all9 BUF1/D connections. Require a fresh pre-edit ODB netlist matching the inherited source, exact one-master change, powered export, legalization, zero-overflow global routing, strict incremental antenna repair, diode-only subsequent changes and fully timed all-corner STA with fast hold≥50ps. No DRT or official hardening is launched by the screen. Actual source-NL rehearsal passes.336 related helper tests pass,8 system-tclsh wrapper tests skip;25 new driver tests include end-to-end rejection of wrong source/history, insufficient saved hold, fresh setup/hold failures, changed clocks and extra logic. OpenDB commands in tests are mocked.

## Work after the screen, ordered by evidence and cost

1. If the single-driver screen qualifies, resume detailed routing without repeating repairs and measure extraction/GL. Keep original−0.179789ns baseline until actual extraction improves. If setup regresses, inspect its new critical paths rather than stack unmeasured repairs.
2. If the same branch still fails, test the separate INV1→2 follow-up; pair fixed-wire evidence is encouraging but not a physical guarantee. Investigate load splitting/cloning of supported gates if stronger drive plateaus. Measure the input-capacitance penalty and protect hold leaves.
3. For official portability, measure native synthesis sizing/tighter delay mapping independently, then native all-corner setup-before-hold repair. Review each project-config change outside the AGENTS whitelist before adoption. Do not inject physical mutations through SDC or alter template jobs.
4. If small ECOs cannot retain routed margin, revisit the live-config→BITSYNC arithmetic/control cone with stateless parallel predicates or balanced arithmetic, using exact modulo-width equivalence and chip-level protocol tests before physical trials. Prior counter bit-toggle, CSA, shared-RX and banked-selector experiments already exist; avoid rediscovering rejected candidates without new evidence.
5. Only promote a reproducible full candidate to the unchanged official workflow after the measured route/extraction/functional gates. Full DRC/LVS/precheck, all-corner timing, source lists, macro/PDN integration and refreshed main CI remain required.

## Constraint-artifact trap caught during this research

The artifact's `final/sdc` contains inherited setup-to-latch exceptions, while STAPostPNR actually reads the explicit signoff constraint file. Reusing that inherited SDC produces an invalid positive slow result+1.393760ns. The mandatory baseline-match assertion caught and discarded it; fully timed constraints reproduce−0.603908ns. This is the already established BUG63/D-066 interaction, not evidence that the diagnostic's actual signoff measurement was wrong.

Future extraction helpers now copy the exact effective signoff input into the evidence directory, pass that copy to STA and record its SHA256/source path. A regression test verifies that the copy remains valid after source removal and differs from an inherited masked view. This makes independent replay use the actual timing contract.


## Clean-build mapping prototype and continuation preparation

Published ccddb80 and launched [driver screen37818177484](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37818177484) with antenna repair enabled. It is building the pinned image at this snapshot. Prepared a conditional DRT continuation for this exact source: refuse unsuccessful run, audit the full inherited hold/sizing chain plus one-driver change, require fresh all-corner STA/50ps fast hold and preserve downstream extraction/GL evidence.83 continuation tests pass. No DRT from this pending source is launched.

Independent native-style mapping uses the pinned wheel's ABC script creator on the same event-late BITSYNC module in the isolated official-preparation directory, typical mapping library and slow ideal-wire STA,20ns target and identical10fF loads/BUF4 input drive. DELAY0 gives43678.6182µm²/12.122954ns PERIOD→rx_load; DELAY1 gives44772.5502µm²/10.994252ns. DELAY1 trades about2.50% module area for1.128702ns shorter targeted delay. Turning native sizing on adds no change at this20ns mapping target in either strategy. No new flop state is passed through ABC, and the source/clock/behavior are unchanged. This is local mapping evidence, not a full-chip timing/area result or a pinned-container reproduction. AREA/other delay controls are being compared separately before choosing a clean-build experiment. Main config and RTL remain untouched.


Additional same-module controls: AREA0 gives40393.6092µm²/13.142539ns, AREA1 gives40144.3938µm²/12.479320ns, DELAY2 gives45251.1738µm²/10.482940ns. AREA1 improves the targeted ideal-wire path by0.663219ns while reducing module area0.62%; it is the selected clean-build comparison against AREA0. The matched native screen uses stock pinned LibreLane and the same event-late2/4 RTL, fully timed20ns constraints,56% density and identical all-corner repair. It changes only generated SYNTH_STRATEGY between jobs and omits the regional-reservation image. Nine new guards verify source/strategy allowlisting, unchanged macro/clock/hold inputs, stock-image operation and matrix symmetry. This is D-080, an isolated experiment; main configuration adoption remains unapproved.

361 related physical/continuation/extraction tests passed with8 system-tclsh wrapper skips before native-screen additions;25 native/RTL-screen tests pass. Conditional driver DRT remains unlaunched until actual source completion and all gates pass.


Published native/continuation preparation on97e6f84 and launched [stock-image mapping comparison37819169130](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37819169130). AREA0 and AREA1 matrix jobs use the same event-late source; measured results pending. Driver37818177484's measurement step passes; artifact upload remains active at this snapshot, so DRT still awaits final successful-source evidence.

Resolved the8 earlier local wrapper skips with an isolated `/tmp` Tcl command shim backed by cached OpenSTA's Tcl runtime, preserving script arguments and failing on Tcl errors. All394 selected physical-screen, routing, extraction and native-mapping tests now pass with zero skips. This verifies guards and orchestration with mocked physical operations, not layout timing.


Driver screen37818177484 completed successfully: setup WS0 in all corners with zero timing violations, hold fast+0.0717144ns/slow+0.336162ns/typical+0.168788ns, antennas0/0. It meets the unchanged50ps gate. Launched [guarded DRT37819598187](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37819598187) on97e6f84 from this exact successful source, original37533969613/bs-event-late, without repeated sizing/hold repair. Actual extracted gain remains pending. Native mapping37819169130 remains in progress.

## Driver extraction and native comparison: completed results

Driver DRT37819598187 succeeds. Extraction37825505569/artifact11570759230 reports slow setup−0.14708412681900332ns, fast/typ setup0; hold fast+0.06757972150942818ns, slow+0.34680981290632085ns, typ+0.1754376693575883ns. This beats original−0.179789ns by about0.032705ns but still fails setup. New driver routedGL37825505461 is pending; prior hold routedGL37815131566 passes22/22.

Selected exact extracted slow max report contains9 negative paths, all starting at48909 (unit0 configuration word1 bit1). Worst endpoint47775 is−0.147084ns; others47981/47982/47985/47983/47979/47980/47984/47774 range−0.117838..−0.020139ns. Previous8 printed failing endpoints are absent from this report; this is not a quantified positive-margin measurement of those endpoints.

New worst path includes25443 O21AI1 (fanout2,0.100257pF,1.252590ns arc,1.512237ns output slew),25445 XOR2_1 (fanout2,0.080263pF,1.415335ns arc,1.166218ns output slew), followed by27852 NAND3_1 and previously strengthened27853 NOR2_2.25445 drives unit3 sel. Pinned slow library only has XOR2_1/O21AI1/NAND3_1, while NOR4 has1/2 strengths. Thus an invented XOR2_2 or O21AI2 trial is invalid. Next independent fixed-wire probes should inspect supported upstream sizing, NOR4_27962_ strength2 and buffer/load splitting possibilities; first map the exact nets and validate all three corners on this new extracted baseline. Do not blindly repeat38386/38387 experiments for a different bottleneck.

Native mapping37819169130 completes. AREA0 final fresh fast hold−0.00416389ns fails; AREA1+0.0404413ns is positive but below50ps continuation margin. Both setupWS0 in all three corners. Final repair GRT tables report zero overflow: AREA0 usage239260/601423(39.78%), AREA1 236798/601423(39.37%). Corresponding final repair cell-type report totals are510004.37µm²/33191 cells versus506758.41µm²/32768 cells (AREA1 about0.636% less reported area). These totals must not be presented as standard-cell-only die occupancy without separately identifying the SRAM contribution. No detailed routing, extracted timing or official qualification follows from these GRT measurements. AREA1 remains the better native lead but needs hold margin and matched stock post-antenna sequence evidence.

## Fresh-baseline fixed-wire probes

Downloaded driver extracted final NL/SPEF from artifact11570759230. Ran27 STA processes across9 variants/control instances and three corners; baseline reproduces all six CI values within1e-6ns. Missing masters/black boxes/errors rejected. Evidence stays under `/tmp/tripwire-closure-probes-37825505569` and `/tmp/tripwire-driver-pair-probes-37825505569`.

| Exact cell substitution | Slow setup WS(ns) |
|---|---:|
|Baseline|−0.147084132|
|27962 NOR4_1→2|−0.039319661|
|place7068 BUF1→2|−0.092601486|
|place6758 BUF1→2|−0.126224369|
|place6860 BUF1→2|−0.020914827|
|27962 NOR4_2 plus place6758 BUF2|−0.039319661|
|27962 NOR4_2 plus place6860 BUF2|−0.020914827|
|place6860 BUF1→4|−0.020914827|

All retain fast/typ setupWS0 and worst hold fast+0.067579724ns, slow+0.346809804ns, typ+0.175437674ns on fixed wires. Best one-buffer result moves worst endpoint to47981;47775 remains−0.009077184ns, so no closure is claimed. Larger buffer/pair spending has no measured global benefit. Next inspect the residual branch and its slew/load before adding another cell change. No new physical workflow launched from these still-negative estimates.

## Residual two-branch repair: qualified fixed-wire prototype

Ran24 further three-corner probes from the current driver extracted baseline. Tail44061 A21OI1→2 or28681 NOR4_1→2 alone do not improve global WS because the other branch dominates. Combining place6860 BUF1→2 with either tail repair moves global slow WS to−0.009077184ns. Adding27962 NOR4_1→2 to the place6860/44061 pair gives setupWS0 in all corners, with unchanged worst hold fast+0.067579724ns/slow+0.346809804ns/typ+0.175437674ns. Explicit slow endpoint reports measure all9 former failures+0.098701492..+0.731180489ns; globalWS0 includes transparent latches and is not positive global WNS. Three-cell library area cost18.144µm², no added state or connectivity change. Fixed-wire gains remain unqualified physically.

Prepared `gds-residual-setup-screen` from successful driver source37818177484. Its three-cell helper preflights all targets, masters, pins, nets and supplies before any mutation. Complete inherited repair history, unchanged source fingerprints, fresh NL/PNL, exact three-master-only change, strict zero-overflow routing/antenna checks and fresh all-corner timing with50ps fast hold remain required. No DRT launched by the screen. Actual extracted NL rehearsal passes.120 selected new/prior sizing and continuation regressions pass with cached Tcl interpreter; physical commands in tests are mocked. Workflow/source audit and shell/diff checks pass. Source/profile choice is frozen; no arbitrary sizing input accepted.

Prepared helper/workflow/report changes remain local. The latest user-supplied AGENTS.md prohibits Codex commits/pushes; publishing requires the user to run the scoped commands. Prior general command approval is not treated as overriding that later explicit git rule. FIPE and unused hold prototypes remain outside the publication groups. Once published, dispatch only this screen, inspect actual results, and prepare DRT continuation only if all gates qualify.
