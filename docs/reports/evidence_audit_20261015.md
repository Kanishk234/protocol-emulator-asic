# Evidence audit, October 15

Phase 5 remains open. This audit checks committed reports and the downloaded
unchanged-control routing trace; it does not refresh expired historical
artifacts or establish a new chip timing result. `docs/EVIDENCE.md` now labels
historical local measurements explicitly, limits the frozen-chip STA row to
the shell, and removes a current-rate range that lacked a fresh matched-view
cross-check. No phase checklist is changed.

## Supported baseline and evidence boundaries

| Statement | Supporting evidence | Actual scope |
|---|---|---|
| Frozen G1 passes recorded TT physical/precheck and gate-level checks |36383587262 at3047dea; phase4 follow-up36451108163 | Historical frozen design. Gate-level chip tests retain fabric RTL under D-023; chip STA does not time arbitrary configured fabric paths. |
| Recorded shell setup/hold at the50MHz target are+12.48/+0.112ns |36383587262, PHYSICAL_DESIGN_AND_CI hardening table | Shell STA with black-box macro; not an end-to-end protocol-rate measurement. |
| G1 has88LC plus two timers/two shifts; design-set fit improves1/4→3/4 over G0 at equal outline/target | architecture_comparison.md; G0 hardened36353540402; G1 hardened36376994834; compiled G1 fabric36376994866 | Reported architectures and particular design parameters. Historical local synthesis/compiler tables are distinct from refreshed matched physical timing. |
| Three held-out designs run; CAN does not fit | heldout_results.md; gl_test36451108163/fabric36451328356 | WS2812/1-Wire/SWD under documented simulation and host limits; SWD packet handling is host software. No generality claim beyond these tests. |
| Formal F1/F4 unbounded; F2 bounded84cycles | formal36383587298 and historical36367067725; formal.md | Named properties only, with F2 assumptions/bound retained; not a full arbitrary-length load proof. |
| F3 depth2/depth4 FIFO unbounded |36491754401, retained engine proof logs as cited in EVIDENCE | FIFO property scope; does not prove surrounding software or protocol behavior. |
| Fresh documented reproduction succeeds |37690896748 at962da93; reproduction.md | Loaded30/30 and cosim1/1 strict XML, pinned clean hosted source; historical revision, not current unpushed fixes. |
| Compiled-C loading and ordered duplex pass simulated SPI |38293580979; status_and_hold_allocation_20261012.md |31-byte exchange on same-job hostecho image; no physical board/backend throughput result. |
| Loaded active-window cancellation passes |38676257805; WORKLOG session102 and PHASE5 final update | Exactly one loaded XML case; counter9/window256/delay4,70/88LC. USER_RESET/STOP cancellation and fresh-window checks under D-023. Earlier38676021166 used wrong parameters and remains failed. |

Numbers in the phase-1 profile are internally consistent:144+100+164+240=648;
counter150/648 rounds to23%, shift111/648 to17%, storage137/648 to21%.
They come from a historical local synthesis run, not a CI run. The later
G0/G1 placed-LC counts use a different compile/mapping flow and must not be
presented as the same measurement. The tile's approximately5090µm²/LUT is
likewise explicitly local and historical (`tile_cmos5l.md`), not fresh signoff.

## Current compact trace: retained failure, better observation

[38676688402](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38676688402)
authenticates producer38167697696, unchanged source, original routing policy
and native returncode1. Actual Metal1–4 overflows13/53/31/36 sum to133.
The collector's success is not routing acceptance. The detailed
[route analysis](route_trace_analysis_20261015.md) records target geometry and
the rejected arbitrary-net-order repeat; no physical intervention follows yet.

Retained artifact provenance (`route_trace/`):

* Native segment SHA256:
  `aee9b65f2cfc5f653793de924dedd919a7b68d67fa3ef3febf7ca17e3f1ad7ca`.
* Selected-target SHA256:
  `f00a6206d105a949428454017fe32fa6553bf07c89428c95ac1d7ead661e37d4`.
* Original routing top source SHA256:
  `9cceedd2c477f85b25362d5e3833fe0e9c0d85f14248060fc38e3fdec0c6187c`.
* Original routing common source SHA256:
  `55b64e4725fb0e58e8ca56945f2858e6f0c88c0a183252c682b63f6675e22681`.
* Observation-instrumented common source SHA256:
  `2e127c88f5ec2445bd85140cae6caf48bd7cdcc97fdf2037f1d857c82d7a74ae`.

These source hashes are from the retained runtime source manifest, rather
than hashes inferred from abbreviated worklog text. The route result reports
`source_unchanged=true`, `route_passed=false` and
`physical_acceptance=false`. Source manifests, actual segment file and target
JSON were checked locally against the downloaded artifact. Heavy EDA was not
run locally.

## Remaining blockers and corrections

| Item | Finding | Required next evidence |
|---|---|---|
| Historical primitive timing | Original matching G1 tile netlist/SPEF cannot currently be restored; newer experimental views are not substitutes | Restore exact approved views or regenerate and authenticate a separately qualified matched set. Until then label cross-check historical. |
| Numerical completeness | EVIDENCE still includes locally sourced profile, cell-area ratio, model and mutation numbers without CI production IDs | Preserve honest local labels; supply reproducible exact source/run manifests or remove unsupported numbers before closing final audit. This audit does not invent historical CI IDs. |
| Compact physical acceptance | Best fanout-clean route remains133; broad RUDY6544 and native-feedback6000 are rejected | Measured new hypothesis; unchanged control; all original guards. Only zero native overflow advances to detailed routing/extraction. |
| Complete configured timing | Positive conditional C2 cases and estimated shell guards omit required LOAD/RUN/intertile/external/annotation obligations | One matched physical build and explicit complete mode/path coverage, as enumerated in compact_timing_modes_gap_audit_20261012.md. |
| Current software/autonomy changes | Supervisor, strict XML helper and Python SPI exception cleanup have local regression evidence only | Commit/push exact source; inspect required hosted checks and clean reproduction where affected. Earlier green6a44252 does not validate later edits. |
| Phase5 summary freshness | PHASE5 header says October12; paragraphs still call D094 pending and an older buffer route queued despite later recorded rejects | Coordinator should reconcile current status and stale prospective paragraphs. Preserve useful historical outcomes with dates; do not label phase complete. |
| Final phase gate | EVIDENCE completeness, all-required-CI and phase-summary exit boxes remain unchecked | Complete those exact obligations with evidence on `efpga`; no submission work until the exit passes. |

The current phase summary does correctly record the later6000 rejection and
active-cancellation pass at its end, but those additions do not resolve its
older contradictory prospective text. This audit owns EVIDENCE and this report
only; it does not silently mark the summary or checklist complete.
