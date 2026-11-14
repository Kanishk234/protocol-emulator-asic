# Review-only source promotion plan for candidate43390348317

Status: planning and verification only. No main hardware/config/spec/template change. The routing run is an approved diagnostic, not a Phase2 pass or adoption decision. The old untracked phase2_main_promotion bundle is withdrawn and is not used.

## Exact candidate and remaining decisions

The routing input is source258186504e4b9f73d2711067e456494def705d2b, with2 lanes,4 pin units and U0 carrying the full PULSE/carrier/BITSYNC features. Main still describes3 lanes,6 units and U0/U1 full. Preserve the owner's2/4-first direction, explicitly reconcile the full-unit mask/counts in the architecture/spec decision, and do not silently substitute a3/6 build after timing qualification.

Every Verilog/header byte used by the parallel tests matches the downloaded routing input and fresh preparation. The prepared candidate's `tools/gen/gen.py --check` passes; encodings remain generated from the candidate YAML. Source/config/macro inventories and the26 project-config differences are recorded locally in `/tmp/tripwire-pending-final-verification/integration_review.json`.

## Clean-checkout requirements

1. Stage a new isolated preparation from current main, then overlay the selected qualified source/spec/generated tables, top wrapper, SRAM blackbox, PDN input, info.yaml and tests. Do not apply the withdrawn setup/template patch.
2. Package the exact SRAM views or use an independently validated stock-PDK macro reference. The current candidate points into `macro/RM_IHPSG13_1P_512x16_c2_bm_bist`, while main tracks no macro files. The unchanged official GDS job does not run our diagnostic fetch step. The candidate contains8 pinned views totaling1,103,560bytes. Vendoring needs the upstream license/provenance and recorded hashes; no workflow-fetch injection is proposed.
3. Reconcile all26 config differences explicitly, including macro/PDN and supported native physical controls. Experimental approval is not a substitute for reviewed main adoption under the repository's config policy. Do not copy generated user/config_merged or absolute runner paths.
4. Keep info.yaml source_files and test/Makefile PROJECT_SOURCES synchronized, excluding the synthesis-only SRAM blackbox from simulation sources and retaining macro models/UDP support for gate-level tests.
5. Treat the verified C-pad width cleanup as an explicit source delta. If adopted, give the final source a new fingerprint and run required validation on those exact bytes; do not claim the older routing artifact validates a changed source.
6. Re-run generator checks, strict lint, unit/chip/SRAM checks, million-clock lockstep and its mutation checks, plus protocol replay on the selected final source. Gate-level evidence must name the actual final routed netlist; old R4 GL evidence is not evidence for this source.
7. Run the unchanged official GDS workflow from a clean checkout, with final timing, DRC/LVS/antenna, precheck and GL all passing. Reconfirm the official action's current engine/tool identity before promotion; do not alter its jobs or silently force an old engine.

## Parallel evidence available now

Chip/SRAM-rotation RTL checks pass6/6 on the exact candidate. Fresh one-million-clock RTL/model lockstep passes with zero divergences (527.82s). This is the deterministic L2 scenario, not a whole-design formal proof or refreshed mutation evidence. Read-only audit43629200280 reports estimated functional setup reserve fast12.527966ns, typical8.897943ns, slow2.533495ns across2414flop endpoints and24outputs. It preserves ordinary all-endpoint checks and source view hashes. These are global-route estimates, not extracted timing.

The worst reported slow path is U1 PIN_A[4] configuration latch to U2 RX rt[23]. Seven hold-delay cell arcs on that path sum4.752074ns. This is a path-budget measurement, not a removable delay budget: each cell may protect other fast-corner paths. Use the final extracted setup/min reports before proposing changes.
