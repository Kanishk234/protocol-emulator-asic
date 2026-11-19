# Native channel composition: first formal milestone

On 2026-11-19, three unbounded ABC PDR proofs and two bounded reachability tasks passed against the actual producer, consumer-port and full fabric RTL. Five deliberate scratch RTL mutations each produced a semantic FAIL with a VCD counterexample. The [receipt](phase3_formal_channels_result.json) records source/tool versions, statuses and evidence hashes. Raw outputs remain in ignored build artifacts.

Run from the repository root, with the project venv active and OSS CAD Suite appended to PATH:

```sh
python scripts/formal_channels.py
```

The separate `formal` workflow runs this command and uploads logs/witnesses. Its first remote execution is pending; this report records local evidence only. Official Tiny Tapeout workflows and qualified hardware are unchanged.

## Exact scope and assumptions

The harness composes `trw_chan_prod`, `trw_chan_port` and `trw_fabric`, including native producer release logic. One HOST_IN producer feeds four blocking lane consumers. Reset is asserted on the initial clock and held deasserted thereafter. Configuration completes before traffic and stays fixed: all four blocking consumers enabled, accepting all tags. Tokens are arbitrary 18-bit values, requests and consumer takes arbitrary each clock.

An independent ghost ledger tracks the accepted generation and its four outstanding consumers; it never controls the RTL. Assertions establish persistent availability until consumption, no overwrite before all blocking consumers finish, no duplicate consumption per generation, and matching token contents. The generation barrier gives common sequence order. This is scoped F-CHAN-1 safety and F-CHAN-2 evidence, not unconditional eventual consumption: an arbitrarily stalled consumer may never take. A separate always-ready proof establishes that every loaded token is consumed by all four on the following clock.

The F-CHAN-3 proof compares two native compositions driven by identical requests/tokens and blocking takes. Four extra ports are disabled in one and enabled as taps in the other, with arbitrary tap takes, tag acceptance sampled during configuration, and drop-counter clears. Producer free/load/state and blocking availability/heads remain identical. This proves tap noninterference for this fixed route/configuration; it does not cover arbitrary runtime reconfiguration or every producer mapping.

## Results and controls

| Task | Engine / scope | Result |
|---|---|---|
| blocking safety and order | ABC PDR, unbounded | PASS |
| always-ready next-clock progress | ABC PDR, unbounded | PASS |
| tap noninterference | ABC PDR, unbounded | PASS |
| two generations consumed, including backpressure | Z3 SMTBMC, depth 40 | Witnesses at steps 15 and 16 |
| tap drop while blocking traffic remains active | Z3 SMTBMC, depth 40 | Witness at step 14 |

Scratch mutations remove the take requirement, allow full-producer overwrite, ignore one blocking subscriber during release, corrupt token data, or make taps blocking. All five are rejected with actual counterexamples; syntax/tool errors do not count. Production RTL hashes are checked unchanged after the run.

F-CHAN-4, scheduler, integrated SRAM rotation, pad ownership, pin cursor, host and decode proofs remain open. The aggregate Phase 3 formal exit checkbox remains unchecked. No whole-chip formal verification, physical timing result or silicon claim follows from this milestone.
