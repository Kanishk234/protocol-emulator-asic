# Formal verification summary (phase 2)

**CI run:** `formal` 36367067725 on d6f5dcd (G1 in the chip), 2026-09-28, all tasks PASS. Tools: SymbiYosys from OSS CAD Suite 2026-06-29 (docs/VERSIONS.md). Logs are CI artifacts (`formal-*`), not committed.

| ID | Property | Design under proof | Method and bound | Result |
|---|---|---|---|---|
| F1 | **Output isolation:** no fabric output or output enable reaches a pin while the chip is not RUNNING (stopped, loading, loaded, error); fabric outputs are unconstrained (any value, any time) | whole top `tt_um_warp` (shell, configuration path, pin logic) with the fabric macro `warp_g1` as an unconstrained black box | `mode prove`, k-induction, depth 4 (`formal/f1_isolation.sby`) | **PASS, unbounded** (basecase and induction) |
| F2 | **Loader:** an aborted or corrupt load (bad sync, length, CRC, architecture version) never reaches RUN; checked against an independent shadow model of the loader written from ARCHITECTURE §3, with arbitrary host bytes | `wp_shell` | `mode bmc`, **bounded, depth 84 cycles** (`abc bmc3`); cover: a full 1-word load followed by RUN is reachable (step 52) | **PASS to depth 84** (not a proof for longer traces); cover reached. Found BUGS #12 |
| F4 | **Primitives equal their spec:** `wp_timer` and `wp_shift` equal a model written from ARCHITECTURE §8 (cycle-exact spec v2) for every configuration (all RELOAD/ONESHOT, LEN/MSB_FIRST) and every input sequence | `arch/prims/wp_timer.v`, `arch/prims/wp_shift.v` | `mode prove`, k-induction, depth 4 (`formal/f4_prims.sby`, tasks `timer`, `shift`) | **PASS, unbounded** (both) |

## What is not formally verified
- The fabric itself (switch matrices, configuration memory, LUT tiles): covered by simulation of real bitstreams (RTL and CI `gl_test`), not by proofs.
- The hardened primitive tile against `arch/prims/*.v` (per-tile netlist-vs-RTL equivalence is planned, D-023).
- F2 beyond 84 cycles; the SPI host protocol decoder beyond what F2 exercises.
- Protocol user designs: RTL simulation against independent reference models only.

"Formally verified" in any claim must name the property and bound from this table (CLAUDE.md honesty rules).
