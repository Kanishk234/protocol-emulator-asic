# Pad-owner factoring: next native screen

## Why this change

Extracted diagnostic [43629225955](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/43629225955) has three slow setup failures, worst -0.783631 ns. All start at U0 config word0bit7. The worst path first crosses the programmable output-owner mux, then pad readback/input selection, event generation and fabric selection. Route DRC, electrical and antenna checks pass; hold slack is positive at all corners. This is not Phase 2 completion.

Factor the mutually exclusive owner choices as OR terms instead of a procedural priority chain. Keep owner registers, write/read behavior, A-over-N priority, reset, output enable and cycle behavior unchanged. No new state, protocol-specific function, or architecture change. Only `src/trw_pins.v` changes in a prepared candidate; main RTL is not edited.

## Matched local comparison

Standard-cell area excludes SRAM macro and physical repair cells. STA uses an ideal 20 ns clock, no routed parasitics, identical Liberty files and mapping options. These values cannot predict extracted signoff.

| Variant | Cell area (µm²) | Slow flop reserve (ns) | Slow SRAM reserve (ns) | U0 config-bit launch reserve (ns) |
|---|---:|---:|---:|---:|
| Exact pending-event reference | 414910.6416 | 5.944 | 6.588 | 6.117116 |
| Parallel A/S selection | 414360.3870 | 5.358 | 6.724 | 5.533123 |
| Direct joint pad decode | 417170.3256 | 5.745 | 5.745 | 7.108249 |
| **Owner OR factoring** | **414037.0080** | **6.125** | **6.125** | **6.801030** |

Choose owner factoring for the next screen: improves the measured launch cone by 0.683914 ns, overall flop reserve by 0.181 ns, and reduces mapped area by 873.6336 µm² (0.21%). SRAM reserve regresses by 0.463 ns; monitor it. Parallel A/S regresses the actual target cone; reject for physical testing. Joint decode improves that cone but increases area and regresses overall/SRAM reserve; retain as an unselected local experiment.

## Verification and provenance

- Exact source screen43390348317; one-file patch/reference/candidate hashes in `spikes/phase2_stock_flow/pad_owner_or/candidate.json`.
- Yosys equivalence:147 points pass for NU4 and NU6. Owned-output polarity mutation is rejected.
- Owner candidate protocol replay:22/22 pass, zero skips/failures. Verilator RTL, optional sigrok annotations disabled; independent protocol waveform/reference checks remain. This is not final-netlist validation. XML digest recorded in candidate.json.
- Parallel A/S prototype also passed22/22; functional correctness alone did not justify physical testing.
- Eight focused helper/workflow checks pass, including bad input/patch rejection, reapplication rejection, unchanged runtime/gates and shell syntax.
- Actual archived source patched successfully; resulting source equals the source used in owner protocol replay. Other source files unchanged.
- Raw logs/builds remain under `/tmp/tripwire-selector-refresh-43629225955`; never commit them.

## Prepared workflow and stopping point

Manual-only `.github/workflows/gds-official-dev4-pad-owner-screen.yaml` reproduces the preceding source-preparation stack, then applies this one hash-bound RTL patch. All existing native runtime/repair/signoff steps and project settings are unchanged. Gates require the completed22-case replay receipt and exact reference config hash before source preparation. No new route or antenna exception is authorized by this screen.

Prepared locally, not committed, pushed or launched. The supplied AGENTS.md Git rule assigns history/remote changes to the user. After publication, dispatch this workflow manually. Inspect all estimated timing/electrical/antenna/overflow gates before selecting detailed routing. Passing this screen still requires extracted timing, final protocol GL, unchanged official GDS and precheck before Phase 2 completion.
