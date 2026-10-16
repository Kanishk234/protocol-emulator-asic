# Current G0/G1 compile evidence refresh

Hosted paired refresh **completed successfully** in
[38852379083](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38852379083)
at `ba0cb76ac717b8656c7d081fc453ca9222b6e8d5`, attempt 1.
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

## Actual paired results

All eight explicit cases completed. G0 places and routes SPI controller;
G1 places and routes UART, SPI controller and I2C controller. The other four
cases have actual native overcapacity census and fatal
`Unable to place cell ... no BELs remaining ... FABULOUS_LC` diagnostics,
not setup errors. No nonfitting case is assigned a placed LC count.

| Design | G0 result: placed LCs or synthesis demand | G1 result: placed LCs or synthesis demand | Model Fmax MHz, G0 / G1 |
|---|---|---|---|
| UART | Nonfit; demand estimate 124 | Fits; 29/88 placed | — / 90.71 |
| SPI controller | Fits; 86/96 placed | Fits; 47/88 placed | 68.03 / 77.97 |
| I2C controller | Nonfit; demand estimate 115 | Fits; 70/88 placed | — / 52.97 |
| I2C target | Nonfit; demand estimate 185 | Nonfit; demand estimate 169 | — / — |

Parameters match the exact revision's pin specifications: UART `DIV=434`,
`RUNTIME_DIV=0`; SPI `CPOL=0`, `CPHA=0`, `HALF=25`; I2C controller `Q=125`;
I2C target `NREGS=4`. Only `PRIMS` differs between each G0/G1 pair (0/1).
All use seed 1 and `nom_slow_1p08V_125C`. The actual retained synthesis scripts
contain these parameter settings. Successful G1 images use timer/shift counts
2/2 for UART and 1/1 each for SPI and I2C controller. The current plain I2C
target demand is 185, whereas the historical local table reported 184; this
refresh preserves the current result without rewriting historical measurements.

## Independent downloaded-artifact audit

Artifact: `current-architecture-comparison-38852379083` from workflow
`current G0 G1 compile evidence`. Result SHA-256:
`3216cbceb1886d5e64f3dc33aef4270e47c7bdd5b9914e0d84bc1c0a3b3a15cb`.

Read-only independent checks confirm the exact eight-case matrix and parameters,
all 449 listed input hashes against the project commit or pinned tile-library
Git objects, all 100 per-case artifact hashes, and all 66 successful-report
input fingerprint entries. Native successful PNR logs match the reported
utilization and model Fmax; emitted images pass CRC parsing, word-count checks,
and architecture-version checks against their corresponding architecture files
(G0 0x0002; G1 0x0003). Failed cases retain the actual capacity/placement fatal
and no successful report/image. No EDA was executed during this audit.

Tools: Yosys `0.66+179`, revision `e74db6dea`; nextpnr
`0.11.1-34-gc4fbb55a`; tile library
`7999e5a91dab77357fe9d401b6dfb0758f438bf1`. Executable SHA-256 values:

- Yosys: `7c3e3396b38c129dd7485be5a0a0f0da8e495a94c8fd486059e3bea043a588d6`.
- nextpnr: `a36179428d1afb5c9b88950097f03473f22949a39be1ac5cf6e5f3a95b526829`.

These are compiler placement/routing results and timing-model estimates. The
50 MHz assessment is evaluated from model Fmax; the compiler uses
`--timing-allow-fail`, so “fits” is not a physical timing pass. Images were
compiled and authenticated here, not loaded in this campaign. Listed-input
hashes do not discover recursive includes or recover the missing original
physical primitive timing views. The run does not measure new total area,
provide configured/SDF timing, or qualify the experimental compact successor.
