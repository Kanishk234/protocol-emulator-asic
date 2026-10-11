# Frozen-G1 design-set seed robustness plan

Prepared and executed 2026-10-10. Results below are compiler evidence only.

New narrowly triggered workflow `seed_robustness.yaml` uses the existing project
compiler on unmodified frozen G1 (`hw-freeze`:
`3047dea08566bedaed9d061c0ce2313c92f4a193`). It checks that `arch/warp_g1`,
`macro/warp_g1` and `arch/prims` still match the frozen commit. This does not
rebuild ASIC geometry or change user hardware.

The bounded matrix is UART, SPI controller and I2C controller at seeds **0,1,2**:
nine fresh independent builds. These are the existing design-set inputs; no
held-out RTL, architecture tuning or new reference model is used. Parameters
are kept at their existing pin-map values:

| Design | Fixed parameters |
|---|---|
| UART | DIV=434, RUNTIME_DIV=0, PRIMS=1 |
| SPI controller | CPOL=0, CPHA=0, HALF=25, PRIMS=1 |
| I2C controller | Q=125, PRIMS=1 |

The same pin maps, default intentional-unmapped-port handling, architecture
models and slow timing corner are used for every seed. Yosys is the existing
OSS CAD Suite 2026-06-29 version 0.66+179; nextpnr is Suite 2026-09-27 version
0.11.1-34-gc4fbb55a. The pristine tile library stays at 7999e5a. The helper records
full tool/library commit identity, executable hashes, compiler input hashes and
all report/bitfile provenance. Hashing tracked source files is evidence collection,
not reading them to design a new RTL/model implementation. Vendor runtime
libraries and recursive includes are not fully hashed by this tool.

Each compiler process group has a 90-second limit plus up to 5 seconds for orderly
termination, including its synthesis/P&R children. The sweep step is bounded
to 15 minutes and the hosted job to 20 minutes. These are resource limits, not
measured runtime predictions. A cold tool install may hit the job cap; an
incomplete matrix must remain explicitly incomplete rather than being treated
as a seed success. No physical route or simulator runs are launched.

Fresh unique output directories prevent stale images. Every planned trial
records status, exit code, elapsed time and its command; failed placements retain
compiler failure diagnostics and synthesized resource demand when available.
Every result remains in the artifact, without choosing a favorable seed.
Successful reports must match architecture, seed, parameter set, model corner,
tools and actual bitfile hash. Input files are rehashed between trials.

`passed` means all nine compiler builds succeeded; it does not mean configured
function, native electrical legality or ASIC timing passed. The existing compiler
allows estimated timing failure, so this sweep retains frequency estimates and
does not turn them into a chip-clock claim. Missing estimates remain missing.
Synthesis/setup/timeout failures must be distinguished from proven routing
failures when reviewing the raw logs. Run IDs and measured results should be
added after an actual hosted run, not inferred from these preparation tests.

Lightweight preparation checks passed: three self-test methods cover successful
report validation, six wrong-report controls, missing/duplicated seed rejection,
failure retention and mocked child-process-group timeout cleanup. Python
compilation, scoped branch trigger and actual frozen-view/three-parameter
map checks also pass. No local
EDA. Root should include the final verification outcomes and future hosted run
ID in WORKLOG; no phase checklist was changed.

## Verified hosted result

[38101717810](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38101717810),
ec91fb9, succeeds in1min39s including hosted setup. Downloaded summary retains
all nine distinct planned trials, all compiled, no timeout/failure and unchanged
input hashes. Each fresh image/report carries compiler provenance. No loaded
simulation, new ASIC layout or configured physical timing is included.

| Existing design | Seed0 / seed1 / seed2 model Fmax (MHz) |
|---|---|
| UART | 89.90 / 90.71 / 90.30 |
| SPI controller | 77.97 / 77.97 / 76.77 |
| I2C controller | 51.74 / 52.97 / 52.56 |

These are existing slow-corner compiler-model estimates, not validated chip
frequencies. Three seeds provide a bounded robustness sample, not a distribution
or best-seed optimization. The I2C controller's smaller estimated margin is a
reason to prioritize actual configured timing; it is not a timing signoff result.
This software/evidence improvement applies to frozen G1 independently of the
compact experiment. No architecture change or held-out retuning occurred.
