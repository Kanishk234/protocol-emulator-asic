# Conditional internal C2 timing: actual result

Run38111705892 completes all six diagnostic cases on292ad9b. This is an
authenticated measurement of final physical C2 from37814078650 with the exact
UART image loaded in37958116481. Configuration Q is assumed stationary for
this diagnostic. It is not full-chip timing acceptance or all-image safety.

All eight user clock pins in each case have actual finite rise/fall arrivals
from the20ns propagated N_GBUF_END[3] boundary clock. Retained libraries match
each original PVT corner; all use the same nominal extracted SPEF. Original
uncertainty/transition/derating remain. No I/O delays, false paths, loop cuts
or user-register state case analysis were added.

| Concrete position | PVT | Reported setup slack ns | Reported hold slack ns | Examined max/min paths |
|---|---|---:|---:|---:|
| X2Y1 | fast |17.89|−0.03|28/28|
| X2Y1 | slow |15.23|0.25|28/28|
| X2Y1 | typ |16.90|0.07|28/28|
| X2Y3 | fast |18.11|−0.04|26/26|
| X2Y3 | slow |15.75|0.24|26/26|
| X2Y3 | typ |17.23|0.07|26/26|

Values above use the native report's two-decimal precision. Root independently
verified every report hash and all path counts. The fast-corner hold paths
fail; successful artifact collection is not a timing pass. X2Y3's worst path
is _1821_/Q through _0828_/Y and _0829_/Y back to _1821_/D. Its short feedback
path lacks hold margin under the original0.25ns uncertainty. This identifies
a concrete path to investigate; it does not authorize relaxing uncertainty.
X2Y1 also reports two VIOLATED paths rounded to0.00ns, besides four displayed
negative paths. Count native status labels rather than comparing rounded
printed slack to zero. The next reporting-only replay adds six-digit precision
and input-pin/net/slew/capacitance/fanout detail using source-verified pinned
report_checks options; constraints, physical views and image stay identical.
Self-feedback timing sensitization needs separate analysis; these structural
reports alone do not prove that the feedback paths can toggle in real operation.

Coverage retains152 inputs without delays,529 unclocked configuration latch
pins and679 unconstrained endpoints per case. Case analysis does not magically
make the loading network timed. Four drivers lack parasitic annotation:
N2END[1],S2END[5],W2END[3],TIE_ZERO_zero_/L_LO; no partially unannotated drivers
are reported. Determine whether those touch active paths before qualification.
Intertile/shell clock latency/skew and input/output paths remain excluded.
No configured loop warning appears in the retained STA stdout; that limited
observation does not prove every configuration loop-free.

Next: inspect exact feedback and clock arcs, report higher precision if needed,
then prepare one isolated physical delay/hold repair only with preserved
configuration, logic and loaded behavior. Any repaired tile needs native route,
geometry/LVS, electrical and fresh configured timing checks across images.
Other tile types still need matching physical views. BMC84/cover84
38102131236 does not prove arbitrary full-frame RUN stability.
