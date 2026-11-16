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
