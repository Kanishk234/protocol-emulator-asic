# Phase 5: Evidence and documentation

**Dates:** Dec 23, 2026 – Jan 5, 2027
**Goal:** make the work understandable and checkable by a judge who has 20 minutes, and reproducible by someone who has a day.

## Tasks
- [ ] Evidence report (`docs/EVIDENCE.md`): the problem, the profiling data, each architecture decision and its measured result, the equal-area comparison chart, held-out results, verification summary, known limits. Every number links to a run ID.
- [ ] Audit `docs/CLAIMS.md`: every claim has evidence; remove or soften anything that doesn't.
- [ ] Comparison with prior art (Tiny FABulous, PRISM, RP2040 PIO, TI PRU): what we do differently, stated only as far as the evidence supports.
- [ ] User guide (`docs/USER_GUIDE.md`): write a protocol, compile it, load it, read status; supported Verilog subset; resource and rate limits.
- [ ] Architecture reference for users: resources, primitives and how to instantiate them, pin map.
- [ ] Tiny Tapeout datasheet section in `info.yaml` / `docs/info.md`: pinout, how to test.
- [ ] Clean reproduction: from a fresh checkout on a clean machine or container, rebuild bitstreams and run all simulation tests following only the README. Fix every gap found.
- [ ] README: one-paragraph pitch, quick start, links to evidence.

## Phase exit checklist
- [ ] `docs/EVIDENCE.md` complete, every number linked to a run ID
- [ ] `docs/CLAIMS.md` audited
- [ ] Clean-checkout reproduction succeeded (date, environment, notes)
- [ ] User guide and datasheet written
- [ ] All CI workflows green on `main`
- [ ] `docs/summaries/PHASE5.md` written
