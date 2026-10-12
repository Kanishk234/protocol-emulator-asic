# Baseline improvement execution backlog

Updated2026-10-11. Research and all30 recommendations with costs/sources are in
[baseline_improvement_research_20261011.md](../reports/baseline_improvement_research_20261011.md).
This implements the user's instruction to improve the baseline alongside compact
closure. Frozen G1 remains the control; no silent hardware/spec changes.

| Track / research ideas | State | Next acceptance gate |
|---|---|---|
| Host transport and budget1–2 | Analytical budget and portable C99 callback channel driver implemented; board backend pending | Budget boundary/error tests plus existing host tests303PASS local; cloud unit pending. Native transport must retain status/backpressure/CS timing and independent shell-model tests before any speed claim. |
| Reusable HDL and recognition3–4 | wp_delay/wp_shift_transaction helpers implemented; recognition pending | Reuse existing WP_TIMER/WP_SHIFT; exact cycle semantics and compiled/loaded behavior; no hard-block additions. |
| Compiler mapping/advice5–7 | Existing seed/control screens retained; further mapping pending | Accurate primitive arcs, equivalence, same-workload resource/fit/timing screen. Do not repeat failed seed/FSM settings as gains. |
| Triggered faults/capture8–9 | Existing externally timed fault/queued capture demos available; autonomous extensions pending | Compile on88LC baseline and load through real interface; trigger timing, loss, wrap and recovery independently checked. |
| Transformation/personalities/host stacks10–12 | Pending | Bounded resource/pin/host-service scope; no time-critical host round trips assumed. |
| Recovery/coverage/certificates13–15 | Existing reset/STOP/jitter coverage; broader certificates pending | Exact bitstream provenance plus actual mode-specific evidence; estimated timing labeled. |
| External challenge/replay16–17 | Relative capture replay planner implemented; hardware replay/external challenge pending | Fresh sealed evaluation and user-facing reproduction, bounded capture precision/storage. |
| Queue/SRAM/CRC/capture/fractional hardware18–22 | Research only | Demand/cost profiling and architecture decision before implementation; matched physical/tools/loaded qualification. |
| Local wiring/remapping/LUT/arithmetic/event lanes23–27 | Research/spikes only | One feature at a time, equal-total-area control, generator/tool support, fresh sealed evaluation. |
| Sampling/parameters/power28–30 | Research only | Spec/CDC/reset/compatibility review and explicit measurement; no inferred gains. |
| Compact shell whitespace closure | Independent cloud diagnostic38166250744SUCCESS | Authenticate actual rows/blockages, select a measured legality/electrical-clean placement policy, then native GRT. net694 rejected146→154; net683 best136 remains failing. |
| Same-build successor signoff | Open | All matched tiles, shell fanout/routing, complete timing modes, loaded tests, official flow/precheck; use project_recovery_evaluation_20261011.md. |

## Work completed now

`tools/board/budget.py` provides a CLI and reusable `plan()` with exact rational
capacity comparisons and integer queue bounds. For a single direction it models
an arrival envelope burst+rate*t, one initial service blackout, then bounded
one-byte service intervals. It includes one STATUS poll and current channel
command (read3total wire bytes, write4), two transaction frame costs and explicit
host overhead. It rejects unsupported clocks, nonfinite/negative inputs and
invalid queue counts. Exact-capacity traffic has no strict service margin.

This is an analytical model, not a board performance measurement, full-duplex
scheduler, or guarantee under arbitrary recurring host pauses. Any claimed
service interval must include those pauses and protocol-side availability.
Default queue depth2 reflects the existing shell; hypothetical extra queue
capacity does not change the chip. Tests cover burst overflow despite adequate
average bandwidth, capacity equality, asymmetric framing and invalid inputs.

No30-item checklist is marked complete merely because research exists. Each
track needs its own concrete implementation and evidence. Hardware revisions
remain behind project phase/freeze/spec requirements; software and bitstream
work can progress on the passing fallback without waiting for compact routing.

## Parallel implementation continuation

Three agents implemented disjoint baseline-compatible features under root review:
portable allocation-free C99 channel APIs with bounded polling and confirmed
partial progress; WP_TIMER/WP_SHIFT-aware one-shot delay and bounded serial
transaction helpers; loss-aware relative trace-to-replay timing windows. Root
combined board/host/helper tests:347PASS and3localHDL skips (cloud-only EDA).
Cloud unit now installs Icarus and must execute all three helper simulations;
helper_compile.yaml separately compiles the example on frozen G1. No loaded
helper image or board/DMA backend throughput pass is claimed.

Physical trialD-080 is running38167016013:24same-row cells shift1.92µm into
authenticated free tail and one reset tie moves next to its receiver. This is
one bounded copied-placement policy, preserving all other instances and exact
connectivity; native legality and six electrical/timing screens precede routing.

Further execution: independent C/shell-model coverage22tests and conditional
operating-report generation implemented; root board/host385testsPASS. Actual
cloud helper behavioral retry38167350632 pytest462PASS. Same-job loaded helper
workflow38167521573 running; loaded success not yet claimed. Receiver-local
row policy reduces native146→145 in38167244563, still fails; D081 tests interaction
with separately measurednet683136 rather than assuming additive gains.

Actual loaded helper38167521573SUCCESS: same-job compile/bitstream/realSPI load,
A5serial/completion/USER_RESET/STOP chip-port case passes with strict1-caseXML.
ExistingD023RTLfabric scope, no native/SDF or new physical clock claim.

## Current measured continuation (session84)

Portable C checked word/WBIT loading and sticky-error recovery are implemented
and independently model-tested. Root board/host regression415PASS; four new
scheduler source tests skip locally by policy and await cloud Icarus. Operating
reports now authenticate architecture pin-table provenance and physical labels.
These are baseline-compatible software changes, with no board-speed claim.

Autonomous triggered UART fault demo compiler38168186117PASS:57/88LC,2/2timers,
2/2shifts. ActualimageSHAa74a2909c144951c41e1f5276e110ae1e7619fb4d078062a83fb886438aefefb.
Loaded run38168215538 fails before loading because the workflow selected the
wrong filename; corrected same-job retry38168413654 pending. No loaded pass yet.

Combined exact placement paired38168159774 improves146→133overflow and111→91
markers, still nativeFAIL. New connectivity audit finds34/91markers without any
tie-driven net; overlapping membership is not causal attribution. See
compact_congestion_membership_20261011.md for hashes and next bounded buffer
placement hypothesis. No phase boxes ticked or successor promoted.

Actual corrected loaded38168609080SUCCESS: independently authenticated strict
onecaseXML/no failures/errors/skips and unchanged imageSHAa74a2909….
Autonomous window/trigger/event/reset-idle/STOP behavior passes through realSPI
under D023RTLfabric scope. Source scheduler corners execute in cloud532-check
pytest job38168413502/114555697291. No new physical or native clock claim.

## Confirmed loaded continuation (2026-10-12)

Loaded38279446388 passes full-duplex UART RX during autonomous TX faults,
concurrent event counting and later clean-frame recovery for both counter widths.
Both remain57/88LC with2/2timers and2/2shifts; keep the4-bit counter.
Compiled C integration38293580979 passes real simulated SPI loading/recovery,
31-byte duplex order/last indication, USER_RESET and STOP on a fresh hostecho
image using23/88LC. Exact image/hash/XML evidence: status_and_hold_allocation_20261012.md.
These baseline additions use D-023 configured-fabric RTL scope; no new physical
clock, native/SDF or board throughput claim. Their earlier pending statuses above
are historical, superseded by these named runs.
