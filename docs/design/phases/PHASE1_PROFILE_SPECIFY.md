# Phase 1: Profile, specify, de-risk

**Dates:** Oct 5 – Oct 25, 2026
**Goal:** know, with measurements, what protocol logic actually needs and whether it can fit. Retire the biggest physical risk by hardening a tiny fabric on CMOS5L. Write the specs everything else follows.

## Tasks

### Seal the held-out set (do this first)
- [ ] Choose 3–4 held-out protocols (candidates: 1-Wire, WS2812, SWD, PS/2, JTAG, CAN). Pick a spread: timing-coded, clocked, bidirectional, and one with CRC or bit-stuffing if possible.
- [ ] Write `docs/design/HELDOUT.md` with the list, the scope of each, and the rule that nothing is written or profiled for them until the hardware freeze. Commit it before any profiling (the commit hash is the seal).

### Design-set protocol RTL (as user designs)
- [ ] `protocols/uart/`: TX and RX, configurable baud divisor, framing error.
- [ ] `protocols/spi_ctrl/`: all four modes, chip select, full duplex.
- [ ] `protocols/i2c_ctrl/`: start, repeated start, stop, ACK/NACK, clock stretching, open-drain outputs.
- [ ] `protocols/i2c_target/`: address match, small register map, read/write.
- [ ] Independent reference models in `tools/refmodels/` (written without reading the RTL) and RTL-level tests for each.
- [ ] Decode simulation waveforms with `sigrok-cli` protocol decoders as an extra independent check.

### Profiling
- [ ] `tools/profile/`: a script that synthesizes each protocol with Yosys onto generic LUT fabrics (LUT3, LUT4, LUT6; with and without carry) and reports LUTs, flip-flops, and a breakdown by function (counters, shift registers, comparators, control/FSM, other).
- [ ] Report in `docs/reports/profiling.md`: what dominates, which functions recur across protocols, and a ranked list of specialization candidates with the expected saving for each.

### Physical de-risking
- [ ] Harden a tiny (~16 LUT) FABulous fabric through the TT CMOS5L flow, with live configuration storage (not optimized away), passing precheck.
- [ ] From it, measure area per logic cell including configuration and routing; build a simple area model in `tools/areamodel/`.
- [ ] Estimate fabric capacity (logic cells) for 6x4 with the shell, leaving routing margin.

### Capacity go/no-go
- [ ] Compare the design set's needs (from profiling) with the estimated capacity, with and without the top specialization candidates.
- [ ] Decide in DECISIONS: continue with the pure specialized eFPGA, cut showcase scope, or switch to the hybrid fallback.

### Specs
- [ ] `ARCHITECTURE.md` v1: shell, host interface, pin allocation, load/start/stop/parking contract, clocking, fabric resource list for G0, and the candidate architecture variants to compare in phase 3.
- [ ] `VERIFICATION.md` v1: layers, check IDs, tools, what runs in which CI workflow.
- [ ] `PHYSICAL_DESIGN_AND_CI.md` v1: how the fabric is hardened and integrated, clock target, known limits.
- [ ] Risk register updated in `OVERVIEW.md`.

## Phase exit checklist
- [ ] `HELDOUT.md` committed before profiling (commit hash: …)
- [ ] All four design-set protocols pass their RTL tests against independent reference models (run IDs: …)
- [ ] `docs/reports/profiling.md` complete with a ranked specialization list
- [ ] Tiny fabric hardened on CMOS5L, precheck passed (CI run ID: …)
- [ ] Area-per-cell measurement and capacity estimate recorded
- [ ] Capacity go/no-go decision recorded in DECISIONS
- [ ] ARCHITECTURE, VERIFICATION and PHYSICAL_DESIGN_AND_CI v1 written
- [ ] All CI workflows green on `main`
- [ ] `docs/summaries/PHASE1.md` written
