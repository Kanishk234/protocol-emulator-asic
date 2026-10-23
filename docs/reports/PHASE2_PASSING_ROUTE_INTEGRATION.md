# Passing route: official integration review

## Evidence as of 2026-10-22

[Route 39868597887](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39868597887) passes the measured extracted gates for the full 2-lane/4-pin-unit/U0-full/SRAM candidate at 20 ns. Setup worst slack is 0 ns at all three corners; fast/typical/slow hold slack is +0.107281/+0.218980/+0.415700 ns. Actual slew/capacitance/fanout violations, antenna violations and detailed-route DRC are zero. This is experimental physical evidence, not official signoff.

[Final routed protocol replay 39880054906](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39880054906) is running at published main ced952c413ac15b73eea0d6402c985dc92984677. Its artifact validation step passed; its 22-test simulation is in progress. The earlier 22/22 preparation replay does not substitute for this final-netlist replay.

## Isolated source integration

Prepared `/tmp/tripwire-official-mux-candidate-20261022` from tracked main tooling, frozen candidate 3393eea9a58c5cad9077cc360a8515d0e5ec8284 and exact successful route source files. Main hardware, template jobs and unrelated local files remain untouched. The directory is temporary review material, not a durable published candidate.

- Regenerated encodings/spec documentation and ran generation check. Every bound source hash remains identical to the routed source.
- All 19 source files exist; `info.yaml` and `test/Makefile` lists match. Metadata specifies 6×4 tiles and 50 MHz.
- Local top-level RTL smoke tests pass 4/4 with no failures or skips: identity/time/SRAM, lane forwarding, UART TX on full and lean units, and routine execution. Tests use the project venv and system Icarus 12.
- `review/source_audit.json` records source checks, test names, configuration differences from both main and the frozen candidate, and unresolved portability issues. Raw test output stays outside git.

## Remaining integration problem

The passing process uses an instrumented OpenROAD image, a second audited repair stage (81 buffers, 14 cell-strength substitutions), incremental placement/routing refresh, then detailed routing and extracted checks. The stock Tiny Tapeout action does not install that image or execute that second stage. Merely copying the successful RTL and config into main would not reproduce the passing process.

The isolated `review/official-config-proposal.json` is unapplied and incomplete: it preserves the measured clock/constraints and enables Magic DRC/overlap errors, but does not implement the missing physical stages. It is not an official-ready recipe. Several proposed settings exceed AGENTS.md's allowed main-config edits; template job bodies are also protected. No such policy exception is assumed or implemented.

Next, finish the exact routed replay, then develop and test a continuous full-flow integration that carries the reviewed repair process and continues through final physical verification. Only a demonstrated portable integration can justify promoting the complete source/config candidate and launching official GDS. Official GDS, LVS, precheck, gate-level testing, viewer and all remaining Phase 2 checklist evidence are still required. No phase boxes changed.

## Parallel physical verification diagnostic prepared

Prepared separate `gds-wire600-mux-signoff` workflow and `wire600_mux_signoff.py` to run stock GDS stream-out, Magic DRC, SPICE extraction/overlap checking and Netgen LVS on this exact passing route. This can identify remaining physical-verification issues without waiting for full recipe integration. It is not the official template workflow and cannot close Phase 2.

Its additional fixture binds 15 extracted-state/config/view files. Original synthesis JSON/header views are absent from the route artifact; the diagnostic explicitly omits only these unused metadata views from its initial state. Physical geometry, powered and logical netlists, constraints and extracted views remain unchanged. The selected stock tail steps do not consume the omitted views. No placement or routing repair runs in this diagnostic.

Actual full-artifact preflight passed locally. Thirteen focused tests passed, including rejection of missing/failing DRC metrics and inherited GDS from the other export step. Fresh Magic DRC, overlap and LVS counts must each equal zero; missing output fails. Each tool must produce its own nonempty GDS. KLayout DRC/XOR remain unverified, consistent with their disabled settings in the bound recipe. No diagnostic CI result exists yet; files are local pending user publication under the latest supplied Git rules.

## Results and next independent precheck

