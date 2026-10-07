# Late selection of RX timer arithmetic

Extraction 37566926240 leaves U3 RX timer bits 23/22 failing setup by 0.175213/0.048972 ns. The isolated rewrite computes timer and offset arithmetic before the live-input start decision, then selects the next value. It preserves sample clocks, modulo-width behavior, restart and framing priorities. `bs-event-rx-timer` retains event-late and changes only RX relative to that matched baseline.

Equivalence passes at FRAC=4/8. Corrected RX/full-feature tests pass 20/20, chip tests 5/5, and 2,048-clock L2 passes in `/tmp/rx-timer-late-20261006`. The first pin run exposed BUG73: the frozen carrier interface was disconnected. The opt-in harness flag fixes it; main's older interface also passes 20/20. Test fix commit: 64fa661. The reusable verifier archives committed tests, so its first attempt still had the old fixture. The corrected run in `/tmp/rx-timer-reusable-fixed-20261006` passes both module proofs, all 41 combined pin tests, five chip tests and 2,048-clock L2.

Matched mapping uses the same typical IHP library and ABC recipe, slow Liberty STA, an ideal 20 ns clock, zero IO delay and 0.01 pF output load, with no wires. Baseline a_in→rt arrival is 6.620677 ns versus 1.943963 ns after the rewrite. Worst a_in→any-register becomes 5.907698 ns at fw[0]. Module area grows from 9704.3184 to 12559.7682 µm² (+29.4%). Replication could add substantial area; specialization means simple multiplication is not a measured full-chip cost. Judge actual global overflow and extracted timing. No routed gain claimed.

Prepared screen and route choices bind both pin_bs and pin_rx, retaining independent successful-main provenance. Compare with event-late through `comparison_baseline`. The extra 150 ps repair remains restricted to the previous event-late variant. Main RTL/spec/config and official template jobs remain unchanged. This candidate still needs measured setup and hold closure, followed by official GDS validation.

## Completed matched physical screen (37572964628)

Both jobs completed successfully in about36minutes. Fresh post-repair setup WS is0ns at all three corners for both candidates; this is not positive global WNS or extracted timing. Hold WS(ns):

| Candidate | Fast | Slow | Typical |
|---|---:|---:|---:|
| Event-late baseline |0.0313302|0.229262|0.102516|
| Event-late + RX timer |0.0229828|0.255965|0.119296|

Both final global routes report zero overflow. Final post-repair instance-area totals from the logs: baseline510232.98um²/33205instances; RX517408.93um²/33994instances (+1.4064% area). Final routing demand239415→245441 (+2.52%),usage40.01→41.01%,capacity598422unchanged. These are matched full-chip GRT-stage measurements, not official DRC/precheck or extracted results.

The RX transformation is physically routeable at this stage, but worsens fast hold by8.3474ps. Setup improvement is not established by the aggregate0ns reports. Do not adopt or claim closure; examine endpoint paths and any bounded repair before spending a full official run. Logs cached in /tmp/rx-timer-screen-37572964628.log; artifact11462117187 contains RX evidence.

## Smaller shared-delta variant (local)

New isolated `rx_timer_shared.patch` computes `sample_delta=per-(1<<FRAC)` once and adds that value separately to `rt` and `sofs`. Both selected branches retain modulo-RW arithmetic, sample cycles and late START selection. No new register or protocol primitive.

With identical Yosys/Liberty mapping, RX area is11701.7082um² versus12559.7682 for the first late-selection variant (6.83% smaller;still20.58% above9704.3184 baseline). Slow ideal-wire a_in→timer arrival1.812930ns versus1.943963ns;worst a_in→any-flop6.063411ns versus5.907698ns. Thus it improves timer area/delay but slightly worsens another endpoint;these module probes are not full-chip WNS.

Independent frozen-baseline equivalence at FRAC4/8 passes;FRAC8 proves226points,induction closes atstep1underseq2cap. All41combined pin tests pass,0fail/skip. Matching frozen chip verification passes5/5;L2passes2048clocks withzero model divergence. First invocation incorrectly used current checkout generated encodings with frozen RTL; discarded that mismatched run and reran in matching frozen environment. Raw scratch evidence:/tmp/rx-timer-shared-20261007. No physical screen launched or mainRTL/config adoption.

## Shared-delta paired screen prepared

Named trial `bs-event-rx-shared` combines unchanged event-late bitsync with only the shared-delta RX transformation. CI supports the exact two-module mutation set, successful-main source provenance, separate RX/BS fingerprints and matched event-late baseline.181helper checks pass; both workflow choices parse. Fresh reusable verification proves BS and RXFRAC4/8;41pin tests,5chip tests and2048model/RTL lockstep clocks allpass. Raw evidence:/tmp/bs-event-rx-shared-verify-20261007.log.

Planned dispatch: `gh workflow run gds-drop-counter-screen.yaml --repo Kanishk234/protocol-emulator-asic --ref main -f experiment=bs-event-rx-shared -f comparison_baseline=bs-event-late`. Evaluate area, global overflow and all three corners; any routing continuation must retain its existing gates. No automatic adoption from diagnostic workflow success.
