# Main promotion and official-flow setup review

Status: prepared locally; protected main configuration and GDS job patches are unapplied. No Phase 2 boxes are closed by this proposal. D-108 requires owner approval for the two project-policy exceptions.

## What is promoted

The exact full 2-lane / 4-pin-unit / U0-full / SRAM RTL from successful fresh reproduction39907035580. The hardware stays at20ns/50MHz and6x4. No RTL logic was changed to make lint pass. Generated definitions, fabric, model encodings and architecture documentation come from the matching canonical specification. Main's placeholder top and tests are replaced with the real chip's wrapper and top-level host/SRAM/lane/UART/routine tests.

The scoped patches are prepared at:

- `/tmp/tripwire-official-mux-candidate-20261022/review/main-promotion.patch`:22source/spec/generated/test/metadata/documentation changes, including the proposed main config.
- `/tmp/tripwire-official-mux-candidate-20261022/review/official-gds-setup.patch`: the exact protected job changes.
- `/tmp/tripwire-official-mux-candidate-20261022/review/protected-config-diff.json`: all37config-key changes from current main.

Both patches pass `git apply --check`. Runtime preparation pins30source/config/test/metadata files and8macro views by SHA256; generated TT user_config is deliberately not treated as a tracked input. Unused legacy pnr.sdc is not promoted. Both actual PNR/signoff constraints use fully timed signoff.sdc.

## Official action integration

Keep the actual Tiny Tapeout GDS action as the entry point. A new setup step fetches and verifies pinned macro views, binds the live main/run/commit context, builds a local container image and selects that image through LibreLane's existing image override. No image is published to a registry. The action's own tt_tool --harden invokes registered flow TripwireReproduced inside that image.

The flow executes the already tested fresh chain in one live container, through normal native child LibreLane invocations. It does not download physical checkpoints, invoke nested Docker, import an old GDS, or synthesize a smaller design. The original Docker backend remains the default for existing diagnostic jobs. Native mode requires an explicit reviewed-image marker. Actual pinned Tcl instrumentation matches the passing image exactly; only the selective target script's source path changes.

Fresh final State views, metrics CSV and the real lint/synthesis/placement/STA directories are exposed under runs/wokwi, as the TT tooling expects. Physical chain directories are linked there for failure artifacts without recursive links. The original merged config and temporary helper alias are restored/removed on success or failure. Actual container image ID is recorded separately; legacy helper image names denote the two instrumentation modes inside the combined image.

Main declares the final physical policy. The plugin reconstructs the verified initial configuration before its existing transformations: refeeding final clock-cluster/repair settings into those guarded transformations would be invalid. The real transformation functions reproduce the complete passing config semantically. Native config validation permits JSON ordering/whitespace differences only: every key/value must still match the source-bound recipe. Physical views, constraints and connectivity remain hash/audit bound.

## Protected changes needing approval

AGENTS.md says “Never edit the template's jobs” and restricts main config edits to “CLOCK_PERIOD, PL_TARGET_DENSITY_PCT and the SRAM macro block”. This proposal needs these narrow exceptions:

1. Allow the measured physical settings and registered flow/context in src/config.json. These include AREA1 synthesis, density56, clock cluster8, GRT adjustment0.16, wire repair600um,55%native electrical repair margins,125pshold repair target, all three repair corners, and explicit signoff constraints. Clock20ns,50psminimum fast-hold acceptance and all measured preparation/extracted gates stay fixed.
2. Add one setup step and read-only contents/actions permissions to the gds job. Pin the official GDS action to3412659307918422f3f0727917cf9b499aaca588, the installer/action source used by successful39907035580; pin TT tools tod66cf179e7bc4d296362ab7e2e3b344dc3c4f665 and LibreLane3.1.0.dev3. The official precheck/gl_test/viewer jobs remain unchanged.

The custom flow uses the same selected export/LVS chain as successful39907035580. It does not rerun raw Magic DRC, and it records the10expected macro-view overlap markers. The earlier raw Magic job remains failed; no zero-Magic claim is made. Real merged-GDS DRC acceptance is the unchanged official TT precheck, already demonstrated with zero violation items. Whole-workflow success still requires that downstream job.

## Verification and integration fixes

- Full isolated scripts/check_all.sh passes: source-list/generation checks, top lint, synthesis sanity with real clock-gate library declarations and allowed latch stores, sigrok smoke,340tool tests including slow tests, and4top-level RTL cases.
- New promoted RTL passes1,000,000L2comparisons with zero divergences in562.67s against the independent model.
- Lean/full pin harnesses pass60/60each, zero skips, with their new carrier/delta ports wired automatically when present.
- Official-style local GL on exact routed NLc60823... passes4/4 in166.47s using pinned Icarus13 and cell/SRAM models. The earlier expanded22-case replay remains tied to the same netlist.
-126targeted repair/runtime/Tcl/check tests and4real LibreLane API/plugin tests pass without skips. This includes mutation-anchor/isolated-build/lint/latch-isolation tests. Actual package import also succeeds outside the project directory.
- Compiler loader test now derives expected unit count from the model instance instead of hardcoding6. Empty sigrok output in sandboxed runs was traced to libusb initialization; all decoder tests pass outside that sandbox.
- Narrow lint annotations cover bounded address comparisons and named dead/lean-only signals in the byte-identical RTL; unrelated warnings remain fatal. Our own lint/unit workflows and local scripts include the SRAM blackbox.
- L2 fault tests now use fresh per-case compile/results directories and support the late-cursor form. The previous shared compiled model could be reused across source directories. Fresh unmodified rx/cursor baselines pass; priority-flip is detected at99compared clocks and cursor-off-by-one at326directed clocks. The old ignored default compilation cache was cleared.

The Docker image cannot be built locally because Docker is unavailable. Separate official-flow-package-check performs only image/plugin/native-instrumentation checks in CI, without synthesis or routing. A complete physical run through the official adapter is still required; the first official GDS run is that integration validation, not a new timing candidate.

## After approval

Apply the reviewed source/config/template patches, verify generation/source bindings, commit in scoped groups and push main once. That hardware push starts the actual official GDS workflow. Inspect its real GDS, timing/electrical/antenna/LVS, precheck, GL and viewer results before updating Phase2exit evidence. Preserve unrelated modified reports, local tools and the local-only FIPE note. No additional timing screen is planned unless an actual regression needs diagnosis.
