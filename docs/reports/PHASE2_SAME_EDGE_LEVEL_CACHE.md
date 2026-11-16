# Same-edge output materialization prototype

Design work targets the measured failure: live IDLE configuration passes through engine output logic, programmable pad readback and event/fabric logic before reaching a register. Compute each timed engine's post-edge output from its next-state terms, capturing that result at the same edge. No pipeline cycle is added. A host-write lookahead matches the ASIC root-clock IDLE bit introduced by the prior idle_ff candidate.

## Matched whole-chip local results

| Metric | Owner-factor reference | Combined output materialization |
|---|---:|---:|
| Standard-cell area, excluding SRAM | 414037.0080µm² | 414799.5474µm² (+0.18%) |
| Mapped flop count | 2414 | 2418 |
| Latches | 2071 | 2071 |
| Slow flop endpoint reserve | +6.125ns | +6.510ns |
| Slow SRAM endpoint reserve | +6.125ns | +6.510ns |
| Measured IDLE-launch reserve | +6.801030ns | +8.817179ns |

This is ideal20ns-clock mapping/STA, not extracted timing. The +2.016149ns measured-cone gain is not a prediction that routed slack will improve by that amount. Native buffering, hold repair, clock skew and RC still decide closure. The new local worst path starts at SRAM rather than this IDLE feedback frontier.

TX-only maps slow overall reserve5.003ns; BS-only5.951ns. The composed representation is materially stronger than either alone. This does not justify combining unrelated ideas: both parts remove the two paths of the same output-feedback mechanism.

## Evidence and limits

- Four changed source files only: chip lookahead connection, pin-unit forwarding and TX/BS output-state functions. Exact before/after/patch hashes in level_cache/candidate.json. No main source/config change.
- TX proofs:760/844points for FULL0/1 under root-clock IDLE contract. One private optimized combinational correspondence (nlvx) is excluded; outputs and state remain checked. BS proofs1152points for each USE_SAMPLE_DELTA0/1, no blacklist. Stale-IDLE output mutants rejected. Reproducer: level_cache/verify.py with explicit source directories and an external output directory.
- Initial TX proof without hierarchy elaboration is invalidated; negative control caught it. Correct elaborated proofs are used. Independent valid bounded miters timed out, not pass evidence.
- Full original/candidate top-level outputs compared2ns after both clock edges throughout5passing cases: identity/time/SRAM, lane forwarding, full/lean UART, SRAM routine and live-IDLE writes in full/lean/BITSYNC modes. This is exercised phase evidence, not exhaustive whole-chip formal or analog timing.
- Expanded22-case protocol replay passes22/22 with zero skips/failures; source/XML hashes recorded. Optional sigrok annotations disabled; independent protocol waveform/reference checks retained. Raw run remains at /tmp/tripwire-level-cache-protocols.
- ASIC candidate only. TRW_PIN_CFG_FLOPS fallback/lookahead behavior requires integration before adoption. No new protocol block, resource-count cut, relaxed timing exception, changed clock or gate.

Current owner physical screen43920762758 remains unchanged. If this prototype's protocol replay passes, prepare a separate native screen using the same physical settings. Choose physical follow-up from actual results; do not cancel a useful running source comparison. Final stock-constrained extraction and unchanged official GDS/precheck/GL remain required.


## Follow-up selection, 2026-11-16
Owner native functional reserve is only +0.295374 ns slow versus +2.533495 ns
for the earlier pending-polarity source. Prepare a controlled cache-only rebase
on that earlier source, retaining its original pin mux and all physical settings.
The same four engine-cache files and their scoped module proofs apply. Exact
whole-source replay remains separately required. Local ideal mapping for this
rebase: area 414062.9388 vs 414910.6416 um2; slow flop 5.742 vs 5.944 ns,
SRAM 6.331 vs 6.588 ns, IDLE-launch 8.375500 vs 6.117116 ns. Selection is a
controlled physical comparison, not a claim that every ideal timing measure improves.

Cheap local alternatives were rejected before spending native CI runs:

