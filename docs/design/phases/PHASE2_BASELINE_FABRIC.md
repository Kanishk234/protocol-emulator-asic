# Phase 2: Baseline fabric and shell

**Dates:** Oct 26 – Nov 15, 2026
**Goal:** a complete, submittable chip with a generic fabric (G0): shell, loader and fabric hardened at 6x4, running the design set from real bitstreams loaded through the real host interface. G0 is our fallback submission and the baseline every specialization is compared against.

## Tasks

### Shell
- [ ] Host interface (SPI-like, polled status) per `ARCHITECTURE.md`.
- [ ] Loader: length check, transport checksum, architecture-version tag, error handling.
- [ ] Run control: stop, start, reset of user state; outputs parked and output enables off whenever the fabric is stopped or unconfigured.
- [ ] Input synchronizers, registered outputs, open-drain support on bidirectional pins.
- [ ] Host data path to and from the fabric (FIFOs if the budget allows; record the decision).
- [ ] Host software: one Python API used by both simulation tests and future board software (`tools/host/`).

### Fabric G0
- [ ] Generic fabric at the size chosen in phase 1, defined in `arch/`, generated into `src/fabric_gen/`.
- [ ] Protocol compile flow: `tools/compile/` turns a user design + pin constraints into a bitstream and a report (architecture version, tool versions, resource use, timing, pins, checksum).
- [ ] The host rejects bitstreams built for a different architecture version.

### Integration and physical
- [ ] Full 6x4 hardening of shell + G0 passes precheck; record area breakdown, routing overflow, and timing at the chosen clock.
- [ ] Timing model for place and route derived from the implemented device (or a documented conservative model).
- [ ] `gl_test` loads at least two different real bitstreams into the gate-level netlist and checks behavior.

### Protocols on G0
- [ ] Compile all design-set protocols onto G0. For each: fits or not, resources, achieved timing. Report in `docs/reports/g0_results.md`.
- [ ] Pin-level tests (top-level ports only) for each protocol that fits, loaded through the host interface.
- [ ] Add the `fabric` CI workflow: compile every protocol and run it on the fabric simulation.

### Formal
- [ ] Output isolation: no protocol output or output enable is active while stopped or loading (property and bound recorded).
- [ ] Loader state machine: aborted or corrupt loads never reach the run state.

## Phase exit checklist
- [ ] Shell + G0 hardened at 6x4, precheck passed (CI run ID: …)
- [ ] `gl_test` green with two different real bitstreams (CI run ID: …)
- [ ] `docs/reports/g0_results.md` shows fit/resources/timing for every design-set protocol
- [ ] Formal properties pass with named bounds (proof log summary in `docs/reports/`)
- [ ] The `fabric` workflow is green
- [ ] Decision point recorded: G0 is a valid fallback submission (or what's missing)
- [ ] All CI workflows green on `main`
- [ ] `docs/summaries/PHASE2.md` written
