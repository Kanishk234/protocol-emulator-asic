# Decisions

Format for each entry: ID, date, status (Proposed / Accepted / Superseded), decision, reason, alternatives considered, cost, evidence.

---

## D-001: Build on FABulous
- **Date:** 2026-09-25 · **Status:** Proposed (confirm in phase 0)
- **Decision:** Use FABulous for fabric generation, synthesis mapping, place and route, and bitstream generation, pinned to one release.
- **Reason:** Open source, supports custom fabrics and primitives, has a physical implementation flow and IHP precedent, and has been used on Tiny Tapeout before (Tiny FABulous).
- **Alternatives:** OpenFPGA (not developed in parallel); writing a fabric and toolchain from scratch (too much work for the schedule).
- **Evidence:** to be added in phase 0 (reference fabric demo).

## D-002: Domain-specific but protocol-agnostic
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** Specialize the fabric for protocol emulation, but never add a dedicated protocol block. Hard blocks and cell features must be general primitives useful to more than one protocol. Each addition needs profiling data, benefiting protocols, area cost, and cost to non-users.
- **Reason:** The brief rules out "a UART block, an SPI block and an I2C block"; generality after fabrication is the point.

## D-003: Design set and sealed held-out set
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** Optimize the architecture on a design set (UART, SPI controller, I2C controller, I2C target). Evaluate generality on a held-out set chosen and committed in phase 1, untouched until the hardware freeze.
- **Reason:** Without a held-out set, a specialized fabric can overfit to the protocols it was tuned on, and the generality claim can't be checked.

## D-004: Equal-area comparison
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** Architecture variants are compared at equal total area (fabric, configuration, routing, shell) and equal clock target.
- **Reason:** A variant using fewer LUTs is not better if its hard blocks cost more area than the LUTs saved.

## D-005: G0 is the fallback submission
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** The generic baseline fabric with the complete shell (phase 2) must be a valid, submittable chip before any specialization work.
- **Reason:** Guarantees a working entry if specialization runs late.
