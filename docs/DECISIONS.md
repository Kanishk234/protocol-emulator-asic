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
- **Date:** 2026-09-25 · **Status:** Superseded by D-008 (a generic fabric holds ~96 LUT4s at 6x4; one UART needs ~215)
- **Decision:** The generic baseline fabric with the complete shell (phase 2) must be a valid, submittable chip before any specialization work.
- **Reason:** Guarantees a working entry if specialization runs late.

## D-006: Provisional pin allocation
- **Date:** 2026-09-25 · **Status:** Proposed (finalized in `ARCHITECTURE.md` §1, phase 1)
- **Decision:** Shell host interface on `ui[0]` CS_N, `ui[1]` SCK, `ui[2]` MOSI, `uo[0]` MISO, `uo[1]` IRQ. Everything else goes to the fabric: `ui[3..7]` (5 inputs), `uo[2..7]` (6 outputs), `uio[0..7]` (8 bidirectional, needed for open-drain I2C and 1-Wire).
- **Reason:** the TT `check-docs` step rejects an empty pinout, so `info.yaml` needs a pinout before the spec exists. SPI-like host port with polled status per OVERVIEW; IRQ is optional and can be dropped.
- **Alternatives:** host port on `uio` (costs bidirectional pins the protocols need); a 2-wire host port (fewer pins, slower loads).
- **Cost:** 5 of 24 pins go to the shell.
- **Evidence:** none yet; revisit with the pin needs of the design set and the showcase.

## D-007: Local tool PATH order
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** System `/usr/bin` comes first; `~/oss-cad-suite/bin` is appended to the end of PATH (`scripts/check_all.sh` and `scripts/gl_local.sh` do this themselves). Python runs only in `.venv`.
- **Reason:** CI's `test` and `lint` jobs use Ubuntu 24.04's apt Icarus 12.0 and Verilator 5.020, which are also the WSL system versions. The OSS CAD Suite ships its own newer Icarus and Verilator; appending it keeps the CI versions in front while still providing Yosys, nextpnr and SymbiYosys.
- **Evidence:** local `iverilog -V` 12.0, `verilator --version` 5.020 (Debian 5.020-1); `scripts/check_all.sh` and `scripts/gl_local.sh` pass (2026-09-25). Versions in `docs/VERSIONS.md`.

## D-008: A generic fabric is probably not a viable fallback at 6x4; revisit D-005
- **Date:** 2026-09-25 · **Status:** Accepted (Kanishk, 2026-09-25): G1 is the fallback only; the goal is still the full specialized architecture from phase 3. Supersedes D-005
- **Finding:** `docs/reports/capacity_early.md`, updated by the tile hardening `docs/reports/tile_cmos5l.md`: measured ~5.1K µm² per LUT4 at 97 % density on CMOS5L, so **~96 LUT4s** fit at 6x4 with margin. Earlier synthesis-only numbers follow. The stock FABulous LUT4AB tile costs ~4.5K µm² of cells per LUT4 on cmos5l (77 config bits per LUT, 53 % of the area). At 42–60 % density a generic 6x4 fabric holds roughly **60–90 LUT4s**. A scratch UART (TX + RX, 16-bit divisor) needs **~215 logic cells**.
- **Proposal:** the fallback submission becomes **G1 = G0 + the smallest set of general hard primitives that lets the design set fit** (first candidates: loadable counter/timer, shift register), instead of pure G0. G0 stays the baseline for the equal-area comparison (D-004), measured at equal area, even if it fits nothing.
- **Also worth trying before adding hard blocks:** a slimmer routing architecture and tile (fewer wires per channel, fewer config bits per LUT) than the stock general-purpose one.
- **Alternatives:** keep D-005 and shrink the design set (e.g. UART TX only); go to the hybrid fallback (OVERVIEW decision points) now.
- **Cost:** the fallback depends on hard-block integration (Yosys mapping, nextpnr, bitstream) working, which is a known risk (OVERVIEW top risks).

## D-009: Phase 0 decision point: a known path exists to put a FABulous fabric through Tiny Tapeout
- **Date:** 2026-09-25 · **Status:** Accepted (answer to the phase 0 decision point); integration choice Proposed
- **Answer:** yes. Tiny FABulous (`docs/notes/tiny_fabulous.md`) hardened tiles with LibreLane's `FABulousTile` flow, stitched them with `FABulousFabric`, integrated the fabric as a macro in a top-level LibreLane run, and submitted through TT's `custom_gds` action. Its tile library already has IHP-specific tiles.
- **Our plan (proposed):** harden the fabric as a macro locally (or in our own workflow), commit it under `macro/`, and integrate it in the **template's** `gds` job with a `MACROS` block. The TRIPWIRE R3 spike integrated the IHP SRAM macro this way and passed precheck and `gl_test`. This keeps the template's jobs, precheck and `gl_test` intact (CLAUDE.md CI rules). Fall back to Tiny FABulous's `custom_gds` route only if the template flow can't integrate the fabric; that needs a DECISIONS entry and the organizers' OK (phase 0 email question 2).
- **Next evidence:** harden one tile on cmos5l with `FABulousTile` (needs OpenROAD/KLayout/Magic locally: Nix or the LibreLane container).

