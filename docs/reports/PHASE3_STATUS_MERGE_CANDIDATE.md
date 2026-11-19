# BITSYNC status merge: minimized defect and scratch candidate

The native status-collision failure is now reduced to four accepted tokens: at clocks3/5/7/8, CTRL LINE0xA001 (arbitration readback), DATA0, CTRL SYNC0x5000, DATA0. The [compact input fixture](../../formal/fixtures/pin_unit_status_collision_minimized.json) retains the real synchronized input sequence and configuration; it drives original RTL without internal state initialization or forces. The testbench also checks stable pending TX tokens.

At clock9, the previous bit's readback sample and the next frame's bit boundary/start coincide: `smp=1`, `bnd=1`, `o_start=1`, `jn=0`. The producer is blocked and the pending status register empty. Readback and frame-start intents both arrive; only the prioritized readback status can be retained. Native `st_new` collapses them into one Boolean, and native OVERRUN remains0. This violates P26's requirement that a second status token which cannot be retained is dropped with OVERRUN. P25 permits the next marker once queued bits are consumed; no contract requires waiting until the old bit's readback sample before accepting SYNC. No dedicated protocol behavior or new architectural feature is needed.

The earlier status report retained admission as unresolved. This minimized sequence establishes a native status loss-accounting defect at this command boundary. It is simulation/formal-counterexample evidence, not an observed failure on manufactured silicon or proof that all shipped personalities hit this path. Existing physical timing/GDS evidence remains the result for the unchanged qualified source.

Run with the project venv active:

```sh
python scripts/replay_pin_unit_status.py
python scripts/check_status_merge_candidate.py
```

The first command reproduces failures on original and minimized native inputs and the finite idle4 controls. It explicitly records `formal_gate_passed=false`. Raising IDLE_BITS only removes those particular finite collisions; it is not adopted as a general protocol restriction or fix. The [native replay receipt](phase3_pin_unit_status_replay_result.json) binds these observations.

## General repair candidate

The [scratch patch](../../spikes/phase3_status_merge/status_merge.patch) preserves each new status intent until capacity is assigned. Old pending status has priority; readback, frame-start and refused status retain their existing order. A frame still takes producer priority. The current output plus the existing one-entry pending register can accept up to two statuses; any excess sets OVERRUN. If a new status goes directly to a free producer, the next status may now fill the existing pending register. No additional state registers or protocol-specific block is introduced.

The old assertion that two status events never coincide is false. The candidate replaces it with a loss-accounting assertion, while the independent reference matrix checks selected output, pending token and exact overflow behavior. Main RTL and its original assertion are untouched; the patch is applied only to ignored build copies. This assertion replacement is explicit, not a passing claim obtained by suppressing the native failure.

## Validation completed

| Check | Result |
|---|---|
| Original and minimized collision replays on candidate | Complete, collision reports OVERRUN1 |
| Native merge matrix, 64 combinations | PASS |
| Three deliberate merge faults | Rejected by reference matrix |
| Existing full pin-unit suite, Icarus | 60/60, no failures/skips |
| Existing full pin-unit suite, Verilator | 60/60, no failures/skips |
| Whole-chip protocol/Phase3/metamorphic suite, Verilator | 55/55, no failures/skips |
| Queue cone and qualified-cache full-unit safety | Unbounded PDR PASS; bounded covers PASS |

The matrix enumerates old pending status present/absent, all eight combinations of three status intents, frame intent present/absent and producer free/busy. It forces only those upstream intent boundaries in the actual candidate BITSYNC module and checks a list-based output/pending/loss oracle before and after one edge. It is exhaustive over these Boolean arbitration combinations, not an unbounded full-engine proof or all payload/state combinations. Fault controls lose the second buffered status, suppress overflow, or bypass older pending data; all fail the matrix for the intended semantic reason. The [candidate receipt](phase3_status_merge_candidate_result.json) records patch/source/runner/fixture/XML/log identity and explicit non-adoption/non-qualification fields.

## Remaining gates before adoption

[Unbounded queue and actual full-unit integration proofs](PHASE3_STATUS_MERGE_FORMAL.md) now pass with their explicit premises; actual-engine triple-status exclusion is proved rather than assumed. The selected55-case whole-chip/protocol regression also passes. Physical timing, area and routing evaluation on this single candidate is next. Extra storage is zero, but added data selection and overflow logic can affect mapping and timing; no area or timing cost has been measured. Main has approximately163ps of reported functional slow-setup reserve, so the extension is not automatically safe.

Only adopt after those results justify it, then requalify through the unchanged official GDS flow. No Phase 3 checkbox is ticked by this candidate, and no new physical pass is claimed. Publication remains separate from adoption.
