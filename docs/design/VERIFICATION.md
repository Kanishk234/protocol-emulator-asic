# Verification, v1

**Status:** v1, written 2026-09-26 at the end of phase 1. Every check has an ID; bugs in `docs/BUGS.md` name the check that caught them and the one that now covers them.

## Principles
- **Independent references.** Reference models (`tools/refmodels/`) are written from the protocol specifications before, and without reading, the RTL they check. Where sigrok has a decoder, it is a second, fully independent oracle. Honest limit so far: one author wrote models and RTL, so independence is by order of writing plus sigrok.
- **Real interfaces.** Pin-level tests (`test/`) touch only top-level ports and also run on the gate-level netlist (`gl_test`). Bitstreams are loaded through the real host interface (ARCHITECTURE §2–3), never pre-initialized, except in the labelled fast "emulation" mode (V2).
- **Configuration survives synthesis.** Gate-level tests load real bitstreams; no configuration bit is tied to a constant in the chip build.
- **Every bug gets a covering check** (BUGS format), and mutation runs (V7) test that the checks catch deliberate faults.

## Layers
| ID | Layer | What it checks | Tools | Where | Status |
|---|---|---|---|---|---|
| V0 | Static | Lint (Verilator `-Wall`, Icarus `-g2005`), source lists in sync, Yosys synth sanity, TT docs check | Verilator, Icarus, Yosys, tt_tool | `lint`, `scripts/check_all.sh`, `gds` docs step | running |
| V1 | Models and primitives | Reference models self-consistent (round trips, hypothesis); later hard primitives and shell blocks at corner cases | pytest, hypothesis; cocotb, formal | `unit`, `formal` | models running (25 tests); primitives phase 3 |
| V1P | Protocol user designs (RTL) | Each design-set protocol against its reference model + sigrok, several configurations | cocotb, Icarus, sigrok-cli | `unit` (`protocols/*/test`) | running: UART 3, SPI 6, I2C ctrl 3, I2C target 3 configs |
| V2 | Configuration mapping | A bitstream's bits land in the intended configuration latches; emulation mode (latches pre-initialized) vs real load give the same behaviour | cocotb, FABulous sim | `fabric` | FABulous demo two-bitstream check running; own fabric phase 2 |
| V3 | Source vs. fabric | A protocol's source RTL and the configured fabric behave the same at the pins, cycle by cycle (the FABulous demo method), then bounded equivalence for one small design | cocotb, SymbiYosys/EQY | `fabric`, `formal` | phase 2 |
| V4 | Protocol peer (chip level) | Protocols running from bitstreams on the whole chip, against the reference models and sigrok, through the host interface | cocotb | `test`, `fabric` | phase 2 |
| V5 | Reconfiguration and robustness | Stop, partial transfer, wrong ARCH_VERSION, bad length, bad CRC, reload, restart; outputs parked until a valid RUN; input edges at varied phases | cocotb | `test`, `nightly` | phase 4 (basic parking/config-session tests exist in `test/` for the spike) |
| V6 | Gate level | `test/` on the hardened chip netlist with real bitstreams; the fabric macro modelled by its RTL (D-023), its own netlist to be checked by per-tile equivalence | TT `gl_test`, `scripts/gl_local.sh` | `gds` | running: 16/16 with real bitstreams (CI 36342012141 with the macro netlist; since D-023 with the macro RTL) |
| V7 | Fault injection | Deliberate faults (config bit position, timer off-by-one, lost FIFO item, inverted OE, parking gate removed) must each fail a check | scripts + mutated RTL | `nightly` | phase 4 |

## Formal properties (name, property, bound)
| ID | Property | Scope | Bound | Status |
|---|---|---|---|---|
| F1 | Output isolation: if STATE ≠ RUNNING then all fabric output pins and all `uio_oe` bits are 0 (ARCHITECTURE §4) | shell with the fabric as a free (unconstrained) black box | unbounded (k-induction) target; ≥ 64-cycle BMC minimum | phase 2 |
| F2 | Aborted or corrupt loads never reach RUNNING: after a LOAD_BEGIN, RUNNING requires a LOAD_END whose CRC and length match | shell (host interface + loader) | ≥ 64-cycle BMC over arbitrary host byte streams; k-induction target | phase 2 |
| F3 | Host channel FIFOs: no loss or duplication; overflow sets ch_overflow and drops only the new byte | shell FIFO | unbounded (induction) | phase 2 |
| F4 | Primitives: cycle-exact behaviour vs. a one-line spec model (timer, shift register) | each primitive | unbounded (induction) | phase 3 |

"Formally verified" is only ever claimed with the property ID and its bound (CLAUDE.md).

## Coverage goals
- Protocols: every feature in each `protocols/<name>/README.md` "Covered" list has a test; each design runs in ≥ 2 configurations (rates/modes).
- Shell: every command × every state (ARCHITECTURE §2.3) once; every ERROR_CODE produced at least once.
- Fabric: every tile type and every primitive exercised by at least one compiled design loaded through the host interface.
- Held-out set: not covered until the hardware freeze (D-003); then one design per protocol, reported pass or fail.

## Tools and versions
`docs/VERSIONS.md`. Simulators match CI (D-007). sigrok-cli from Ubuntu 24.04 apt (local and CI).
