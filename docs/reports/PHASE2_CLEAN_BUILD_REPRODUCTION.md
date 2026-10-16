# Reproduce the clean routed checkpoint from RTL

The measured baseline is route/extraction [38784492656](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38784492656), followed by exact-netlist protocol regression [38796998628](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38796998628): **22 passed, no failures, errors or skips**. These runs establish the checkpoint's measured timing, electrical and exercised functional behavior. They do not establish clean-build reproduction or official GDS/LVS/precheck.

## Integration preparation

Prepared `/tmp/tripwire-clean-inline-official-prep-20261015` from a fresh Git archive of `3393eea9a58c5cad9077cc360a8515d0e5ec8284` plus exactly `bs_event_late.patch`. It contains the real TT wrapper, generated 2/4 specification/fabric, U0 full, 12 slots per lane and the 512-word SRAM. Metadata names the actual resources rather than the frozen spike's stale 3/6 description.

- `tools/gen/gen.py --check` passes on the isolated candidate.
- The two source lists match, with all 19 source modules present.
- Fully timed signoff SDC hash remains `63a9ac8dc9d00741c26ea37cf8ee01345c2ebf178e1c408dd213619e080d0ffa`; no latch setup false path is introduced.
- `candidate_manifest.json`, `integration_inventory.json`, `official-hardware-review.patch`, `official-native-config-proposal.json` and `native-config-delta.json` make the integration and settings reviewable. The inventory covers 17 differing text files and nine SRAM views, including binary view hashes. The proposed configuration is separate and unapplied. This is review material, not a complete promotion patch: macro copying, configuration review and regeneration of main's generated documentation remain explicit integration steps.
- Full-wrapper RTL replay of the current 22-case suite passes 22/22 locally with sigrok, with zero failures, errors or skips (`/tmp/tripwire-clean-inline-rtl-l3.xml`). The first sandboxed invocation decoded no UART bytes because libusb initialization was denied; replaying the same captured waveform outside the sandbox decoded every expected byte. The rerun uses working decoders. No RTL failure is inferred from the sandbox result.
- The isolated candidate's existing top-level smoke suite also passes 4/4: identity/time/SRAM, host forwarding through a lane, UART on full and lean pin units, and an SRAM routine on the rotation. Local result: `/tmp/tripwire-clean-inline-smoke.xml`.

Main's hardware, frozen specification and template GDS jobs have not been replaced by this preparation.

## Native electrical-margin experiment

Published `gds-native-margin55-screen.yaml` and `native_margin_screen.py` with scoped user approval and launched [native screen 38823883005](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38823883005) on `2d2b697fb6268d61e2d9be6df16901dc2f281b17`. At the latest check it has completed setup and is running the physical screen. Starting from clean synthesis, the native AREA1/clock8/100 ps hold-target recipe enables stock post-GRT design repair with 55% slew and capacitance repair margins. This tests whether native settings can supply the conservative electrical headroom without source-bound checkpoint ECOs. Signoff timing/load constraints remain fixed at the measured 20 ns recipe; the measured fast-hold gate remains 50 ps.

The pinned LibreLane 3.1.0.dev3 wheel exposes `GRT_DESIGN_REPAIR_MAX_SLEW_PCT` and `GRT_DESIGN_REPAIR_MAX_CAP_PCT` and passes them directly to OpenROAD's native `repair_design`. [OpenROAD documents these margin controls](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html#repair-design) as a way to compensate for the difference between estimated and routed parasitics. The selected reserve is motivated by the project's paired measurements and successful 0.45 utilization guard; it is an experiment, not evidence that native repair will converge or reproduce the checkpoint.

The screen uses the stock image and Classic step ordering, all three repair corners, identical fully timed PNR/signoff SDC, and no checkpoint edits. It stops after native post-GRT timing repair. Fresh STA plus the read-only per-net diagnostic must independently show:

1. Nonnegative setup and hold at all corners; fast hold at least 50 ps.
2. Zero slew, fanout and capacitance violations.
3. Zero antenna violations and final GRT overflow.
4. Estimated slew/capacitance utilization no greater than 0.45 at all corners.

Missing evidence fails closed. No detailed routing is included. Native timing repair comes after design repair and may consume its reserve, which is why the final measured guard is required.

The inherited checkpoint recipe disables `ERROR_ON_MAGIC_DRC` and `ERROR_ON_ILLEGAL_OVERLAPS`. The new proposal enables both. Zero detailed-router DRC is not evidence of passing full Magic DRC or LVS.

## Remaining portability gaps

