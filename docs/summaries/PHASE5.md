# Phase 5: evidence and documentation

**In progress, October 16, 2026.** Frozen G1 remains the supported submission
baseline. The larger compact successor remains experimental. No board or
silicon has been tested, and phase 6 has not started.

## Goal

Make the design, results and limits understandable to a judge in twenty
minutes, and make the documented software/simulation path reproducible from
a fresh checkout. Separate measured results from estimates and hypotheses.

## What is ready

- The user guide, examples, architecture reference, datasheet and prior-art
  comparison are written. G1's historical chip flow passed GDS, precheck and
  gate-shell tests in [36383587262](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36383587262).
  Those tests use the documented RTL-fabric accommodation (D-023); they do not
  establish configured whole-chip timing.
- Fresh README reproduction [38780941472](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38780941472)
  rebuilt all twelve retained images, passed thirty loaded cases and one
  source-versus-fabric co-simulation case. Downloaded image bytes and reports
  were independently checked. See [reproduction evidence](../reports/reproduction_refresh_20261015.md).
- Current paired compiler evidence [38852379083](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38852379083)
  checks all eight design-set cases: G1 fits UART, SPI controller and I2C
  controller at 29, 47 and 70 placed logic cells; G0 fits SPI at 86. The four
  nonfits have actual native capacity rejections. Their demand estimates are
  not placed-cell counts. Images, native logs and exact inputs were audited;
  this does not remeasure total area or configured timing.
  See [current comparison](../reports/architecture_refresh_20261015.md).
- Current profiling [38820879331](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38820879331)
  authenticates 24 synthesis trials and 555 plain-logic LUT4s across the design
  set. These synthesis counts are separate from placed fabric cells and the
  historical profile that motivated G1.
- Controlled mutation evidence [38823961384](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38823961384)
  passes six pristine controls and rejects eleven planted defects with executed
  assertion/property witnesses. Missing tools, timeouts and harness failures
  do not count as detected defects. See [verification scope](../reports/mutation_evidence_repair_20261015.md).
- Host tools and loaded demonstrations have retained simulation evidence,
  including the compiled-C path and concurrent UART/fault/event examples.
  Their individual limits remain in [EVIDENCE](../EVIDENCE.md) and
  [CLAIMS](../CLAIMS.md); none establishes board operation.

## What we found

The compiler coverage advantage is reproducible on current sources. Model
Fmax is an estimate; matched macro outlines alone do not prove a new total-area
or timing advantage. Historical comparisons now carry explicit dates and scope.

Compact chip routing remains the main development problem. The identical-input
pair [38820879445](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38820879445)
measured original 50-iteration overflow 133 and a 15-iteration result of 121.
Both fail routing. Broad placement changes regressed and are retained as
rejections, rather than repeatedly retried.

Source diagnosis found repeated pin-access credits during incremental repair;
upstream independently fixed the same mechanism after our pinned revision.
The restricted correction now preserves observed capacities. Controlled
[38948702750](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38948702750)
then measures grid overflow 132, worse than the preserved 121 control, and
ends with native GRT-0232 and incomplete selected guides. There is no final
postrepair native table, so 132 is an independently audited grid observation.
See [the controlled result](../reports/force_repair_controlled_result_20261016.md).
Fixing the accounting defect did not solve routing.

## What remains

- Complete the numerical/source audit in [EVIDENCE](../EVIDENCE.md). Current
  compiler coverage is authenticated; missing original primitive netlist/SPEF
  timing views, historical local measurements and physical timing limits must
  remain explicit. See [remaining numerical gaps](../reports/current_numeric_gaps_20261015.md).
- Confirm all required CI gates for the final applicable revision before
  closing the phase. A diagnostic collector passing does not mean its route
  passed. No phase-completion claim follows from a launch or pending job.
- Continue the compact routing investigation under unchanged hardware,
  capacities and timing margins. The current observation-only build records
  actual expansion membership and whole-grid states after each existing pass;
  it must reproduce the rejected 132 final identity before its snapshots can
  support another intervention. Exact active run IDs live in the newest
  [WORKLOG](../WORKLOG.md) entry and [backlog](../autonomy/backlog.json).
- Retain frozen G1, original 50/133, best measured 15/121 and rejected 132 as
  distinct checkpoints. Detailed routing, extraction, complete configured
  timing and physical signoff remain necessary for any successor promotion.

**Takeaway:** the baseline and current compiler evidence are retained and
reproducible; compact routing and the final phase-5 evidence gates remain open.
