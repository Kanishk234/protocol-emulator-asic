# Phase 5: Evidence and documentation

**Dates:** Dec 23, 2026 – Jan 5, 2027
**Goal:** make the work understandable and checkable by a judge who has 20 minutes, and reproducible by someone who has a day.

## Tasks
- [ ] Evidence report (`docs/EVIDENCE.md`): the problem, the profiling data, each architecture decision and its measured result, the equal-area comparison chart, held-out results, verification summary, known limits. Every number links to a run ID. (phase 4 CI IDs filled 2026-09-28; local measurement references still need the final evidence audit)
- [x] Audit `docs/CLAIMS.md`: every claim has evidence; remove or soften anything that doesn't. (C1–C10 audited 2026-09-28; CI IDs filled for the phase 4 results, local and board limits stated)
- [x] Comparison with prior art (Tiny FABulous, PRISM, RP2040 PIO, TI PRU): what we do differently, stated only as far as the evidence supports. (`docs/reports/prior_art_comparison.md`)
- [x] User guide (`docs/USER_GUIDE.md`): write a protocol, compile it, load it, read status; supported Verilog subset; resource and rate limits. Must cover the organizers' three items (D-032): description → bitstream flow, loading onto the chip, working UART/SPI/I2C examples. (`docs/USER_GUIDE.md` + `docs/EXAMPLES.md`)
- [x] Architecture reference for users: resources, primitives and how to instantiate them, pin map. (`docs/USER_GUIDE.md` §1, §3, §4; cycle-exact detail in ARCHITECTURE §8)
- [x] Tiny Tapeout datasheet section in `info.yaml` / `docs/info.md`: pinout, how to test. (rewritten for G1 2026-09-28)
- [x] Clean reproduction: from a fresh checkout on a clean machine or container, rebuild bitstreams and run all simulation tests following only the README. Fix every gap found. (standard fresh Ubuntu24.04 runner37690896748,962da93; pinned tool/README/source provenance, rebuilt images, strict loaded30/30 and cosim1/1 XML verified; docs/reports/reproduction.md; no physical/native/SDF claim)
- [x] README: one-paragraph pitch, quick start, links to evidence.

## Phase exit checklist
- [ ] `docs/EVIDENCE.md` complete, every number linked to a run ID
- [x] `docs/CLAIMS.md` audited (`docs/CLAIMS.md`, 2026-09-28; C1–C10 each carry CI or explicitly local evidence)
- [x] Clean-checkout reproduction succeeded (2026-10-07, fresh Ubuntu24.04 runner37690896748,962da93; retained result/command logs/XML inspected, docs/reports/reproduction.md)
- [x] User guide and datasheet written (`docs/USER_GUIDE.md`, `docs/EXAMPLES.md`, `docs/info.md`, `info.yaml`)
- [ ] All CI workflows green on `efpga`
- [ ] `docs/summaries/PHASE5.md` written
