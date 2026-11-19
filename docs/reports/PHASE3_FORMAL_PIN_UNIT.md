# Pin-unit sticky flag integration: scoped lean milestone

The actual lean `trw_pin_unit`, RX, TX and pin-input modules pass local unbounded ABC PDR checks for sticky flag priority, RX gating and token selection. Both default parameters and the cache parameters used by the qualified chip are checked. Reachability and deliberate fault controls accompany the proof. The [receipt](phase3_formal_pin_unit_result.json) records source/runner/tool identities and evidence hashes.

Run with the project venv active and OSS CAD Suite appended to PATH:

```sh
python scripts/formal_pin_unit.py
```

This command is included in our separate `formal` workflow; its remote execution is pending. Official workflows and production hardware remain untouched. Full/BITSYNC tasks are deliberately outside the default passing suite and remain an open acceptance obligation; `--full` attempts them and rejects failure or timeout.

## What is proved

For FULL=0, the actual sticky `overrun` and `late` registers clear on reset/restart; otherwise they equal the previous clock's set indication OR the retained flag when not cleared. A simultaneous set wins over clear. RX loads require a free producer; selected tag/data match the native RX result. No producer storage is abstracted into this task: the earlier [RX/producer proof](PHASE3_FORMAL_PIN_RX.md) checks that storage composition separately.

Proof assumptions: initial synchronous reset followed by deassertion; static arbitrary configuration; PERIOD at least 256 fixed-point ticks (one clock); `live` cannot fall after activation; an unconsumed TX token remains available with stable tag/data. For cache parameters, cached inputs match their configuration-derived values and `idle_next=idle` in this static-configuration scope. These are explicit interface premises, not a whole-chip proof that every configuration/host transition satisfies them.

The runner copies native RTL into ignored build storage and inserts only includes of the reviewed property files before `endmodule`. It verifies that removing each include restores the original source exactly. Native source hashes are checked unchanged after the run. All native assertions remain enabled. Technology mapping is followed by symbolic replacement of undefined bits, permitting either value rather than assuming zero.

Two depth-16 cover tasks demonstrate set-winning-clear and successful clearing of an already set flag. Five scratch faults reverse set/clear priority, forget sticky state, ignore clear, ignore restart, or corrupt selected RX data. Each must produce FAIL with a VCD counterexample; errors/timeouts cannot count as rejection evidence.

## Full-unit investigation remains open

The native full unit adds ordinary RX events competing with BITSYNC frame/status output. Its property include checks producer gating, merge priority, blocked frame overrun, status overflow and pending status retention. Those checks are prepared, but no full-unit unbounded PASS is claimed.

Unrestricted inputs first produced counterexamples to the existing BITSYNC assertion forbidding two status events in one clock. A narrower replay with static configuration, legal period and monotonic live still collided, but used STUFF_N=2 and IDLE_BITS=1, below the documented threshold in ARCHITECTURE P20. Icarus replay of the original RTL reproduced the assertion at cycle29, with readback and frame-start status simultaneous and overrun low. Raising only IDLE_BITS to4 made that same finite replay pass. Both default and qualified cache parameter sets reproduced the invalid-configuration case. This is not evidence of a supported-configuration hardware defect, nor proof that all invalid inputs are benign.

Further full-unit proof attempts constrain SAMPLEOFS below PERIOD, nonzero IDLE_BITS, and the documented stuffing/delimiter threshold, alongside the interface premises above. A broad full proof was interrupted without a result. The qualified full task has a 120-second limit and returned FAIL after about95seconds, again at the native status-collision assertion (step10), with its diagnostic/witness hashes recorded in the receipt. Native status-collision assertions are retained, never assumed true or removed. Full-unit cover witnesses establish reachability only, not safety proof.

F-CHAN-4 and the aggregate Phase 3 formal exit remain unchecked. Physical closure and the qualified official GDS result are unchanged; no architecture change, analog or silicon claim is made.


## Later counterexample: open admission/status-arbitration issue

The qualified full task returned another counterexample after applying those premises. The compact [input fixture](../../formal/fixtures/pin_unit_status_collision.json) and `scripts/replay_pin_unit_status.py` reproduce it with original RTL, FULL=1 and all three qualified cache parameters enabled. No formal state initialization or property injection is used in this replay. Configuration uses PERIOD=738 fixed-point ticks, SAMPLEOFS=704, SJW=256, STUFF_N=0, IDLE_BITS=1, DELIM=0, CRC_WIDTH=9. The replay retains other symbolic choices from the formal trace; command/configuration admission is still under review.

At cycle9, native readback and frame-start status indications coincide, the original assertion fires, and the combined overrun indication is zero. Both status intents feed the single `st_new` path, with readback selected ahead of frame-start data; whether that execution must be admitted by the intended contract remains unresolved. Raising only IDLE_BITS to4 makes this finite replay complete. That control is not a universal workaround and is not an adopted restriction.

The [replay receipt](phase3_pin_unit_status_replay_result.json) binds fixture, runner, original RTL and both finite outcomes. Script exit0 means the diagnostic was reproduced and its finite control completed; `formal_gate_passed=false` remains explicit. This diagnostic is excluded from the default passing formal CI suite; the full proof remains visibly open, and its native assertion is neither removed nor assumed. BUGS records the unresolved status-arbitration/admission issue. Do not claim full F-CHAN-4 or relax the phase requirement based on the lean result.

Follow-up: [minimized status-merge evidence](PHASE3_STATUS_MERGE_CANDIDATE.md) resolves the retained command-boundary case as a P26 loss-accounting defect and tests a non-adopted generic candidate. The historical full proof remains FAIL; the new finite candidate results do not turn that receipt into PASS.