| Trial | Slow flop slack, ns | Area, um2 | Decision |
|---|---:|---:|---|
| Early operand flags | 5.855 | 416283.1596 | Reject global regression |
| Speculative full operands | 5.030 | 419355.6192 | Reject timing/area regression |
| Root-clock mode FF | 5.355 | 413672.9184 | Reject critical timing regression |
| Late mode mux factoring | 5.717 | 414401.7780 | Reject global regression |
| Selected final output cache | 5.837 | 415279.0404 | Reject global regression |
| Raw mode decode | 3.992 | 414069.1002 | Reject global regression |
| RX timer speculative arithmetic | 5.793 | 423111.8430 | Reject timing/area regression |

These are ideal-wire mapped results, not routed evidence. Scoped equivalence
passed for the modified modules; only root-mode FF received separate full
configuration phase replay. None is integrated or claimed as whole-design verified.


Cache-only replay now completes: 22/22 protocols and 5/5 original/candidate
chip phase comparisons, zero failures/skips. XML hashes and exact source
inventories are in level_cache_no_owner/candidate.json. The phase golden uses
the owner baseline; original/owner pin-mux equivalence supplies the compositional
link. Optional sigrok annotations were disabled; independent protocol checks remain.
The separate manual cache-only workflow is prepared locally, not yet launched.

Cache+owner final violations are different from owner-only: U3 wdata_odd[8]
to hold10179/A exceeds Metal2 cumulative ratio 252.73/200; net11554 to a
lane1 slot[454] NAND2B input exceeds Metal3 cumulative 225.46/200 even though
partial ratio is 199.88. The cache does not eliminate the post-repair antenna
failure pattern. Final netlist has 5056 named hold cells, with 47 inserted in
the last repair. Exact summary is level_cache/native_result_43941730264.json.

## Cache-only native screen 43957277296
The full native physical screen completes, but its strict final gate fails one
antenna net/pin. All other final gate checks pass: electrical violations zero,
global overflow zero, stock hold fast/typical/slow +0.0765731/+0.244206/+0.548727 ns.
Fast hold is only 26.5731 ps above the 50 ps gate. Aggregate setup WS remains
zero; functional flop/output setup reserve has not been measured on this source.
No positive-setup-margin or routed/signoff pass is established.

Compared with cache+owner, removing owner factoring reduces antenna violations
from two to one, but reduces fast hold from +0.117026 to +0.0765731 ns. Compared
with the earlier pending baseline, antenna count remains one and fast hold is
worse (+0.107840 ns before). Thus this is not yet a demonstrated overall winner.
The log again shows a clean antenna-repair checkpoint followed by a final
hold-repair/reroute (57 inserted hold buffers) and a fresh antenna failure.
The reported endpoint is net14102 -> _35365_/B2 on Metal3. Its displayed partial
ratio137.46/200 does not by itself identify the failing cumulative ratio;
inspect the full antenna report before selecting the remedy.

Next: inspect that endpoint and its native repair history; query exact-source
functional setup reserve if this source remains promising. No automatic detailed
route from this failed screen, no acceptance-gate relaxation, and no change to
official jobs. Routine main test/unit/lint/docs at f00bf49 all pass.

Full report confirms net14102 cumulative Metal3 ratio221.37/200; driver
wire14103 (BUF2) and sink _35365_/B2 (A22OI1) exist in the earlier checkpoint
as well as final netlist. Thus final reroute, not a newly created sink alone,
exposes this failure. Prepared read-only setup audit bound to exact source run,
commit and final ODB5163a4b917e4ec52ce3de679b954f165e6fd3698fd0dfa7a6469952849179908.
It preserves stock0.25ns uncertainty, repeats native metrics, checks unchanged
views, and cannot qualify a failed source.25focused tests pass; real source
config/ODB and workflow embedded scripts validate. A local mapping comparison
excluding weak A22OI1 is running; it is not yet a selected physical experiment.

A22OI1-exclusion local map completes: area419801.3568um2 (+1.39% vs cache-only
414062.9388), slow flop5.582ns (was5.742), slow SRAM6.617ns (was6.331).
This trades area and global timing for one possible antenna benefit; it is not
selected for a native run yet. The gate's input is already on a BUF2 wire-repair
chain; its output feeds a hold delay. Blanket upsizing is not a proven cure for
the stock final-reroute pattern. Await actual cache-only setup reserve before
committing another expensive physical trial.
