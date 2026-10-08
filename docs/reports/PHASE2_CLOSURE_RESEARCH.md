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