Clean synthesis may choose different strengths and buffering than the accumulated checkpoint repairs. Native margins also do not reproduce the custom routing reservation, source-specific fanout/hold buffers, exact positions or the live incremental repair loop. This trial must pass its own gates; a failed screen does not invalidate the passing checkpoint, and a passing screen still needs extraction and exact-netlist protocol regression.

If native reproduction passes, review the full integration/configuration changes and run the unchanged official Tiny Tapeout flow on the complete selected design. If it fails, use the measured failing paths and loads to choose a general RTL or supported-flow repair. Do not copy synthesized instance-name ECOs into a clean build or weaken acceptance gates.

Local helper verification: 70 focused tests pass across the native margin policy, stock runner, clock clustering and saved-checkpoint STA. Physical convergence and official signoff remain unmeasured. No Phase 2 checklist box is changed by this preparation.

## Watched replay of the quiet synthesis run

Original run38823883005 remains active with its persisted log stopped at23:32:14UTC in Yosys resource-sharing activation-pattern output. The equivalent pass in successful baseline37990280838 completed in about0.385seconds. Hosted runner process state is unavailable: this is suspected stalled computation or log delivery, not a proven synthesis deadlock.

Prepared `gds-native-margin55-watched-screen.yaml`. It preserves source, synthesis strategy, all optimization passes and every physical acceptance gate. `YOSYS_LOG_LEVEL=WARNING` reduces Yosys output using the pinned step's `-q` option. Full flow output goes to an uploaded file rather than flooding the Actions console. A watchdog prints a heartbeat every30seconds with current stage, stage duration, log size/quiet duration and available container CPU/memory statistics. Synthesis has a15minute deadline checked at heartbeat intervals; the complete flow has a115minute deadline within the existing130minute step limit. Expiration returns124, preserves logs/receipt, and stops the child process group. A failure cleanup step stops remaining containers on the dedicated hosted runner before upload.

The advertised `SYNTH_SHARE_RESOURCES` flag is not a valid bypass in the pinned3.1.0.dev3 wheel: it appears only in the step variable declarations; `scripts/pyosys/synthesize.py` unconditionally executes `d.run_pass("share")`. The watched revision therefore does not set that ineffective flag or claim that sharing is disabled. No custom synthesis script/image or mapping change is introduced. If the watched run still exceeds its synthesis deadline with high CPU and unchanged output, investigate the synthesis process using the retained evidence rather than assuming log backpressure was the root cause.

76 focused tests pass, including real subprocess success/failure propagation, synthesis/total timeout termination, leaving synthesis without a false timeout, refusing evidence overwrite, and retaining the native physical recipe under the logging change. The actual CI replay is required to establish whether the apparent stall is resolved.

## Actual watched result and positive wire-limit trial

[Watched run38827554368](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38827554368) completed the screen in1919.98seconds, with exit1 and no watchdog timeout. SetupWS is0 at allcorners; fast/typical/slow hold is+101.177/+204.122/+380.307ps. Electrical counts are fast/typical1slew, slow11slew, allcorners7fanout and0capacitance. The global0.45guard also fails, so no DRT is eligible.

The full artifact proves post-GRT design repair received `-slew_margin55.0 -cap_margin55.0 -max_wire_length0.0`. It counted61slew/21capacitance problems but inserted0buffers and resized0cells. The before/after netlists are byte-identical: SHA256 `d73ed3a1d2a43a464110c40555c0bed04d83360234a036495615ee71f07df4c3`,33446cells with identical connectivity. This isolates a no-edit repair step, rather than merely assuming a later stage undid useful repair. Local independent receipt: `/tmp/tripwire-native-repair-noop-proof.json`.

Prepared `gds-native-margin55-wire200-screen` as a one-setting comparison against the watched recipe: `GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=200`µm instead of0. The pinned LibreLane variable description says0disables buffer insertion; OpenROAD's documentation distinguishes wire-length repair from electrical checks, so the zero setting is a hypothesis to test, not a proven explanation of every unresolved violation. Measure actual resize/buffer activity, area/overflow and all final strict gates. Native design repair does not generally repair clock nets; four16-load clock branches against limit8 remain a separate known issue, and this experiment does not claim to fix them.

The watchdog, stock image, source, AREA1/clock8 strategy, 100ps repair target,50ps fast-hold acceptance, fully timed20ns constraints,55% margins and all strict guards stay fixed. Early artifacts now include the actual native repair log/config/metrics.77focused tests and workflow YAML/shell checks pass. Main hardware/config and template GDS jobs remain unchanged.
