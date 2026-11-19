# Native pin RX overrun preservation

On 2026-11-19, an unbounded ABC PDR proof passed against native `trw_pin_rx` and `trw_chan_prod`. Z3 depth-20 reachability checks passed, and five deliberate RTL mutations were rejected with actual counterexamples. The [receipt](phase3_formal_pin_rx_result.json) records source/runner/tool identity and log/witness hashes. No production hardware or official workflow changes.

Run with the project venv active and OSS CAD Suite appended to PATH:

```sh
python scripts/formal_pin_rx.py
```

Our separate `formal` workflow runs the RX and channel suites and uploads raw artifacts. Remote execution is pending; these results are local.

## Scope and proof structure

The real RX drives the real depth-one producer. A second native RX sees the same inputs but `rx_free=1`; its load output exposes the candidate completion. Assertions prove the real RX only requests a load when free, indicates overrun for blocked completions, preserves the producer token/valid/sequence while blocked, and stores the exact accepted token with a sequence toggle. An independently evaluated event condition requires candidate generation and the generated EVENT tag, guarding against both RX copies silently dropping every event.

Initial reset is asserted for one clock and held deasserted afterwards. All RX configuration fields, synchronized pin inputs/previous samples, restart/live, selection/echo, TX sampling/reframing commands and producer release are symbolic. This intentionally overapproximates integration: changing configurations or previous-sample inputs need not form a legal physical transaction. No fairness assumption or fixed data pattern is used. The default native FRAC=8 implementation is proved; this is not a claim for every parameterization.

The extra RX is verification instrumentation only. The proof checks `ovr_set`, the RX indication consumed by unit sticky-flag logic. It does **not** prove that sticky flag's set/clear priority, BITSYNC merge arbitration, pad synchronization, physical timing or the entire pin unit. Release is an arbitrary input here; native fabric release is covered separately by the [channel composition proof](PHASE3_FORMAL_CHANNELS.md). Full F-CHAN-4 acceptance remains open pending the remaining integration obligations.

## Results

| Check | Engine / bound | Result |
|---|---|---|
| Completion gating, overrun indication, producer preservation and accepted data | ABC PDR, unbounded | PASS |
| Blocked event completion | Z3 SMTBMC, depth 20 | Witness at step 3 |
| Blocked data completion without an event | Z3 SMTBMC, depth 20 | Witness at step 3 |
| Two accepted completions with an intervening overrun | Z3 SMTBMC, depth 20 | Witness at step 5 |

Scratch faults suppress blocked-completion overrun, request RX loads while full, erase the old producer token while blocked, remove event completions, or corrupt accepted tokens. All five produce semantic FAIL and VCD witnesses. Tool errors and missing witnesses are rejected. Native source hashes remain unchanged.

The initial harness run incorrectly encoded qualification/tag constants and failed; the oracle was corrected against the generated definitions before the recorded final run. This was a verification-harness error, not a discovered hardware bug. No architecture change or weakened acceptance requirement was used to obtain PASS.