**2026-10-23 result:** [exact-GDS precheck 39890538270](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39890538270) succeeds. Downloaded `precheck_reports/results.xml` independently confirms all nine applicable checks pass, with no failures/errors/skips: KLayout pin-label overlap, SG13CMOS5L DRC, zero area, general checks, pins, boundary, layers, cell names and analog pins. CMOS5L DRC itself took 8276.18s. This establishes unchanged TT precheck acceptance of the exact primary exported GDS despite the separate raw Magic diagnostic failure. That failing job remains failed; no waiver or gate edit was applied. Official main GDS/source-recipe integration and Phase 2 closure remain unfinished. The preparation narrative below records how this test was assembled.

## Fresh integration proof prepared

Prepared separate `gds-wire600-integrated-proof`: one hardening job executes fresh RTL synthesis, the same reviewed identity/strength repairs, strict measured preparation gates, detailed routing and extracted gates, then fresh stock GDS/LEF export and LVS. A dependent job runs the unchanged TT precheck on this newly generated package. No physical checkpoint artifact is downloaded; native tool state passes between normal helper invocations within the same live workspace. This is a continuous source-to-GDS workflow, not a single LibreLane invocation or an already integrated official main build.

Live provenance binds the actual current run ID/main head/workflow, rather than pretending this execution is the historical clean screen. The former 244-file downloaded-artifact forensic binding included process statistics and logs; the fresh execution retains its 56 physical/source/constraint/audited-state/proposal identity files and independently reevaluates current measurement reports through the unchanged routing helper. Historical fixture data remains unchanged. An actual historical-artifact check passes this identity-only binding; the new execution must still demonstrate reproduction.

Final fresh routed netlist must match SHA c60823d33a9aa63b20ff4e07a934a4f1daa8b519c4ef2581c9d0b53599f13225, the exact netlist with 22/22 protocol replay evidence. A different netlist stops before export. The export stage requires fresh zero-error LVS and records/classifies all ten expected abstract-view overlap markers. This integration experiment does not rerun raw Magic DRC or claim its old failure is cleared. Merged-GDS DRC acceptance remains the real unchanged TT precheck; no failed check is converted to success. Receipts retain official_signoff=false and precheck_passed=false until the dependent external check actually runs.

32 focused tests pass, including foreign provenance, stale workspace, failing LVS, inconsistent overlap counts, foreign GDS, malformed DRC, unchanged precheck invocation and no physical-artifact download. Actual prior exported evidence still classifies identically after extracting the shared overlap audit. Main hardware/configuration and template jobs remain untouched. Full official integration still needs a reviewed way to carry the custom repair execution into the protected template flow; this experiment alone cannot close that policy/portability gap.

The diagnostic was published at 8cfdfce14dcdf070a6daded58d142b3123a447cd and ran as [39883160399](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39883160399). Both GDS exports completed. Netgen LVS reports zero errors and zero device/net/property/pin differences. Strict raw Magic checks correctly fail on 57,924 DRC markers and 10 illegal-overlap markers. This result does not satisfy the diagnostic's zero-marker gates.

Downloaded full artifact `wire600-mux-signoff-39883160399` under `/tmp/tripwire-mux-signoff-39883160399`. All 57,924 DRC rectangles are contained in the SRAM footprint (12,40)–(248.8,231.34) µm; none is outside. Seven rule categories account for the entire count. The total matches the historical R4 run5 baseline documented in `R4_FLOORPLAN.md`, which also recorded a successful precheck. Matching count and containment are consistent with the known macro baseline, not proof that every marker is harmless. All 10 feedback polygons are `obsm4-metal4.ILLEGAL_OVERLAP`, confined to the four VPWR stripe columns and the FS-macro obstruction gap y186.135–192.255µm described in `src/pdn_cfg.tcl`. No violation is waived by this classification.

[Final routed replay 39880054906](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39880054906) now succeeds. Downloaded XML independently confirms 22 cases, zero failures, errors or skips on the exact final routed netlist. This replaces the earlier pending status for that replay.

Prepared `gds-wire600-mux-precheck`: bind nine exact exported-GDS/signoff evidence files, classify raw markers, copy the primary KLayout GDS and fresh LEF unchanged into a 6x4/50MHz package, then invoke the unchanged `TinyTapeout/tt-gds-action/precheck@ihp-cmos5l` action. The package names top `tt_um_tripwire`, specifies CMOS5L, and supplies the metadata/LEF expected by the precheck CLI. Local actual-artifact packaging passes, including hashes and spatial classification; 19 focused checks pass. The original failing Magic diagnostic remains a failure. Precheck must independently check the merged physical layout; no result is assumed. This separate workflow is experimental precheck evidence, not completion of the official main `gds` workflow or Phase 2.