## D-010: Patch the FABulous tile library for CMOS5L's 5-layer metal stack
- **Date:** 2026-09-25 · **Status:** Accepted (spike)
- **Decision:** use `mole99/fabulous-tiles` at 7999e5a (the Tiny FABulous tile library) with `spikes/tile_cmos5l/cmos5l.patch`, applied to a fresh clone in `build/`, never to the upstream checkout. The patch (1) gives `ihp-sg13cmos5l` its own routing-obstruction list (Metal1–Metal4 + TopMetal1) ahead of the `ihp-sg13*` entry, which lists Metal5/TopMetal2; (2) adds a `pdk::ihp-sg13cmos5l` section to the tiny library's `common.yaml`, with the power grid of the PDK's own LibreLane config (Metal4 vertical, TopMetal1 horizontal, 50 µm pitch) and `RT_MAX_LAYER: TopMetal1`.
- **Reason:** CMOS5L has only 5 metal layers (`libs.tech/librelane/config.tcl`: "M1-M4-TM1, no Metal5/TopMetal2"). The upstream IHP settings are for SG13G2 (7 layers) and reference layers that don't exist.
- **Consequence to watch:** one fewer signal layer than SG13G2, so the SG13G2 tile size and 96 % density may not route. Measured in `docs/reports/tile_cmos5l.md`.
- **Revision (run 2, same day):** `RT_MAX_LAYER: Metal4` (the TT CMOS5L top level routes only to Metal4; TopMetal1 is its power grid) and KLayout stream-out with the Magic stream-out/DRC/LEF/extraction and LVS steps skipped in the tile config (BUGS #2; the PDK has no CMOS5L LVS yet). Run 1 used `RT_MAX_LAYER: TopMetal1`. Run 3 adds a driver fix to `tiles.py`: apply `meta.substituting_steps` removals (the librelane CLI does, the driver did not).

## D-011: The `unit` workflow arrives with the first Python tool
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** phase 0's "add `lint` and `unit` workflows" is met by `lint` now; `unit` (pytest over `tools/`) is added in the same commit as the first Python tool with tests (phase 1: `tools/areamodel/` or `tools/refmodels/`). The phase 0 box is ticked for `lint`, the `gds` paths filter and concurrency, and marked as deferred for `unit` with this reference.
- **Reason:** there is no Python code yet; a `unit` workflow with nothing to test would pass without checking anything.
- **Meanwhile:** `fabric` (added early) runs the FABulous flow in CI.

## D-012: Close phase 0 with the organizer email outstanding
- **Date:** 2026-09-25 · **Status:** Accepted (Kanishk: "start phase 1, email doesn't matter")
- **Decision:** phase 0 is closed with its two email items marked waived, not passed. Phase 1 starts.
- **Reason:** the email's answers (eFPGA eligibility, a hardened macro inside the template flow) don't change phase 1's work. Every other phase 0 exit item has evidence.
- **Follow-up:** if the email is sent, log the date and the answer here.

## D-013: Held-out set sealed: WS2812, 1-Wire, SWD, CAN
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** `docs/design/HELDOUT.md`: H1 WS2812 TX, H2 1-Wire controller, H3 SWD host, H4 CAN 2.0A. PS/2 and JTAG stay free (stretch/design set).
- **Reason:** phase 1's criteria: a spread of timing-coded (H1, H2), clocked with turnaround (H3), bidirectional/open-drain (H2, H3, H4), and CRC plus bit-stuffing (H4). PS/2 and JTAG are too close to the design set (a device-clocked shift register, SPI-like shifting) to test generality.
- **Seal:** the commit that adds `HELDOUT.md` (hash recorded in the phase 1 checklist).

## D-014: Provisional user-design interface
- **Date:** 2026-09-25 · **Status:** Proposed (formalized in `ARCHITECTURE.md` v1, phase 1)
- **Decision:** every protocol user design exposes: `clk`, `rst_n` (from the shell; held low while the fabric is stopped or loading); its pins as input / output / output-enable signals; a host → design byte channel `h_wdata/h_wvalid/h_wready`; a design → host byte channel `h_rdata/h_rvalid/h_rready`; and an 8-bit `h_status` the host can read at any time. Settings (e.g. a UART divisor) are Verilog parameters fixed in the bitstream by default; a design may also offer a run-time register (`RUNTIME_*`) so both can be profiled.
- **Reason:** protocols have to be written and profiled before the shell exists; a byte channel in each direction plus status is the smallest host path that serves UART, SPI and I2C. Fixing settings in the bitstream is how an FPGA is normally used, and it is much cheaper: the UART is 171 LUTs with a fixed divisor and 262 with a run-time one.
- **Alternatives:** a memory-mapped register window (more flexible, more fabric logic); wider channels.
- **Revision (SPI controller):** the host → design channel carries a 1-bit `h_wlast` flag with each byte, marking the end of a transaction (e.g. SPI chip-select release); designs that don't need it ignore it.
- **Cost:** the shell must provide both byte channels (the write side with `h_wlast`) and the status read (ARCHITECTURE §2).

## D-015: The `unit` workflow (closes D-011)
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** `.github/workflows/unit.yaml` added with the first Python tool (`tools/refmodels/uart.py`): pytest over `tools/`, and the cocotb RTL tests of every design-set protocol (UART now, others as they land), with sigrok installed as the second decoder.
