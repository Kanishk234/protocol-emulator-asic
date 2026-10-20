# Work independent of the combined screen

2026-10-20. Screen 39458833532 is still in progress; no result inferred.
These are prioritized engineering hypotheses, not measured improvements.

| Priority | Follow-up | Evidence and expected benefit | Cost or qualification risk |
| --- | --- | --- | --- |
| 1 | Diagnose electrical reserve by repair stage | Staging-only screen39378465307 ends with lane-control net11513 and TX-cursor net15192 over the fixed slew reserve. Compare the same source's pre-repair, post-design-repair, post-timing-repair and post-antenna reports before choosing a fix. | Instance names cannot be transferred to the new source. Inserted buffers prove repair ran, not that its final reserve passed. Additional audit runs should be diagnostic, with acceptance unchanged. |
| 2 | Rewrite TX cursor next-state selection | In trw_pin_tx.v, qn selection feeds a conditional increment into all16 eq bits. Evaluate parallel candidate next values followed by late selection, instead of selecting qn before the carry chain. The previous offending nor4 drives cursor mux selects. | Replicated arithmetic may increase area or optimize back into the original structure. Preserve qn==7fff saturation, rn==presc wrap, synchronous restart, SYNC/late precedence and modulo arithmetic. Formal equivalence first, then paired mapped area/depth before physical screening. Structural reachability alone does not prove this is the critical path. |
| 3 | Unit-local slot write staging | trw_slots.v still captures shared wdata every cycle. The prior topology has104 slot-latch loads across two lanes after pin-unit staging is separated. Enable the existing16-bit stage only for writes to its lane, analogous to the verified pin-unit experiment. | May prevent merging and add one16-bit bank plus enable logic relative to shared mapping. Needs a separate registered-host latch-phase proof, reset/idle/consecutive-write tests and full protocol replay. Useful only if current lane/config arrival remains limiting; does not directly fix TX cursor logic. |
| 4 | Measure detailed-route sensitivity from matched evidence | Event-late wire150 screen had slow capture+1.483047ns; its completed route had setup−1.608072ns. That pair motivates reserve, but the two extrema need not describe the same path. Match endpoint, launch, borrowing, clock arrival, cell delay and wire delay before attributing the difference to RC. | One pair is not a universal multiplier or a guarantee. Keep the3.5ns screen guard and all extracted gates. Never substitute global setup WS0 for FF capture headroom. |

## Routing preparation

The current native_post_antenna_route.validate_provenance explicitly expects
source_variant=bs-event-late. The existing wire150 route profile is bound to
run39177724036 and its old SHA. Neither is a valid continuation for the running
combined source.

After a successful combined screen, prepare a dedicated profile bound to its
exact run/head/workflow, both RTL hashes, original SDC and physical recipe.
Recompute the measured capture reserve from the saved reports as well as the
electrical/antenna gates before routing. Tests must reject a failed source,
wrong variant/hash, missing capture report, insufficient reserve or stale
checkpoint. Do not generalize the old helper by weakening its source checks.

No new physical experiment is launched here. Main RTL, acceptance thresholds,
protocol behavior and the ongoing screen remain unchanged. The combined
candidate already passed22/22 local protocol tests; rerunning those identical
bytes adds less information than these targeted follow-ups.
