# Phase 2 resume review — 2026-11-02

Reviewed repository instructions, current worklog/decisions/bug evidence, architecture and verification contracts, Phase 2 exit checklist, physical workflow definitions, local changes and processes, live GitHub main/workflow status, and the final raw measurements from the last launched experiment. This is a status review, not a claim to have re-verified every source line or rerun the full physical/RTL suites.

## Repository and workflow state

- Local HEAD, origin/main and remote main are `d2c07b3e6772f6d99c3743d0808d2d8b2c1c062f`; there are no unpublished commits.
- No workflows are in progress. Two queued diagnostics date from 2026-10-07: L3 37655518919 and extracted timing 37655518925. They are stale queues, not current work; no cancellation or rerun performed.
- Latest main test 40808353191, lint 40808353158, unit 40808353207 and docs 40808353156 all pass. Nightly runs through 41487087016 (2026-11-02) pass. This does not make the failed physical screen green.
- No local Icarus/VVP/Verilator/Yosys/OpenROAD/LibreLane processes were found. No watcher was started.
- On arrival, four tracked documentation files were modified and older diagnostic notes/tools were untracked. They were preserved. The FIPE note stays local and unignored. No uncommitted main RTL, info.yaml, macro or official workflow edits were present.
- `src/tt_um_tripwire.v` is still the counter placeholder; info.yaml and test/Makefile both list only that top. Core modules exist, but the selected full optimized 2-lane/4-unit/U0-full/SRAM design is reconstructed by hash-guarded diagnostic patches. Official GDS on current source would not verify the full candidate. The official workflow hash still matches the frozen design manifest; its jobs remain unchanged.

## Last experiment: qualified timing, failed electrical/antenna/routing

[40808367962](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40808367962) completed in about 3h51, with stock flow, native-effect audit and repeated corner measurements successful. Only strict final qualification failed. Artifact 12878441353 is 263764479 bytes. Selected raw reports were retrieved; all before/after corner metrics and fresh antenna values independently match the receipt, and the final late-route Total row independently reports 174 overflow. Both requested optimizer targets executed (275 ps early, 75 ps late), with clock diameter100µm/size8 retained.

| Measurement | Best clock100 reference 40779354529 | Last early275/late75 40808367962 |
|---|---:|---:|
| Setup WS, fast/typical/slow | 0 / 0 / 0 ns | 0 / 0 / 0 ns |
| Fast hold | +93.5213 ps | +83.2385 ps |
| Typical hold | +340.985 ps | +255.152 ps |
| Slow hold | +739.804 ps | +555.838 ps |
| Slew/cap violations | 0 / 0 | 0 / 0 |
| Fanout violations per corner | 0 | 1 |
| Antenna nets/pins | 5 / 5 | 10 / 10 |
| Final GRT overflow | 0 | 174 |
| Reported instance area | approximately 674347 µm² | approximately 707734 µm² |
| Instance count | 45015 | 47357 |

The last schedule adds approximately33387µm² and2342instances, with more antenna failures and congestion. Do not promote or repeat it without new evidence. Keep clock100 as the stronger measured reference. Zero setup WS is not demonstrated positive setup margin. Neither result is detailed-routed, extracted signoff or official GDS success. Exact new data and report hashes are in `spikes/phase2_stock_flow/early_repair_schedule_result.json`.

## What remains and the next decisions

1. Retain the clock100 source/config as the reference and stop treating the early275/late75 or no-mirroring controls as selected improvements. The fixed final gates remain setup/hold nonnegative, fast hold at least50ps, and zero electrical/antenna/overflow.
2. Target its five data-net antenna failures with a source-bound diagnosis and one controlled change. Prior evidence establishes all five branches exist before antenna repair and become violating after later physical operations. Native antenna protection reaches zero before late repair; the earlier snapshot still fails fast hold, so skipping late repair alone is ruled out. Broad diode insertion has a large estimated area/capacitance cost and is not a blind next run. Additional global margin sweeps are unsupported by the new regression.
3. Review official-flow configuration portability in parallel before promotion. The experimental recipe includes hold, clock-clustering and repair settings beyond the current AGENTS.md whitelist for src/config.json (clock period, density and SRAM block only). Do not silently copy these settings into main or modify official template jobs. A permitted recipe or an explicitly reviewed owner decision is needed before main adoption.
4. Obtain a fully qualifying screen on one final physical checkpoint. Then continue that exact candidate through detailed routing, extraction and complete timing/electrical/antenna/DRC/LVS checks. A screen pass alone is insufficient.
5. Replay the whole supported protocol test suite on the exact final netlist, with independent decoder checks retained. Previous 22/22 local RTL tests and module equivalence are valuable but do not establish final routed behavior or exhaustive protocol conformance.
6. Promote the coherent full candidate into the official entry point and synchronized source lists, with reviewed project configuration; rerun applicable unit/lockstep/formal evidence for that revision. Run unchanged official GDS, precheck, gl_test and viewer, and require the final timing/violation requirements on that full design.
7. Reconcile Phase 2 exit checklist/area evidence to that final revision and keep all required main CI green. Several existing checks cite historical candidates or typical-corner-only passes; they do not establish closure of the current stronger target. Phase 2 remains open; do not begin Phase 3 work or tick completion now.

## Local validation and changes in this review

- 80 diagnostic gate/profile/checkpoint tests passed.
- `tools/gen/gen.py --check`: all generated outputs up to date.
- `git diff --check`: passed.
- No new experiment, commit, push, hardware promotion, official workflow edit, watcher or phase tick performed. Only this review, measurement evidence and session status documentation were added locally. Older dirty work remains preserved.
