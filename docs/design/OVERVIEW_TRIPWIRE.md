# TRIPWIRE overview

TRIPWIRE is a firmware-programmable protocol emulator for the Jane Street ASIC competition, targeting the January 18, 2027 submission deadline (internal target: January 11).

The qualified design uses **8×4 Tiny Tapeout IHP CMOS5L tiles**, two reflex lanes, four timed pin units and one 512×16 SRAM at a 20 ns clock period. Phase 2 completed with a passing official GDS, precheck, gate-level test and viewer workflow. See [the baseline](../BASELINE.md) for the exact revision, timing measurements, hashes and signoff policy.

## How it works

A lane holds triggered reflex instructions rather than fetching an instruction on every fast-path reaction. Ready instructions act on registers and tokens; bounded routines in SRAM handle longer work. The multicast channel fabric connects lanes, the host and timed pin units. Pin units schedule and sample pin events independently of instruction timing. Protocol behavior lives in reloadable firmware, rather than dedicated UART, SPI or I2C hardware.

The [plain-language introduction](../HOW_IT_WORKS.md) explains these parts. The [architecture](ARCHITECTURE.md) and [ISA](ISA.md), together with `spec/tripwire.yaml`, define the hardware contract. Encodings and generated tables must stay synchronized.

## Current status and limits

- Phase 2 is complete; cleanup prepares the repository for Phase 3.
- The unchanged official flow passed on the full design. D-185 explicitly waives unsupported SRAM Magic checks while requiring zero full-GDS KLayout DRC violations.
- The exact final netlist passed 22 protocol scenarios. [The support matrix](../PROTOCOL_SUPPORT.md) distinguishes exercised scenarios from full protocol conformance.
- No fabricated-chip or board testing is available. Model feasibility work is not USB/Ethernet hardware support.
- Helper units such as MEM and CAPTURE remain deferred. Existing routines and general primitives are the first choice for showcase firmware.

## Phase order

| Phase | Purpose | Status |
|---|---|---|
| 0 | Environment and flow setup | Complete |
| 1 | Contract, independent model and risk exploration | Complete |
| 2 | RTL core and physical qualification | Complete; evidence in the phase checklist |
| 3 | Showcase firmware, independent verification and FPGA build | Next; no cleanup task counts as implementation |
| 4 | Stretch work and freeze | Planned |
| 5 | Evidence and submission documentation | Planned |
| 6 | Submission | Planned |
| 7 | Optional hardware validation | Off the critical path |

Each phase checklist in `docs/design/phases/` is its completion gate. The [Phase 3 plan](phases/PHASE3_SHOWCASE_PROTOCOLS.md) needs a fresh schedule review following the November 18 closure of Phase 2. Preserve the qualified hardware while extending firmware and evidence; any necessary hardware change needs a reviewed decision and fresh physical qualification.

## Historical planning

The original area estimates, three-lane/six-unit alternatives, 6×4 constraints and early schedule are preserved in the [pre-cleanup overview](https://github.com/Kanishk234/protocol-emulator-asic/blob/9b440582c489b228f8306a137f3a722bdfa8ed2a/docs/design/OVERVIEW_TRIPWIRE.md). They are exploration history, not the current resource contract.
