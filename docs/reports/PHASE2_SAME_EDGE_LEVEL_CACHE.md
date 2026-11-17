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


## Native functional audit 43970069989 and next controlled mapping test
Exact-source read-only audit succeeds with setup fast/typical/slow
+12.766801/+9.293901/+3.183562 ns at stock0.25ns uncertainty. Source views and
ordinary native metrics remain identical. Slow functional reserve improves
+0.650067 ns over pending-only +2.533495 ns. No extracted result or qualification
is inferred: final antenna1 and narrow fast-hold headroom remain unresolved.
Source-bound receipt is level_cache_no_owner/functional_setup_43970069989.json.

Reconsider the small mapped area/timing tradeoff in light of this actual reserve:
prepare one native screen excluding A22OI1 on exactly the same cache-only RTL.
The library offers only A22OI1, so this is logic decomposition/remapping, not
a direct A22OI2 replacement. The local trial directory's a22oi2 name does not
identify an actual library cell. Area rises1.39%; local flop slack falls0.160ns
and SRAM slack improves0.286ns. The native result could worsen; all final gates
remain unchanged. Exact source/config binding, one-field config comparison,
unchanged RTL inventory, native synthesis/final exclusion checks and workflow
parity tests pass (73 focused checks). Actual frozen-source preparation produces
config155c0c8efe5375f12cd34feb5d4a559c860d2f94970be7d2bf150fbb50b6e9af.
No full protocol rerun for byte-identical RTL; the original22/22 evidence remains.
This does not adopt non-default configuration into main or authorize routing an
antenna-failed source.


## A22OI exclusion screen 43972384723
Corrected preparation passes; full native run completes and final gate fails only
one antenna net/pin. Exclusions verified at synthesis/final, electrical0 and
overflow0. Stock hold fast/typical/slow+0.107982/+0.306447/+0.637996ns, improving
fast by31.4089ps vs cache-only. Aggregate setupWS0does not establish the actual
functional reserve for this changed placement; earlier+3.183562ns is not this
source's result. ANT repair again reacheszero before finaltiming/reroute;22late
holdbuffers inserted. Fresh summary identifies net14132→hold10808/A onMetal2,
ratio203.75/200. The previous A22OI endpoint is eliminated but another violation
remains. This is not a qualified screen, detailed route or official GDS result.
Full artifact inspection pending; no new experiment launched on summary alone.

## Exact gate-mapping setup measurement and future early gate
User requested setup be measured on this exact mapping before further promotion.
Prepared bound read-only audit43972384723/source2f17b0c/config155c0c8e. It restores
only the named GitHub artifact, verifies every original physical-view hash from
the source audit receipt, repeats ordinary metrics and stock0.25ns uncertainty,
and cannot qualify the antenna-failed design. Local artifact transfer times out;
runner-side restoration avoids depending on that transfer. No setup result yet.

For future executions of our separate mapping screen, add the functional-endpoint
Tcl to the existing repeat-all-corner STA. Collect actual flop/output setup reports
and require strictly positive reserve at every corner, in addition to all existing
gates. Missing/repeated/malformed/nonstock reports fail closed. This changes our
diagnostic workflow only; official jobs and constraints remain untouched.91focused
checks pass; collector reproduces actual cache-only audit+12.766801/+3.183562/
+9.293901ns. Those values remain historical and are not gate-mapping measurements.

## Exact A22OI-exclusion setup result: audit 43984026662
Read-only audit succeeds on source43972384723. Stock functional setup reserve
fast/typical/slow+12.594728/+9.014820/+2.854549ns. All physical-view hashes,
ordinary baseline metrics, repeated functional reports and stock0.25ns uncertainty
checks pass. This source therefore has positive measured pre-routing functional
setup as well as positive hold (fast+.107982ns). It remains unqualified because
one antenna endpoint fails. This is not extracted/signoff evidence.

Compared with cache-only: slow setup falls0.329013ns, fast hold improves0.0314089ns;
antenna1persists at a different endpoint. Preserve both tradeoffs rather than
calling it a universal improvement. Source-bound receipt saved in
cache_gate/functional_setup_43984026662.json. Local artifact downloads remain
unavailable after bounded timeout; runner audit restored and verified the exact
source successfully. Final antenna endpoint history still needs inspection.

## Config-only late antenna repair prepared on pinned dev4
Full source artifact finally downloaded with a300sbound. hold10808/A is already
present before the final timing pass; M2cumulative203.75/200 is confirmed. A native
late repair therefore addresses changed final geometry, not just a new sink.

Prepared D181 experiment: add native RepairAntennas after final timing, followed
by native GlobalRouting, and set GRT_ALLOW_CONGESTION=false. All original Classic
steps remain in order, as verified with the installed pinned dev4 API. The actual
official TT generation/merge preserves the config on8x4, with source/macro/clock
checks passing. Official hardening reads this config without a forced flow;
o official workflow or tool edit is required. This is configured Classic with
two added stock steps, not an unmodified Classic-sequence claim.

Because native antenna/routing steps inherit NL/PNL, repeat final ODB readbacks
at every corner/phase, allow only diode additions to existing nets, and create a
separate audited state without modifying original native state. Gate uses the
last full routing report and checks its database provenance. Strict positive
functional setup plus all ordinary timing/hold/electrical/antenna/overflow gates
remain.112focused tests plus real pinned config generation/order checks pass.
Candidate config19e89d36297436bc7b078f54f8b02d2b72629ce04e886b93e9ad3d523c4a4c0e.
No current physical result, main adoption, DRT or official GDS claim.

## Late repair/full-reroute result43994989722 and correction
Full flow and audits complete; final gate fails only3antenna nets/pins. Actual
functional setup fast/typical/slow+12.565165/+8.966791/+2.776346ns; stock hold
+.109586/+.331108/+.683447ns, electrical0, final full-route overflow0. Native
view/conservation/chain audits pass. All routine main CI at7834348passes.
Direct individual-job logs work when gh run view returns an empty file.

Artifact confirms native late repair reaches0antenna before the added full
GlobalRouting-1. After that extra reroute, failing sinks are _20819_→wire12281/A,
lane0time_now1→hold10555/A and net11763→wire11763/A. Do not treat the earlier
clean checkpoint as a qualified result for this completed failed flow.

D182 prepares a new clean config with antenna repair last: remove only the added
GlobalRouting-1 substitution, preserving every original Classic step. Retain
GRT_ALLOW_CONGESTION=false and prove zero preceding full-route overflow plus
successful native congestion-prohibited incremental antenna repair; receipt
explicitly identifies this verification rather than claiming a new numeric full
routing report. Pinned Tcl sets allow_congestion from the command flag, and pinned
GlobalRouter incremental repair rejects remaining overflow (GRT232). The newer
report_congestion command is absent from this pinned Tcl/binding; do not backport
it or reroute merely to obtain a report. Source references: [pinned Tcl](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.tcl),
[pinned incremental routing](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.cpp#L5295).

No waiver of antenna0, electrical0, fast hold50ps, stock constraints, positive
functional setup or original routing checks. Reject any later extra-route evidence
in final-antenna mode; retain six matching fresh NL/PNL readbacks and diode-only
connectivity conservation.120focused checks and actual official generation/merge
plus pinned exact step-order checks pass. New config0b7a388f659ae287b20580fbfa0572b36809df2fd04b63988c5499f3b66598bc.
Fresh native execution still required; no screen/route/official qualification yet.
