# Event-path timing prototypes (2026-10-06)

All three patches are isolated against frozen R4 `3393eea`, preserving the full2/4 candidate and live-write semantics. No main RTL, spec, cycle timing, clock or constraints changed. They are not combined with the running resync route.

| Isolated candidate | Module equivalence points | Slow PERIOD→RX-load probe(ns) | Mapped module area(µm²) |
|---|---:|---:|---:|
| Frozen baseline |—|13.808641|40667.3184|
| `bs_load_flat.patch` |892|12.391160|40740.4998|
| `bs_event_late.patch` |892|11.697581|40591.0764|
| `bs_sample_predicate.patch` |818|13.980507|41529.5370|

The identical-library probes use typical IHP mapping, slow-corner STA, ideal20ns clock, zero IO delays,0.01pF output load and no wire parasitics, matching the previous prototype report. Late event gating improves this query by2.111060ns at−76.2420µm² mapped area; flattened producer load improves by1.417481ns at+73.1814µm². Neither establishes whole-chip WNS. The sample-predicate variant regresses both delay and area and should not consume a physical run on this evidence.

Flattened producer load reduces frame/status load arbitration to `rx_free&&(fr_want||st_v||st_new)` while retaining original tag/data priority and status/overflow updates. Late event gating computes completion qualification before the sample-dependent `fbit`: it combines flag/abort token existence and removes nested committed-bit/frame-count qualification from the producer's request path. Existing individual token conditions remain for payload and priority. Direct sample predicates split the modular subtraction/addition at the eight fractional bits and compute only the seventeen upper bits needed for sign-or-less-than256; this proves correct but maps worse.

Yosys equiv_simple plus equiv_induct with seq2 cap proves complete named-module equivalence; no unproven points remain. All three variants pass21bit-clock tests,5chip tests and2048-clock RTL/model lockstep. Raw evidence stays in `/tmp/timing-next-fixed-20261006/<candidate>/` (equiv.log,pin.log,chip.log,l2.log,probe/).

BUGS72: copying current model tools also copied main's generated3/6 resource tables into frozen2/4 fixtures. The first flattened-load chip run failed HOST_OUT forwarding. The verifier now regenerates Python encodings using the archived specification before tests and does not rewrite archived RTL. A regression checks exact4units/9producer/9consumer tables and unchanged RTL; all83timing-helper tests pass. This fixture correction is independent of the RTL optimization.

Named local verification support is prepared: run `source .venv/bin/activate`, then `python scripts/ci/verify_timing_trial.py bs-event-late /tmp/fresh-event-check --simulate` (substitute bs-load-flat or bs-sample-predicate as needed; output must be new). The existing matched screen is prepared with separate bs-event-late and bs-load-flat choices, independent concurrency groups and a baseline job for each. Timing-driven placement/all-corner repair remain enabled with0ns repair margin; no source/config/spec/template hardware change. The user explicitly approved separate commits, push and both screen launches.

Next: prioritize independent physical screens for event gating/load flattening. Assess resync and these variants independently before evaluating a clean-synthesis combination. No new dispatch, adoption, phase tick, extracted gain or official timing pass is claimed here.
