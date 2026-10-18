# Remaining judge-facing evidence gate, October 16

Bounded follow-up after hosted G0/G1 refresh `38852379083` and removal of
local fault/capture resource numbers from `docs/EVIDENCE.md`. This reads the
judge-facing report and its cited reports only; no held-out RTL, profiling,
tuning or EDA is performed. No phase box is changed.

## Actionable shortlist

| Location in EVIDENCE | Remaining issue | Smallest sufficient correction | Fresh measurement needed? |
|---|---|---|---|
| §6 held-out table: G0 `82/126/61/241`, G1 `32/77/44/207` | The linked held-out report contains those historical compiler counts, but does not give an exact producer run for the paired G0 numbers. Nonfit figures also lack the synthesis-demand distinction now present in the design-set table. The nearby gate-shell/fabric runs support simulated behavior; they should not automatically be credited with producing every number. | Keep the demonstrated supported operations and named CI tests. Remove the unbound LC columns from the judge-facing table, or attach retained exact-run compiler reports where already available. If retaining nonfit counts, label them synthesis demand rather than placed cells. Keep dated historical values in their report with honest scope. | **No**, if the unbound numeric detail is removed. A new paired experiment would only be required to present fresh quantitative held-out resource savings; do not start one merely to finish the summary. |
| §4 fabric-macro row: `1016.64 × 669.06 µm`, `88 LUT4 + 2 + 2` | Source cell currently names `macro/warp_g1`, D-027, rather than an explicit run ID. This is a citation gap, not evidence that the outline or resource count is wrong. | Cite the recorded G1 chip integration `36367067731` and/or frozen G1 `36383587262`; the physical-design history explicitly records G1's same outline and resources. Preserve the distinction between macro outline and internal component cost. | **No**; use existing physical evidence. |
| §3 heading “chosen at equal area” | The current body correctly says the compiler refresh does not remeasure total area and that matched outlines do not establish identical internal costs. The heading still promises a stronger comparison than this refreshed evidence provides. | Rename to “Architecture and measured compile coverage”, retaining the dated matched-outline comparison and D-004 requirement in the linked historical report. | **No**, unless making a new physical superiority claim. |
| Opening audit paragraph and linked `evidence_audit_20261015.md` remaining-blockers table | The older audit still lists local profile, area-ratio, model and mutation numbers together as missing CI evidence. Current profile and mutation now have direct hosted evidence, and the current G0/G1 comparison has been refreshed. This stale list can make completed work look unresolved. | State the specific remaining gaps above and distinguish disclosed historical timing limitations. Keep the older audit dated, but append a superseding status link rather than requesting duplicate profile/mutation/compiler runs. | **No**. |

Two scope clarifications are useful without more numbers or experiments:

- §6's “within the datasheet's timing” should explicitly refer to **simulated
  waveforms**. The cited chip tests use the D-023 RTL fabric and do not establish
  ASIC operating rates.
- The opening C2 progress sentence should say the **listed tile-level physical
  checks** pass, rather than suggesting every physical gate for the compact
  successor passed. Its cited report already excludes I/O, intertile, loading
  and other-tile timing; preserve that existing scope.

## What is no longer an open numerical gap here

The current design-set placement/demand table now cites `38852379083` and
labels estimates correctly. The profile cites `38820879331`, mutation cites
`38823961384`, shell area/slack/check counts cite `36383587262`, and the retained
README images cite `38780941472`. Earlier compact measurements in §§10–11
carry their own run IDs and rejection/partial-timing scope. No new blanket
remeasurement is justified by those already-scoped historical entries.

The monitor's `37/88` entry names hosted `37512249763` separately from its local
gate-shell evidence; it is not the same gap as the removed local-only fault
and capture numbers. If it remains in the summary, keep that hosted reference
and avoid implying it produced a new hardened or SDF result.

## Missing original timing views: limitation versus gate

The original matching G1 primitive netlist/SPEF gap is already disclosed in
EVIDENCE §§8–9 and `reports/reproduction.md`. It prevents a fresh independent
physical cross-check of the historical primitive timing model. It also blocks
stronger claims such as complete configured-fabric timing, native/SDF timing,
or a newly established whole-chip protocol rate.

It does **not** by itself prevent completing a truthful evidence report that
limits the old cross-check to historical local evidence, labels model estimates,
reports frozen-shell STA separately, and explicitly states the missing views.
The phase-5 report-completeness gate does not require inventing or silently
substituting physical artifacts. Recovering or regenerating qualified timing
views is a separate measurement task if those stronger claims are pursued.

Closing the editorial/evidence gaps above does not close compact routing or
the independent all-CI-green and phase-summary gates. Those remain decisions
for the coordinator using their own actual evidence.

## Review after the bounded corrections

Independent read-only review of the updated `docs/EVIDENCE.md` and
`docs/CLAIMS.md` finds **no remaining blocking numerical-source or scope gap
in the judge-facing report's limited baseline claims**:

- The held-out summary now reports demonstrated behavior, names the supporting
  simulation runs and removes the unauthenticated paired resource columns.
  Its waveform language explicitly describes simulation; CAN remains
  unsupported without a successful loaded-result claim.
- The macro row names G1 integration `36367067731` and frozen-chip
  `36383587262`. The current design-set resource table retains the independently
  verified paired run `38852379083` and distinguishes placed cells from
  nonfit demand estimates.
- The architecture heading now promises measured compiler coverage rather
  than new equal-area superiority. The reconfiguration heading and C4 clearly
  identify the gate-level shell/RTL-fabric accommodation. C2 no longer makes
  a current quantitative local area claim; C5 is scoped to demonstrated
  simulated behavior.
- Local fault/capture resource measurements stay in explicitly dated historical
  reports and scoped claim-ledger entries, rather than appearing as newly
  authenticated judge-facing numbers. The remaining monitor resource figure
  has its separate hosted citation, with local gate-shell scope distinguished.
- Remaining quantitative results in the evidence summary carry named producer
  runs, or describe static architectural/specification facts within the cited
  build/proof context. Historical compact experiments retain their individual
  run IDs and explicit failure or partial-coverage limitations.
- Original primitive timing-view recovery remains openly unavailable. The
  report does not turn model Fmax, shell STA, or partial C2 diagnostics into a
  complete configured-fabric/physical-rate claim. Recovering those views is
  not necessary to complete this accurately limited evidence report.

This supports completing the **report-content review**, not declaring phase 5
complete or compact hardware accepted. All-CI-green and phase-summary evidence
must still be assessed separately. This reviewer changed no checklist, public
claim, measurement or acceptance rule.
