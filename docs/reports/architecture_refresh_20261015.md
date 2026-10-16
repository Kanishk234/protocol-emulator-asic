# Current G0/G1 compile evidence refresh

Prepared collector and separate hosted workflow; **no completed measurement yet**.
First hosted run `38851943119` stopped during tool setup: the tracked
`scripts/fetch_nextpnr.sh` has mode `100644`, so direct execution failed with
permission denied. The workflow now invokes it through `bash`; no compile
result came from that failed setup run.
Historical local tables in `g0_results.md` and `g1_results.md` remain historical.

The new matrix explicitly selects UART, SPI controller, I2C controller and
I2C target, each on `warp_g0` with `PRIMS=0` and `warp_g1` with `PRIMS=1`.
All other parameters come from the same current design pin specifications.
The seed is 1, assessment target is 50 MHz, and both use the compiler's
`nom_slow_1p08V_125C` timing model. No held-out protocol is discovered or read.

Each worker has a ten-minute process-group limit. Successful cases retain
native logs/netlists, report and actual CRC-checked image; rejected cases must
retain a native capacity or placement diagnostic with a known placement fatal.
Every fatal must match reviewed nextpnr grammar; high resource demand cannot mask
an additional unknown, setup or routing failure. Synthesis, import, missing-tool,
unknown native failures and timeouts fail the campaign instead of counting as
expected nonfit. The collector rechecks native usage/report/image consistency,
the complete eight-case matrix, listed input stability, exact tool revisions and
binary hashes, library revision/files, architecture files and workflow run/attempt.

For failed placement, synthesis demand is explicitly an estimate, not placed
LC count. Compiler Fmax is a model estimate, not configured physical timing.
The paired compiler measurement does not remeasure total chip area: historical
matched outlines and clock targets remain separate evidence, and this refresh
cannot establish a new equal-total-area architectural superiority claim.

Local evidence validation: 30 tests pass, covering workflow script invocation,
paired parameters,
native capacity/placement rejection, unknown/routing/setup errors, stale success,
actual synthesis parameter drift, CRC/image/native usage corruption and bounded
process-group termination. No EDA was executed locally.

Artifacts: `current-architecture-comparison-<run>` under the workflow
`current G0 G1 compile evidence`. Root review will append the actual run ID,
authenticated results and limitations after hosted execution.
