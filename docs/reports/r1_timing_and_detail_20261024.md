# R1 configured timing and detailed-routing diagnostics

The native primary function/reset/reload gate40109928699 remains accepted in its
documented simulation scope. This follow-up introduces two independent probes;
neither replaces it or selects R1 as the chip.

## Configured RUN timing

`spikes/r1/run_timing.py` consumes the authenticated D118 direct-primary state,
the same ten native leaf exports and pinned slow-corner Liberty. Its8736case
constraints are analysis-only. No chip netlist/configuration storage is changed.
Frame inputs are inactive, reset is released, and spare inputs have the exact
constant values of the verified direct test. The model has cell/pin loads and
ideal clocks, with zero wire RC; it excludes the management shell, extracted
intertile/clock wiring, CTS, SDF and hold analysis.

OpenSTA cannot read the generated parameterized top directly. A structural-only
Yosys conversion resolves its dimensions while treating native leaves as opaque;
the audit compares all40instances, port/master identities and the complete
port/cell-pin connectivity partition with the frozen source. No optimization,
mapping or leaf resynthesis is performed.

Both OpenSTA loop policies must cover the same endpoints with identical timing.
Configuration Q/gate checks and register classification avoid accepting a small
reported path set while actual runtime registers remain untimed. Clockless
state is permitted only with a constant-low clock and no enabled path to any
register/output observable. A clocked D must have a timed input/register path
or a derived constant value. Structural-loop warnings remain visible.

The local reproducible probe finds a loop-policy sensitivity at six endpoints
(BUG133). Its guard intentionally fails; this is not repaired by treating the
two reports as interchangeable or silently adding false paths. The source-bound
scripts/reports/result live under `build/r1_configured_timing_reviewed`.
The hosted workflow will retain both views and the complete source artifacts,
excluding the cloned PDK Git cache while preserving the pinned Liberty/LEF.
The method follows OpenSTA's primary-source
[disabled-edge reporting](https://github.com/The-OpenROAD-Project/OpenSTA/blob/master/search/Search.tcl)
and [loop-handling variables](https://opensta.readthedocs.io/en/latest/Variables/).
No configured setup/clock-rate acceptance follows from the optimistic reports.

Hosted40119792005 atdcf59af reproduces the same qualification failure on the
pinned OpenSTA2.7.0 environment: all8736case/gate checks,370classified registers
and246endpoints are retained, with six loop-policy-sensitive endpoints. The
program and native functional acceptance from40109928699 remain unchanged.
Two grounding hypotheses were evaluated separately and are **not retained**:
broad closure changed implicit register-enable defaults and broke UART, while
a routing-wire-only closure passed a short native behavior/reset probe but left
the six-endpoint sensitivity. Preserving explicit FASM fields alone does not
justify changing implicit BEL defaults. A case-aware sequential observability
check also finds the six endpoints can reach outputs, so they cannot simply be
waived as dead storage. No new bitstream policy is promoted.

## Detailed-routing readiness

D120 fixes one source: primitive1's global-route output from40030916359,
source00216eac, with the recorded ODB/guide hashes. The native source is not
regenerated. `spikes/r1/detailed_leaf.py` requires its prior zero-overflow/PG gates,
then emits a standalone detailed-route script with unchanged placement and
Metal2–Metal4 routing. The32-iteration policy and hosted wall bound are fixed,
with no architecture, footprint, seed, clock, CTS or buffer-repair sweep.

The local exploratory180-second bound expired during optimization. That records
readiness and incomplete routing only, not final DRC or impossibility. The
hosted pinned-tool workflow allows the declared complete run and saves
per-iteration DRC reports, exit code, inventories, guides and final database
when available. Timeout has its own failure classification.

Hosted40119792058 atdcf59af **completes detailed routing with zero router
violations**, with the route stage reporting1m49s elapsed. The workflow's
postcheck fails because of BUG134's unsupported wire getter. A corrected
read-only local replay of that exact hosted ODB, using the same OpenROADdcf36133
backend, confirms all1557required signal nets have nonempty wire encodings,
versus zero in the frozen unrouted source. Frozen resource, placement,
connectivity and boundary-pin inventories are identical. Corrected hosted [40126282580](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40126282580)
at8d1ebea attempt1 succeeds end to end. Root authenticates all5prepared input
hashes, script/final ODB hashes,6strict guard cases, completion/exit0/zero-router
markers and the same1557wire/frozen-inventory checks. The final ODB hash is
identical to the original route, confirming an observer-only correction. The
failed original workflow is not relabeled green.

The after-route audit requires identical cells/placements/orientations, logical
terminal connectivity and boundary-pin geometry, including PG pins. It checks
the334configuration-latch/1453cell/2906PG-terminal census and a route wire for
every multi-terminal signal net. Completion and zero router violations are
mandatory. These are necessary diagnostics; they do not replace foundry DRC,
LVS/antenna/PG analysis, extracted timing or assembled-macro/chip qualification.

G1, its configuration ABI and the sealed held-out set remain untouched. No
phase box or full-chip hardening attempt is consumed by these probes.

## Binary feedback-support follow-up (D121)

The source-bound local diagnostic in `build/r1_boolean_support_v2` uses the
same snapshot0491a427…, actual native LUT4x8_ha export and slow Liberty. All438
configuration latch outputs in Tile_X2Y3 are bound. For each LA–LH output, it
expands a cone to64levels/2048cells; sequential outputs, module inputs and
recursion/boundaries become shared arbitrary binary values. Two copies differ
only in that root's feedback cut value. All8difference miters are UNSAT.
The positive equality control is UNSAT and the unequal negative control SAT.

This establishes independence of each expanded binary function from its own
feedback cut, under arbitrary shared boundaries. It does **not** establish
whole-network acyclicity, absence of reconvergent glitches, bounded settling,
physical timing or a waiver for the six endpoint differences. No original STA
arc, case value, image or tolerance changes.97focused guards pass. Hosted replay
is added to the existing configured-timing workflow ahead of its unchanged
strict timing gate; its original timing sensitivity must remain visible.

The stronger local `build/r1_boolean_support_v3` compares all recursively
encountered feedback cuts fixed0 against independent arbitrary values. Six
outputs prove independent; LE and LG produce counterexamples. Individual-cut
scratch probes isolate `_0327_` (LE_I2 via `_0762_`) and `_0280_` (LG_I2 via
`_0715_`). These are expanded-cone counterexamples, potentially introduced by
boundary abstraction, not physical defect witnesses. They demonstrate why the
own-feedback result cannot clear BUG133. The reproducible tool now retains all
16cofactor cases and both polarity controls.98focused tests pass; the initial
hosted own-feedback run40128629795 atbc13e60 keeps its original scope.
