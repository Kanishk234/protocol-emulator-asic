# Phase 3: Specialize, compare, hardware freeze

**Dates:** Nov 16 – Dec 6, 2026
**Goal:** turn the generic fabric into a protocol-specialized one, one measured change at a time, and freeze the hardware on the best variant the data supports.

## Method
Work through the ranked specialization list from `docs/reports/profiling.md`, top first. For each candidate:

1. Write a DECISIONS entry: the need (with profiling data), protocols that benefit, expected area cost, cost to protocols that don't use it.
2. Implement it: primitive RTL, behavioral model, fabric definition in `arch/`.
3. Make the tools use it: Yosys mapping (explicit instantiation first), placement and routing, bitstream configuration.
4. Test it: primitive corner cases (reset, simultaneous controls), then a compiled user design using it, loaded through the real interface.
5. Harden it: **one hardware change per hardening**; record area, routing overflow and timing.
6. Compare it with the previous variant at **equal total area**: coverage and performance on the design set.
7. Keep it only if the measured benefit justifies the cost. Record the result either way.

Stop adding features by Nov 30 regardless of how many remain.

## Tasks
- [ ] Candidate 1 (from profiling): full method above.
- [ ] Candidate 2: full method above.
- [ ] Candidate 3 (only if time allows): full method above.
- [ ] Optional experiment, only if profiling points to it: multi-context configuration (store 2 contexts and switch between them). Measure configuration-storage cost vs. capacity gained.
- [ ] Equal-area comparison of all variants: coverage × performance chart (Pareto front) in `docs/reports/architecture_comparison.md`.
- [ ] Choose the final architecture from the data; DECISIONS entry.
- [ ] Final hardening: precheck, timing at the chosen clock, routing overflow within limits.
- [ ] `gl_test` with at least two real bitstreams on the final netlist.
- [ ] Tag the commit `hw-freeze`. After this, hardware changes only for bugs, each with a DECISIONS and BUGS entry.

## Phase exit checklist
- [ ] Each attempted specialization has a DECISIONS entry with its measured result (kept or dropped)
- [ ] `docs/reports/architecture_comparison.md` with the equal-area comparison and chart
- [ ] Final architecture hardened, precheck passed, timing met (CI run ID: …)
- [ ] `gl_test` green on the final netlist with two real bitstreams (CI run ID: …)
- [ ] All design-set protocols recompiled and passing on the final architecture
- [ ] `hw-freeze` tag created (by the user)
- [ ] All CI workflows green on `efpga`
- [ ] `docs/summaries/PHASE3.md` written
