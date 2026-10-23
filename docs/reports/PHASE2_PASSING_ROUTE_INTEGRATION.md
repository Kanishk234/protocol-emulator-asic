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
