# Event-late plus parallel drop qualification

The 150 ps event-late repair fixes extracted fast hold (+0.067034 ns) but regresses slow setup (−0.389409 ns). The report contains nine failing dropped-counter paths and two U3 RX timer paths, launched by live PIN_A selection. The worst two counters include hold-delay cells adding about 0.62–0.66 ns; other paths also worsen. Evidence: routing run 37559740009, extraction 37566926240, artifact 11459002750.

The `bs-event-drop-qual` combination applies the previously proved event-late and parallel per-source drop qualification to frozen candidate 3393eea. It preserves live configuration, same-cycle counter behavior, the complete 2/4 resources and 20 ns clock. It does not directly address the RX timer paths, and has no measured physical benefit yet.

The first isolated combination passed channel equivalence at N=1/5/6/7/9/16, channel tests, five chip tests and a 2,048-clock model/RTL comparison. Evidence is in `/tmp/event-drop-qual-20261006`. The reusable verifier now proves each changed module separately and runs channel, pin, chip and L2 suites; the fresh proofs and all four simulation suites passed. Results are in `/tmp/event-drop-qual-reusable-20261006`.

CI preparation adds an exact two-file mutation whitelist and fingerprints both files from an independent frozen checkout plus the named patch. Successful main workflow provenance and routing/downstream guards remain required. The optional `comparison_baseline=bs-event-late` makes the paired screen isolate only drop qualification. Existing defaults remain timing-placement/drop-counter. All 143 helper tests pass and both workflows parse. The screen's default hold-repair target and all-corner policy are unchanged. The extra 150 ps routing option remains restricted to the earlier event-late variant.

Proposed dispatch after reviewed publication:

```bash
gh workflow run gds-drop-counter-screen.yaml --ref main \
  -f experiment=bs-event-drop-qual -f comparison_baseline=bs-event-late
```

Publish CI/helpers/tests and prototype patches separately from documentation. The local `timing_trial.py` also contains previously verified resync-event/resync-load registrations; their matching patches must accompany publication. Keep SRAM prototypes, the execution report helper and unrelated readiness updates separate. No remote dispatch or main RTL adoption occurred during preparation.

## Paired screen outcome

Run37569441149 completed diagnostically. Both variants retain estimated setupWS0 at allcorners. Event-late baseline fast hold+0.0313302ns; event/drop-qualification fast hold−0.0184668ns afterrepair (slow+0.158524ns,typical+0.0647883ns). Therefore the combination fails the fresh fast hold gate and must not be sent directly to routing or promoted. No extracted gain established. This result does not invalidate its functional proofs, but shifts priority to another candidate or a separately measured hold repair.
