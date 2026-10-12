# Routing algorithm follow-up on the best compact placement

Keep measured133-overflow combined placement38167697696/38168159774 as control.
Buffer35 trial38178351037 worsens it to143; buffer234 trial38274085899 worsens it
to141. Both are rejected. Further terminal-distance proxy optimization is not
evidence that routing demand improves.

Current cloud38279250531 compares no-order-randomization with seed41 on original
and combined placements. Capacity perturbation is explicitly0; no capacity,
layer, congestion, margin or placement relaxation is applied. D085 records
provenance and the copied-source instrumentation; actual outcomes remain pending.

## Alternate router and report compatibility

The exact pinned OpenROAD revisiondcf36133a369abc8f3c5e5738cd4d82e4903c0e0
accepts global_route -use_cugr. This is verified in its native Tcl, not assumed
from current documentation.
[Pinned Tcl](https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.tcl).

Its C++ implementation selects a different routing engine and skips the
FastRoute congestion-report function in the CUGR finishing branch. Our current
strict parser requires that final table, so blindly appending -use_cugr would
produce an observer failure or incomplete evidence. Retain native errors; do not
interpret a missing table as zero congestion.
[Pinned engine source](https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.cpp).

Before execution, add engine-specific collection of native congestion/coverage
evidence with unchanged placement/netlist authentication. Validate all required
nets have guides, retain native congestion rejection and route metrics, then
require detailed-route/antenna/disconnect/physical checks. Global guides alone
are insufficient. Reuse physical inputs/capacity/margins and declare the changed
engine; do not label changed algorithm policy identical to the control.

Horizontal cell mirroring is another later hypothesis for pin access. OpenROAD
documents it as an HPWL heuristic, not a congestion guarantee; a trial needs
explicit orientation/power-phase/connectivity and all-other-bbox guards plus
native legality/electrical checks. It must not silently pass through existing
audits that demand every original orientation remains exact.
[Detailed placement](https://openroad.readthedocs.io/en/latest/main/src/dpl/README.html).

No algorithm gain, routing pass or successor promotion is established here.
