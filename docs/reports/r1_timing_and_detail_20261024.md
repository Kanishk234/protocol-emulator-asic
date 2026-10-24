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

The after-route audit requires identical cells/placements/orientations, logical
terminal connectivity and boundary-pin geometry, including PG pins. It checks
the334configuration-latch/1453cell/2906PG-terminal census and a route wire for
every multi-terminal signal net. Completion and zero router violations are
mandatory. These are necessary diagnostics; they do not replace foundry DRC,
LVS/antenna/PG analysis, extracted timing or assembled-macro/chip qualification.

G1, its configuration ABI and the sealed held-out set remain untouched. No
phase box or full-chip hardening attempt is consumed by these probes.
