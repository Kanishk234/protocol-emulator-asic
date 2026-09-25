# Phase 4: Protocols, showcase, held-out evaluation

**Dates:** Dec 7 – Dec 22, 2026
**Goal:** show what the frozen chip can do. Everything in this phase is bitstreams and tests, not silicon changes, which is the core claim of the project: new protocols after fabrication.

## Tasks

### Held-out evaluation (the generality test)
- [ ] Unseal `HELDOUT.md`. For each held-out protocol: write the user design and an independent reference model, compile onto the frozen fabric, test.
- [ ] Report every result honestly in `docs/reports/heldout_results.md`: fits or not, resources, rate reached, what limited it. Failures are results too.
- [ ] Compare held-out resource use on the final architecture vs. G0 (from a G0 build) to show whether specialization generalized.

### Showcase
- [ ] I2C target with fault injection: normal register-map operation, plus host-selected NACK and clock-stretch insertion, with host-readable status.
- [ ] Concurrency demo if resources allow (e.g. I2C target plus UART at the same time).

### Stretch protocols (only after the above)
- [ ] Pick from remaining candidates (JTAG, SWD, PS/2, 1-Wire, CAN). Report fits and failures.

### Robustness and verification depth
- [ ] Reconfiguration tests: stop, partial transfer, bad checksum, wrong architecture version, reload, restart; outputs stay parked until a valid start.
- [ ] Input phase tests: external protocol edges at varied phases relative to the system clock.
- [ ] Fault injection (mutation) campaign: wrong configuration-bit position, timer off-by-one, lost FIFO item, inverted output-enable. Each must be caught; investigate any that survive.
- [ ] Bounded equivalence or co-simulation between a protocol's source RTL and its configured-fabric simulation for at least one small design.

## Phase exit checklist
- [ ] `docs/reports/heldout_results.md` covers every held-out protocol
- [ ] Showcase passes its tests from a real bitstream through the host interface (run ID: …)
- [ ] Reconfiguration test suite green (run ID: …)
- [ ] Fault-injection results recorded; no unexplained surviving faults
- [ ] No hardware changes since `hw-freeze` except logged bug fixes
- [ ] All CI workflows green on `main`
- [ ] `docs/summaries/PHASE4.md` written
