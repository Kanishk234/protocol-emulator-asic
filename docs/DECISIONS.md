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

## D-016: Capacity go/no-go: GO for the specialized eFPGA (4 x 3 tiles + primitives)
- **Date:** 2026-09-25 · **Status:** Accepted (phase 1 decision point; revisit with the phase 3 measurements)
- **Evidence:** `docs/reports/capacity.md` (area model `tools/areamodel/`, tile hardening, profiling).
- **Decision:** continue with the pure specialized eFPGA, not the hybrid fallback. Planned G1: a 4 × 3 grid of LUT-size tiles next to a shell column; one tile slot holds primitives (2 loadable timers + 2 shift registers with bit count, settings in configuration bits); the host byte channel (holding register/FIFO, valid/ready, overrun) lives in the shell; I/O cells get input synchronizers, registered outputs and open-drain mode. That leaves 88 LUT4s.
- **Fit:** UART (~50 LUT4 with glue), SPI controller (~45) and I2C controller (~77) each fit 88. The I2C target (~220) does not; options in order: register-file primitive, smaller register map, showcase on the I2C controller. Running two protocols at once does not fit.
- **Primitive rules (D-002):** timer and shift register are used by 4 of 4 design-set protocols; host channel and I/O features are shell/I/O, not fabric blocks; the register file has one user so far and needs its own justification before it is built.
- **Alternatives:** hybrid (PIO-style sequencers + small fabric): not needed for 3 of 4; generic-only fabric: fits nothing (D-008).

## D-017: Tile power stripes on a global grid that the TT chip grid can land on
- **Date:** 2026-09-26 · **Status:** Accepted (spike; verified by the chip-level hardening)
- **Problem:** in TT's CMOS5L flow a user block has only vertical Metal4 power stripes (no TopMetal1), each ≥ 2.1 µm wide and running the full block height (precheck). A macro's Metal4 power pins must therefore be overlapped, same net, by those stripes; any chip stripe that crosses the macro anywhere else shorts to its wiring. Lessons from the TRIPWIRE R3 spike on `main` (IHP SRAM macro, 6 CI runs, `spikes/r3_sram/overlay/src/pdn_cfg.tcl`).
- **Decision:** the tiles' Metal4 power stripes are 2.1 µm wide at a pitch of **109.92 µm (half the LUT tile width, 219.84 = 2 × 109.92)**, with a tile-type offset so that, in the stitched fabric, every column's stripes sit on one global grid: fabric-local x = 20.00 + 109.92 k (VPWR) and + 4.1 (VGND). West-column tiles (W_IO4, NW_term, SW_term) use local offset 20.00; LUT-width tiles (LUT4x8_ha, N_term, S_IO2) and east-column tiles (E_IO4, NE_term, SE_term) use 61.28 (= 20.00 + 109.92 − 68.64, since every LUT-width column starts at 68.64 + 219.84 j). Tiles stacked in a column form continuous full-height power columns. The chip level uses the same pitch and width, offset to the macro's x position, with the R3 spike's pdn_cfg.tcl (it releases the macro during stripe generation and checks that every stripe crossing a macro lies inside same-net pins).
- **Why not per-tile 50 µm stripes:** tile widths (219.84, 68.64) are not multiples of 50, so no uniform chip grid can hit the stripes of every column.
- **Cost:** wider stripes take Metal4 routing tracks inside the tiles (2 × 2.1 µm per 109.92 µm, vs 2 × 1.0 per 50: about the same share, 3.8 % vs 4.0 %). IR drop with a 110 µm pitch: to check at chip level.

## D-018: Phase 1 spike top: 16-LUT fabric behind a minimal shell
- **Date:** 2026-09-26 · **Status:** Accepted (spike; replaced by the phase 2 shell)
- **Decision:** `tt_um_warp` = the fabric macro `warp_tiny` + `wp_fabric_cfg` (FABulous's bit-bang receiver and frame-configuration FSM, copied unmodified into `src/fabric_gen/`, + per-row frame registers and per-column frame selects). Pins: `ui[0]` RUN, `ui[1]`/`ui[2]` bit-bang config clock/data, `ui[3..6]` fabric inputs, `uo[0]` config active, `uo[2..5]` fabric outputs, `uio[0..7]` fabric bidirectional pins. Outputs and output enables are parked (0) unless RUN is high and no configuration session runs; the user design's reset and SYS_RESET are held during a session. Supersedes the D-006 pinout for this spike.
- **Reason:** phase 1 must harden a small fabric through the TT flow with live configuration (configuration latches driven from pins, not tied off). FABulous's own loader matches its bitstream format by construction.
- **Not yet:** the SPI-like host interface, loader checks (length, checksum, version) and host byte channels (ARCHITECTURE, phase 2).

## D-019: `src/config.json`: fabric macro placement and power grid
- **Date:** 2026-09-26 · **Status:** Accepted (spike; verified by the CI `gds` run and precheck)
- **Changes** (one entry per change, CLAUDE.md):
  1. `MACROS.warp_tiny`: instance `u_fabric` at (11.52, 7.56), orientation N; GDS/LEF from `macro/warp_tiny/`; netlists of the fabric and its 9 tile types. Location on the Metal2 (0.48) and Metal3 (0.42) track grids.
  2. `PDN_MACRO_CONNECTIONS`: `u_fabric VPWR VGND VPWR VGND`.
  3. `PDN_CFG`: `src/pdn_cfg.tcl`, the TRIPWIRE R3 spike's script (from `main`, unmodified below a WARP note). It releases the macro while stripes are built and fails the step unless every stripe over the macro lies inside same-net power pins and every macro pin is reached.
  4. `FP_PDN_VPITCH` 50 → **109.92**, `FP_PDN_VSPACING` **2.0**, `FP_PDN_VOFFSET` **20.64** (`FP_PDN_VWIDTH` stays 2.1): the chip stripes land on the fabric's power columns (D-017). The template marks these keys "do not change"; the R3 spike changed the same keys for the same reason and passed precheck.
- **Risk:** a 109.92 µm stripe pitch is wider than the template's 50 µm for the shell's standard cells (IR drop); PSM/IR report to be checked in the run.
- **Revision (2026-09-27, BUGS #9):** the first location (11.52, 7.56) put the fabric's pin-heavy west face (152 pins) and south face (67 pins) against the die edges; chip-level routing did not converge (run 36277723397). New location **(890.88, 113.40)**: east side of the die, centred vertically, west and south faces toward open core. x = 11.52 + 8 × 109.92 keeps the power-grid phase; `FP_PDN_V*` unchanged. Rule for any macro: check which faces carry its pins before choosing a location.
- **Revision 2 (2026-09-27, before the next run):** adopt the macro settings the R3 SRAM spike needed on CMOS5L (its `src/config.json` on `main`): `DRT_OPT_ITERS` **16** (a non-converging route fails in well under an hour instead of running to the 6 h limit, which cost ~4 h in run 36277723397); `MAGIC_MACRO_STD_CELL_SOURCE` `PDK`; `ERROR_ON_MAGIC_DRC` false (Magic's CMOS5L deck reports false errors inside macros; the precheck's KLayout DRC is sign-off); `ERROR_ON_ILLEGAL_OVERLAPS` false (chip stripes over the macro's Metal4 obstruction on its power columns); `MAGIC_EXT_ABSTRACT_CELLS` `["warp_tiny"]` (LVS treats the fabric as a black box). The macro's `nl` is now the port-only black box `src/warp_tiny.v` (not in `info.yaml` source_files), so synthesis and STA see only its pins; the fabric's full netlists stay in `macro/warp_tiny/` for simulation. Pre-run checks done: no TopMetal1/TopVia1 in the macro GDS (layers ≤ Metal4 + prBoundary), unique cell names, pin faces W 152 / S 67 / E 24 (Metal3/Metal2).
- **Revision 3 (2026-09-27, BUGS #11):** run 36293031051 passed `gds` and `gl_test` but failed the precheck pin check: the 38 µm channel east of the fabric got a short channel stripe from pdngen. Fabric moved to **x = 780.96** (11.52 + 7 × 109.92): the east channel (148 µm) holds a full grid stripe pair. Rule: beside a macro leave no channel or one that a full-height grid stripe pair crosses. Verified locally with TT's merged config before pushing: power grid (all LOOMPDN checks), 24 full-height stripes / 0 short, routing 0 overflow / 0 DRC.

## D-020: The template `fpga` workflow does not apply once the fabric is a hard macro
- **Date:** 2026-09-27 · **Status:** Accepted
- **Decision:** the template's manual `fpga` workflow (iCE40 build of `tt_um_warp`) is no longer run as a phase gate. Its last green run (36201219254) was on the placeholder design.
- **Reason:** since D-018 the top instantiates the hardened fabric macro `warp_tiny` as a black box (`src/warp_tiny.v`); an iCE40 build has no implementation for it. An FPGA prototype of WARP means synthesizing the generated fabric RTL (`macro/warp_tiny/warp_tiny.v` + tile RTL) onto a larger FPGA; that is phase 7 (optional), with its own build.
- **Workflow file:** unchanged (CLAUDE.md: never edit the template's jobs); it stays available for manual use.

## D-021: Shell v1 implementation clarifications to ARCHITECTURE §2–4
- **Date:** 2026-09-27 · **Status:** Accepted (ARCHITECTURE.md updated to match)
- **Decision:** the phase 2 shell (`src/wp_shell.v`) fixes points v1 left open or got wrong:
  1. **LOAD_BEGIN is also allowed in LOADING** (restarts the load). v1 allowed it only in UNCONFIGURED/LOADED/ERROR, so a host that lost a load midway (never sent LOAD_END) could only recover with the chip reset.
  2. **When load errors are reported:** a wrong ARCH_VERSION at LOAD_BEGIN (nothing is forwarded); a bad sync word or no words at all (BUGS #12), a LENGTH mismatch and a CRC mismatch at LOAD_END, checked in that order (0x13, 0x11, 0x12). A bad first word stops forwarding immediately; words beyond LENGTH are not forwarded. Reporting at LOAD_END means a host streaming LOAD_DATA never gets its error overwritten mid-stream.
  3. **ERROR_CODE priority:** a load error always replaces the code; a bad command (0x01) is recorded only when no error is pending. READ_STATUS clears it (and ch_overflow) once its ERROR_CODE byte has been clocked out.
  4. **Host timing** (from the two-flop synchronizers): SCK ≤ clk/8; CS_N falling to the first SCK rising edge ≥ 8 clk; CS_N high between transactions ≥ 4 clk. MISO changes right after each detected SCK rising edge.
  5. **Parking gate after the output registers:** `pin = reg & running`, so pins are 0 in the same cycle `running` drops (a register-only gate would leak one cycle). F1 is proved on this structure.
  6. **Channel FIFO depth 2** per direction (resolves the §7.3 OPEN item for now; revisit with the fabric's area). FIFOs are emptied whenever the design is not running.
  7. **FABulous's bit-bang receiver is removed** (`src/fabric_gen/bitbang.v`); the shell delivers words to `ConfigFSM` directly.
- **Reason:** found while writing the RTL, the host software (`tools/host/protocol.py`) and the tests; all are small and none changes the host command set or the STATUS layout.
- **Alternatives:** keep v1 as written (item 1 leaves a stuck state; item 3 loses the cause of an ERROR).
- **Cost:** none in area worth measuring; item 4 limits host SCK to 6.25 MHz at 50 MHz (a 3 K-word bitstream loads in ~16 ms).
- **Evidence:** `test/test.py` 12 pin-level tests (all pass locally 2026-09-27); `formal/f1_isolation.sby` (k-induction PASS 2026-09-27); `formal/f2_loader.sby`.

## D-022: Compile flow and real-bitstream tests for the current fabric
- **Date:** 2026-09-27 · **Status:** Accepted
- **Decision:**
  1. **`tools/compile/`** turns a user design + a pin map (YAML: user port → WARP pin, `.o/.oe/.i` for bidirectional pins; ARCHITECTURE §10, D-014) into a `.wbit` file and a JSON report (architecture version, tool versions, LC/IO/GBUF use, Fmax at the slow corner, pins, CRC, unmapped ports). Steps: a generated wrapper `warp_top` (one explicitly instantiated IOBUF per used IO cell, its IN/EN/OUT wired exactly as in the fabric, so value, enable and input are independent signals as the host channel needs, D-024; a GBUF on the clock; revised 2026-09-27 from tristate pads); Yosys `synth_fabulous` (pinned 0.66) with the tile library's primitives and with the IO pad mapping done explicitly (the pinned version's pad mapping targets the stock FABulous IO cell); nextpnr-generic `--uarch fabulous` on the fabric's pips/bels at the `nom_slow_1p08V_125C` corner, fixed seed; WARP's own bitgen (`tools/compile/bitgen.py`, BUGS #13).
  2. **Architecture identity** in `arch/warp_tiny/arch.yaml` (`arch_version` 0x0001, rows, macro path); `arch/warp_tiny/pins.csv` is the pin → IO BEL map; the fabric definition moved from `spikes/fabric_tiny/warp_tiny.csv` to `arch/warp_tiny/fabric.csv`. A unit test keeps arch.yaml, the shell's ARCH_VERSION, the host default and the committed bitstreams on one number.
  3. **`.wbit` format** (`tools/compile/bitfile.py`): magic, ARCH_VERSION, word count, CRC-32, then the words from the sync word on. The host library refuses a file whose ARCH_VERSION differs from READ_ID before sending anything (`checked_load_transactions`); the shell refuses it again at LOAD_BEGIN.
  4. **All 4 configuration rows are written**, the edge rows included (they hold the clock/reset IO and the GBUFs); FABulous 2.2's bitgen leaves them out by default.
  5. **Generated macro views for simulation:** the tile RTL FABulous generated in the tile build is exported with the macro (`macro/warp_tiny/rtl/`), next to the netlists; the fixed primitives come from the pinned tile library (`scripts/fetch_tiles.sh`). `test/Makefile` selects the fabric model: the black box (default, CI `test`), the RTL (`WARP_FABRIC=rtl`, CI `fabric`), or the macro's gate-level netlists (`GATES=yes`, CI `gl_test`).
  6. **Test bitstreams are committed** (`test/bitstreams/*.wbit` + their FASM and report), built by `scripts/build_test_bitstreams.sh` from `tools/compile/examples/`, because the template's `gl_test` cannot run the compile flow. The `fabric` workflow rebuilds them and fails if they differ (`--check`). They are build products of committed sources, not CI artifacts.
- **Reason:** PHASE2 needs the compile flow, a host that rejects foreign bitstreams, and `gl_test` with two real bitstreams; all of it has to work with the current 16-LUT fabric first so the G0/G1 fabric only changes `arch/` and `macro/`.
- **Alternatives:** FABulous's own `compile_design` (fixed project layout, the stock pad mapping, and bitgen with BUGS #13); running the compile flow inside `gl_test` (the template job cannot be edited).
- **Cost:** ~0.5 MB of generated tile RTL in `macro/warp_tiny/rtl/`; ~2.4 KB per test bitstream.
- **Evidence:** 2026-09-27 locally: `test/` 15/15 with `WARP_FABRIC=rtl` (counter4 and logic4 loaded over SPI and checked at the pins, one after the other in the same chip); `tools/compile` 9 pytest (bitgen equals fabulous_bit_gen word for word on all non-CLK features of both designs). counter4: 7/16 LCs, 162.6 MHz at the slow corner; logic4: 5/16 LCs (no register-to-register path).

## D-023: Simulating the fabric with real bitstreams: 4-state handling, and the gl_test fabric model
- **Date:** 2026-09-27 (revised the same day) · **Status:** Accepted
- **Context:** 4-state, zero-delay simulation of an FPGA fabric meets problems silicon does not have. Unused routing sits on default mux inputs and forms combinational loops, across tiles and inside them.
  (a) A loop that starts at X stays X, and the gate-level LUTs (synthesized gates, unlike the RTL's mux-tree LUT model) pass X on from inputs the configured function ignores: with the hardened macro's netlists, correctly loaded designs read X at their pins although all ~1,500 configuration latches held clean 0/1.
  (b) While one configuration is written over another, a half-written configuration can close a loop that rings; the simulator never advances past it.
  (c) Even with a complete configuration, a gate-level LUT's static hazard on an input its function ignores, fed back to that input through a default-routed loop, glitches forever in zero-delay simulation (seen with logic4 loaded after counter4 once the compile flow's IO wiring changed, 2026-09-27).
  In silicon a loop holds some definite 0/1 (a), a ring during a load (b) stops when the load completes (the design is held in reset and every pin parked meanwhile), and the gates have delay (c).
- **Decision:**
  1. **`gl_test` simulates the shell at gate level and the fabric macro from the RTL it was hardened from** (`test/Makefile`: `GATES=yes` defaults to `WARP_FABRIC=rtl`; the macro's generated RTL in `macro/<fabric>/`, primitives from the pinned tile library via `scripts/fetch_tiles.sh`). TT's check is then what it is for: our synthesized, hardened logic with real bitstreams through the real host interface. The macro's gate-level netlist can still be simulated locally (`WARP_FABRIC=gl`); CI run 36342012141 did so, 16/16, before the IO-wiring change.
  2. **Testbench modelling of the loops** (`tb.v` includes `test/fabric_settle_{rtl,gl}.vh`, generated by `scripts/gen_fabric_settle.py`): `tb.hold_x` holds the fabric's nets at X for the whole of a load (no ring can form; the configuration path, found by tracing the tile netlists, is excluded, and latches and flip-flops keep their state underneath the force); after the load `tb.settle_routing` pulses the inter-tile routing wires to 0 for 1 ns so each loop settles to a definite value, with the design still in reset. This is simulation modelling in the testbench; the tests use top-level ports only.
- **Gap and plan:** the macro's gate-level netlist is no longer exercised by CI with real bitstreams. It was synthesized by the tile flow from the same RTL, and its one CI run passed, but nothing checks the two are equivalent. Plan (phase 2/3): a per-tile-type formal equivalence check of each tile's netlist against its RTL (EQY/Yosys), which covers every configuration rather than a few bitstreams. In the OVERVIEW risk register.
- **Risk noted (silicon):** during reconfiguration a partially written configuration can form a ring oscillator for the duration of the load (b); nothing leaves the chip (pins parked, F1), it costs switching power only while loading. In the OVERVIEW risk register.
- **Alternatives:** unit-delay gate-level simulation (would need SDF annotation of the PDK cell models in the template's gl_test); loading an all-zero configuration between designs (the zero load itself passes through half-written configurations); forcing internal nets to 0 (leaves gates inconsistent with their inputs; hangs).
- **Evidence (local, 2026-09-27):** `scripts/gl_local.sh` (Yosys gate-level shell + fabric RTL + real bitstreams) 16/16; `WARP_FABRIC=rtl` 16/16; black box 13 + 3 skipped.

## D-024: G0 fabric layout and where the host channel enters the fabric
- **Date:** 2026-09-27 · **Status:** Accepted (G0 stitched 1016.64 × 669.06 µm; chip placement D-025)
- **Decision:** `arch/warp_g0/fabric.csv`: 4 × 3 `LUT4x8_ha` (96 LUT4+FF) framed by `W_IO4` (west), `E_IO4` (east), `N_IO` (north) and `S_IO2` (south) columns/rows plus corner terms. All tile types are already hardened on CMOS5L (N_IO added 2026-09-27: 219.84 × 56.7 µm like N_term, 0 DRC, 0 antenna). IO cells (BELs): west 12, east 12, north 4, south 8 = 36. Allocation:
  - user pins (ARCHITECTURE §1): FAB_IO0..7 on 8 west cells; FAB_IN0..4 and FAB_OUT0..5 on 11 east cells; clock and user reset on 2 south cells (as in warp_tiny);
  - host channel (§7.3): 11 signals into the fabric (h_wdata[7:0], h_wlast, h_wvalid, h_rready) and 19 out (h_wready, h_rdata[7:0], h_rvalid, h_status[7:0], h_attention). Each IO cell gives the fabric one input (its pad side) and two outputs (value and enable, both plain wires into the shell), so the 15 spare cells (4 west, 1 east, 4 north, 6 south) carry 15 in / 30 out: enough without narrowing h_status (resolves the §7.3 OPEN item).
- **Reason:** no new tile type (a 4-cell north IO tile would need its own definition, DECISIONS entry and hardening risk); keeps the §7.3 interface whole.
- **Alternatives:** a new N_IO4 tile; narrowing h_status to fit fewer cells; host channel only on the north edge (4 cells: too few).
- **Cost:** the enable output of a host-channel cell is used as a data bit, so the compile flow's pin map must name both roles (already supported: `.o`/`.oe`); the shell's host-channel wires spread over three fabric edges (chip-level routing, to watch in the 6x4 hardening).
- **Evidence:** pending the G0 stitch (`FABRIC=warp_g0 spikes/fabric_tiny/run.sh`) and the design-set synthesis check in `docs/reports/capacity.md` (only the SPI controller comes close to 96 LCs; G1 needs the primitives, D-008).

## D-025: G0 in the 6x4 chip: placement, placement density, routing derate, per-column frame decode
- **Date:** 2026-09-27 · **Status:** Accepted (evidence: local pre-flight; CI hardening 36353540402 on e5b1f98: `gds` 45.8 min, precheck pass, `gl_test` 17/17, routing DRC/LVS/antenna 0, setup WS +10.63 ns, hold WS +0.121 ns)
- **Context:** the 6x4 CMOS5L chip routes only on Metal2–Metal4, and **Metal3 is the only horizontal layer**. The G0 macro (1016.64 × 669.06 µm) fills the core's height except 34 µm, and nothing routes over it. All TT pins are in the top-left corner (x 30–191 µm). So every wire between the west (shell, TT pins) and the fabric's far faces shares a few Metal3 tracks in the strips above and below the fabric. The first placement's global routing had 9,290 overflows, almost all *over* the macro: the router pushed ~118 crossing nets through it.
- **Decision (`src/config.json`, `src/wp_frame_select.v`):**
  1. Macro at **(121.44, 30.24)**: x on the power-grid phase (11.52 + 109.92 k, D-017) with a 148 µm east channel that holds a full stripe pair (BUGS #11; x = 231.36 would leave 38 µm with none); y leaves 26.46 µm below (frame-strobe logic) and 7.56 µm above.
  2. **No standard cells in the east channel** (`FP_OBSTRUCTIONS` x ≥ 1148.16): the shell stays west, so shell-internal wires do not cross the fabric.
  3. **`PL_TARGET_DENSITY_PCT` 75** (default 60): the shell packs into the west column instead of spilling into the strips around the macro, where every cell adds crossing wires.
  4. **`GRT_ADJUSTMENT` 0.15** (default 0.3): global routing reserves less of each track for detailed routing; the strips are the scarce resource and the design is small (25 % of tracks used).
  5. **Per-column frame decode:** FABulous's `Frame_Select` needs all 20 one-hot frame bits at every column; `wp_frame_select` takes a 5-bit frame number and decodes it under its column, so 11 wires run along the fabric instead of 26. Same behaviour for every bitstream with one frame per header (all the compile flow writes).
- **Measured (global-routing overflow, local LibreLane):** first placement 9,290 → y moved up 8,210 → east channel blocked 4,734 → per-column decode 4,153 → **density 75 % + derate 0.15: 23**.
- **Alternatives:** no IO on the fabric's east face (all user pins on west/north/south cells: needs an east edge tile without IO, a rebuilt macro, and one fewer fabric input; kept as the fallback if detailed routing fails); a larger TT tile (cost; the crossing problem stays).
- **Evidence:** local `scripts/preflight.sh` 2026-09-27 (Nix LibreLane 3.0.0, TT merged config): global-routing overflow 23, **detailed routing 0 violations, 0 antenna**, 22 vertical Metal4 power stripes all full height. G0 RTL suite 17/17 with the per-column decode. CI hardening: to be recorded here.

## D-026: G1 hard primitives: timer and shift register (D-002 entry)
- **Date:** 2026-09-27 · **Status:** Accepted 2026-09-28 (ARCHITECTURE §8's method complete: built, proven (F4), Yosys mapping, nextpnr placement, bitstream configuration, and compiled user designs using both blocks loaded through the host interface on the hardened chip: `test_prims`, `test_uart` in CI `gl_test` 36367067731)
- **Decision:** G1 adds two general primitives (ARCHITECTURE §8, cycle-exact spec v2), placed in a primitive tile that takes one LUT-tile slot of G0:
  - **`wp_timer`** (`arch/prims/wp_timer.v`): loadable 16-bit down-counter with terminal count; config RELOAD[15:0], ONESHOT; ports rst, load, half, en → tc.
  - **`wp_shift`** (`arch/prims/wp_shift.v`): 8-bit shift register with a step count; config LEN[3:0], MSB_FIRST; ports rst, load, step, sin, d[7:0] → sout, done, q[7:0].
  - Planned tile content: 2 timers + 2 shift registers (32 block inputs, like a LUT tile's 32 LUT inputs; 22 outputs spread over the tile's 32 output muxes), clocked by the tile's global clock. **Protocol-agnostic:** no protocol state machine, framing or bus behaviour is in hardware; each block is a counter or a shifter any protocol can use.
- **Profiling data behind it** (`docs/reports/profiling.md`, ranks 1–2): counters are the largest function (23 % of the design set's 648 LUT4s): upper-bound saving 150 LUTs + 51 FFs (UART 63, I2C controller 48, SPI 24, I2C target 15); shift registers with bit counts 17 %: 111 LUTs + 56 FFs. The real compile flow confirms plain G0 fits none of the four (`docs/reports/g0_results.md`: SPI 95, UART 127, I2C controller 160, I2C target 205 LCs of 96).
- **Protocols that benefit:** timer: UART (2), SPI controller (1), I2C controller (1), and the I2C target's timeout if added; shift register: all four (UART TX/RX, SPI MOSI/MISO, I2C data both ways).
- **Area (measured 2026-09-27):** the primitive tile `PRIM2T2S` (`arch/tiles/PRIM2T2S`, generated by `scripts/gen_prim_tile.py` from the LUT tile) hardened on CMOS5L in the LUT tile's footprint, 219.84 × 185.22 µm, with 35,094 µm² of standard cells (92.3 % utilisation) against the LUT tile's 36,047 µm² (94.8 %): **0.97 × a LUT tile**; routing 0 DRC, KLayout DRC 0, antenna 0. Phase 1's estimate was 1.07 ×; before: estimated 1.07 × a LUT tile per primitive tile (`capacity.md`: 2,751 µm² per timer and 1,538 µm² per shift register including configuration bits, against ~740 µm² per LUT4 without routing); measured when the tile is hardened. **Cost to protocols that don't use it:** the slot's 8 LUT4s (G1 = 88 LUT4 + 2 timers + 2 shift registers, against G0's 96); a design using neither block loses 8 % of its logic capacity.
- **Verification so far:** F4 (`formal/f4_prims.sby`): each block equals a spec model written from ARCHITECTURE §8 for all configurations and inputs, unbounded (k-induction), 2026-09-27; `test_internal/test_prims.py`: RTL against the independent Python reference model (`tools/refmodels/prims.py`, 28 property tests), random configurations and stimulus, cycle by cycle.
- **Tools (2026-09-27):** users instantiate `WP_TIMER #(.RELOAD, .ONESHOT)` / `WP_SHIFT #(.LEN, .MSB_FIRST)` (`tools/compile/prims/warp_prims.v`); Yosys keeps them as the BEL cells (`warp_plib.v`) with one parameter per configuration bit, nextpnr places them on `PRIM2T2S`, and the bitstream sets the bits (checked on `tools/compile/examples/prims2`). The G1 fabric (`arch/warp_g1`, `macro/warp_g1`) has G0's size and ports.
- **Measured benefit (`docs/reports/g1_results.md`, local):** with the same sources and flow, G1 places UART 29, SPI controller 47 and I2C controller 70 of 88 LCs; G0 places only the SPI controller (86 of 96; UART 124, I2C controller 115). The I2C target fits neither (205).
- **Still to do before Accepted (ARCHITECTURE §8's method):** G1 in the chip (one hardening), and a compiled user design using each block after loading through the host interface (`test/test_bitstream.py`); the full equal-area comparison against G0 (D-004) in phase 3.

## D-027: G1 replaces G0 in the chip
- **Date:** 2026-09-27 · **Status:** Accepted (CI 36367067731 on d6f5dcd: `gds` 43.6 min, precheck pass, `gl_test` 19/19, routing DRC 0, LVS/antenna/Magic 0, setup WS +10.73 ns, hold WS +0.143 ns)
- **Local pre-flight (2026-09-27, LibreLane 3.0.0 Nix):** global-routing overflow 20 (G0: 23), power stripes 22/22 full height, but **21 detailed-routing violations**, all on `clk`: its route from the TT clock pin drops through the 7.6 µm strip above the fabric onto the macro's Metal4 blockage near its top-left corner (x ≈ 137.7 µm, y 653–699 µm). The G1 LEF is byte-identical to G0's apart from the name, and G0 routed with 0 violations in CI (LibreLane 3.1.0.dev3) with the same floorplan; the netlist differs only in the architecture-version constant. So this is placement noise at a known tight spot (D-025), not G1's macro. CI hardening decides; if it fails there, the next hardening moves the macro down one row (7.6 → 11.4 µm above it) as its one change.
- **Context:** G0 is hardened and green in CI (36353540402) but runs only the SPI controller of the design set; G1 (D-026) runs UART, SPI controller and I2C controller in the same macro size (`docs/reports/g1_results.md`). The phase 2 fallback submission needs protocols that run.
- **Decision:** `arch/CURRENT` = `warp_g1`, ARCH_VERSION 0x0003 (shell parameter, `tools/host/protocol.py`, `arch/warp_g1/arch.yaml`). `src/config.json` changes only the macro's name and files (`MACROS.warp_g1`: `macro/warp_g1/warp_g1.{gds,lef}`, black box `src/warp_g1.v` generated from the macro RTL; `MAGIC_EXT_ABSTRACT_CELLS`). Location, orientation, obstruction, density and routing derate stay as D-025: the G1 macro has G0's size (1016.64 × 669.06 µm) and identical ports, and its pin placement comes from the same fabric flow. This is the one hardware change of the next hardening.
- **Tests:** the chip suite's bitstreams are rebuilt for G1 (`scripts/build_test_bitstreams.sh`), plus `test_prims` (both block types configured by a real bitstream) and `test_uart` (the design-set UART on the primitives, through the host interface). The RTL fabric model includes `arch/prims/*.v`.
- **Consequence:** G0 stays in `arch/warp_g0` and `macro/warp_g0` as the equal-area baseline (D-004); its bitstreams are no longer loadable on the chip (architecture check).

## D-028: Compile flow uses nextpnr 0.11.1 for hard-primitive timing
- **Date:** 2026-09-27 · **Status:** Accepted
- **Context:** BUGS #17: the pinned nextpnr (0.10-82, OSS CAD Suite 2026-06-29) gives no timing arcs to custom BELs, so every path through `wp_timer`/`wp_shift` was untimed and G1 Fmax figures were optimistic. Upstream nextpnr's FABulous back end reads per-BEL-type arcs from `.FABulous/placement_estimate.txt` since 2026-07.
- **Decision:** the compile flow (`tools/compile`) takes nextpnr-generic 0.11.1-34-gc4fbb55a from OSS CAD Suite 2026-09-27 (`scripts/fetch_nextpnr.sh`, `~/.cache/warp/ocs-2026-09-27`; `WARP_NEXTPNR` overrides); Yosys and FABulous stay on the 2026-06-29 suite (FABulous 2.2 pins it; newer Yosys breaks `synth_fabulous`, docs/VERSIONS.md). The primitives' arcs come from OpenSTA (`tools/timing/`) into `macro/<fabric>/fabulous/.FABulous/placement_estimate.txt` (`scripts/gen_prim_timing.py`, generated; margins clock-to-out ×1.5, setup/combinational ×3.0, set by a cross-check against STA of the hardened tile, `tools/timing/tile_check.sh`). A fabric with primitives and no arcs is a compile error.
- **Check:** on the G1 fabric files without the new file, 0.11.1 produces byte-identical FASM and the same Fmax as 0.10-82 for uart16, spi8, i2c8. With the arcs (final margins): UART 90.7 MHz, SPI controller 78.0, I2C controller 53.0 (slow corner).
- **Cost:** a second tool download in CI (`fabric`, cached) and locally; nextpnr warns that `bel.v3.txt` is absent (only needed for per-instance arcs; not used).

## D-029: Phase 2 decision point: G1 is a valid fallback submission
- **Date:** 2026-09-28 · **Status:** Accepted
- **Question (OVERVIEW decision point, end of phase 2):** is the chip as it stands (shell + G1) a submission that meets the competition's required protocols if later phases slip?
- **Evidence:** G1 hardened in the 6x4 chip with precheck and `gl_test` 19/19 (CI 36367067731); UART, SPI controller and I2C controller compile onto it (29, 47, 70 of 88 LCs; nextpnr slow-corner estimates 90.7, 78.0, 53.0 MHz with primitive arcs, D-028) and pass pin-level tests through the host interface on the fabric RTL (21/21 locally; the SPI and I2C chip tests reach CI `gl_test` with the next push); F1 (unbounded), F2 (BMC 84), F4 (unbounded) pass (`docs/reports/formal.md`).
- **Decision:** yes, G1 is the fallback: UART, SPI and I2C (controller side) run on it.
- **What is missing for a stronger submission:** the I2C target (does not fit, `docs/reports/g1_results.md`); an SPI target design; protocol rates on the chip clock (only nextpnr estimates, no STA cross-check yet); the phase 3 equal-area comparison of variants; held-out evaluation (phase 4); any hardware test.

## D-030: Phase 3 candidate 1: timer with a registered terminal count (measured; not kept alone)
- **Date:** 2026-09-28 · **Status:** Measured, not kept on its own (parked: `build/c1/parked/`, not committed)
- **Need (data):** `docs/reports/g1_limits.md`: every design-set critical path goes through a primitive; the timer's clock → `tc` arc (2.98 ns, a 16-bit compare after the counter) was the largest primitive arc.
- **Change:** `wp_timer` keeps a flop `zero` equal to (count == 0), computed a cycle ahead from (count == 1) and the static configuration; `tc` = en & armed & zero. Same ports and cycle-exact behaviour: F4 re-proved unbounded (k-induction) with the invariant zero == (count == 0) asserted; white-box tests against the Python model pass. Protocols that benefit: every timer user (UART, SPI, I2C controller). Cost to non-users: none (same tile, same ports).
- **Measured:** standalone slow corner: clock → `tc` 2.98 → 0.88 ns; input setup 1.40 → 1.47 ns; area 2,428 → 2,416 µm² (no cost). With the arcs in the compile flow (same margins): UART 90.7 → 100.5 MHz, SPI controller 78.0 → 76.2, I2C controller 53.0 → 52.1. The worst design is limited by paths **into** the timer (its input setup, ×3.0 after the hardened-tile check), which this change does not touch.
- **Decision:** not kept alone: the design set's minimum Fmax (I2C controller) does not improve. The real limit is physical: the primitive tile is hardened with the tile library's settings, which disable the resizer and design repair (`arch/tiles/PRIM2T2S/config.yaml`), so a NOR inside the timer drives 33 loads unbuffered (2.90 ns, `tools/timing/README.md`). Next candidate (D-031): harden the primitive tile with buffering/repair of the primitives' internal nets, then re-measure; this change is re-evaluated together with it.

## D-031: Phase 3 candidate 2: primitive tile hardened with design repair (measured; not feasible)
- **Date:** 2026-09-28 · **Status:** Not feasible at the tile's size; not kept
- **Need (data):** D-030: the design set's slowest path ends inside the timer, after an unbuffered NOR driving 33 loads (2.90 ns) in the hardened `PRIM2T2S`; the tile library's flow has no design-repair step (its config also nulls it: "don't resize the buffers").
- **Tried (local tile runs, 2026-09-28):** (1) removing the library's null for RepairDesign: no effect (the FABulousTile flow has no such step); (2) inserting `OpenROAD.RepairDesignPostGPL` after `OpenROAD.AddBuffers` (the tile driver in `build/tile_cmos5l` extended to apply step insertions): repair fixed 106 fanout violations and 1 slew violation but added 153 output-port buffers and 58 tie cells, and detailed placement failed; (3) the same without output-port buffers and tie separation: still 106 fanout violations (the tile SDC's max fanout 10), and detailed placement failed again.
- **Result:** the primitive tile is 92.3 % utilised in the LUT tile's footprint (D-026); there is no room for the buffering the timer's control nets would need. Keeping the footprint (so the fabric grid and macro stay the same) rules this out; a larger primitive tile would change the fabric and the equal-area comparison.
- **Decision:** not kept; the tile config is restored. G1 keeps its timing model (`tools/timing/README.md`): every design-set protocol still estimates above 50 MHz (I2C controller 53.0). D-030 stays parked. Options left if timing becomes binding (e.g. a held-out protocol in phase 4): restructure the timer's control logic in RTL to lower its fanout, or a primitive tile with one timer fewer.

## D-032: Organizers: an eFPGA entry is accepted; the software side is required
- **Date:** 2026-09-28 · **Status:** Accepted (requirement)
- **Source:** reply from the competition organizers to Kanishk's email (2026-09-28; paraphrased): an eFPGA entry is fine; the blog describes a CPU-style approach only because it is the most common; what counts is that the chip can be reprogrammed after fabrication to support new protocols, within its timing and I/O limits. The main extra thing expected is **the software side**: (1) the flow from a protocol description to a bitstream, (2) how the bitstream gets loaded onto the chip, and (3) working examples for the supported protocols (UART, SPI and I2C to start); the equivalent of a CPU entry's assembler and example programs.
- **Where WARP stands:** (1) `tools/compile` (Verilog + pin map → `.wbit` with report, D-022/D-028); (2) the shell's checked SPI loader (ARCHITECTURE §3, F2) and `tools/host/protocol.py` (builds and checks every host transaction), exercised through the chip's pins in `gl_test`; **missing: a loader that runs on real hardware** (the Tiny Tapeout demo board drives the chip from its RP2040, MicroPython); (3) `protocols/uart`, `spi_ctrl`, `i2c_ctrl` compile onto the chip's fabric and pass through the host interface on the hardened netlist (`gl_test` 21/21).
- **Plan changes:** phase 4 adds "loader for the Tiny Tapeout demo board" and "end-to-end examples (source → bitstream → load → run) for UART, SPI and I2C"; phase 5's user guide (`docs/USER_GUIDE.md`) covers exactly the three items above. Held back from claims until tested on hardware: anything the board loader has not done on a real board (CLAIMS rules; no hardware yet).

## D-033: Final architecture: G1 (phase 3)
- **Date:** 2026-09-28 · **Status:** Accepted (pending the `hw-freeze` tag by the user)
- **Data:** `docs/reports/architecture_comparison.md` (equal area): G1 places 3 of the 4 design-set protocols against G0's 1, all three above 50 MHz in the timing model; the measured candidates did not improve the design set (D-030: worst design 53.0 → 52.1 MHz; D-031: not feasible), and the unbuilt ones fail on the data (`docs/reports/g1_limits.md`): LUT tiles with two control sets (3–7 control sets per design vs 11 LUT tiles: not binding), a second primitive tile (no design-set user, costs 8 LUT4s), a register-file tile (the I2C target would still need ~105–110 LCs of 80).
- **Decision:** the final architecture is **G1** as hardened at 3047dea (CI 36383587262: precheck pass, setup WS +12.48 ns at 50 MHz, `gl_test` 21/21), including the BUGS #18 reset fix. No further fabric changes; after `hw-freeze`, hardware changes only for logged bugs.
- **Not reached:** the I2C target does not fit (169 LCs of 88). It stays a design-set protocol that the final architecture does not run; I2C is supported through the I2C controller.

## D-034: Phase 3 candidate 3: register file for the I2C target (measured; does not make it fit)
- **Date:** 2026-09-28 · **Status:** Measured, not kept
- **Context:** the user chose to keep the hardware open to look for a way to fit the I2C target (the one design-set protocol G1 does not run).
- **Measured:** the tile library's `RAM_32x4_2R_1W` (32 × 4, two read ports, one write port; two side by side for 8-bit registers) holding the I2C target's registers (bus read on one port, host read on the other, shared write port; experimental source `build/c3/i2c_target_rf.v`, not a protocol file), synthesized on G1's cells: **4 registers 169 → 123 LCs, 2 registers 123 → 110 LCs**. A tile holding the register file would take a LUT slot (80 LUT4 left).
- **Why it still does not fit:** after the register map, the design is ~110–120 LCs of bus state machine, host command decoding, status and port logic, about 1.5 × the fabric. Yosys's generic LUT4 mapping agrees (D-033). The fabric cannot grow in the 6x4 chip: the macro already spans the core's width beside the shell column, and a fifth tile column (219.84 µm) does not fit.
- **Decision:** not kept. No fabric change we can build at 6x4 makes the I2C target fit. Remaining options are on the design side (a much smaller I2C target: fewer features, not fewer registers) or scope (document the I2C target as not supported; I2C is supported through the I2C controller). The user decides (hardware kept open).

## D-035: I2C target not supported on the chip; hardware freeze on G1
- **Date:** 2026-09-28 · **Status:** Accepted (decided by the user)
- **Context:** D-033/D-034: no fabric change buildable at 6x4 makes the I2C target fit (169 LCs of 88; 110–123 even with a register-file tile). The phase 3 exit item "all design-set protocols recompiled and passing on the final architecture" cannot pass as written.
- **Decision:** the I2C target is **not supported** on this chip and leaves the set of protocols the chip is claimed to run; it stays in `protocols/i2c_target` as a tested RTL design (its tests still run in CI) with the fit result documented. I2C is supported through the I2C controller; the organizers' list (UART, SPI, I2C, D-032) is covered. The phase 3 exit item is amended to "every supported design-set protocol" (UART, SPI controller, I2C controller). The hardware freezes on G1 as hardened at 3047dea (D-033); the user tags `hw-freeze`.
- **Consequence:** no claim of I2C target support (`docs/CLAIMS.md`); `protocols/i2c_target/README.md` says it does not fit.

## D-036: Phase 4 showcase: one chip, six protocols, switched at run time
- **Date:** 2026-09-28 · **Status:** Accepted
- **Context:** the planned showcase (I2C target with fault injection, PHASE4) cannot run: the I2C target does not fit the frozen chip (D-035). The optional concurrency demo does not fit either: every pair of the protocols that run exceeds the fabric (88 LCs) or its 2 timers + 2 shift registers (UART alone uses all four blocks; SPI + SWD need 91 LCs).
- **Decision:** the showcase is the project's core claim itself: a single simulated chip, never reset, loads six bitstreams one after another through the host interface (UART, SPI controller, I2C controller, WS2812, 1-Wire, SWD) and each one works against its independent reference device on the pins (`test/test_bitstream.py::test_showcase_protocol_switching`). Three of the six are held-out protocols the architecture was never tuned for.
- **Consequence:** PHASE4's showcase items are amended accordingly; the fault-injection idea is covered by the mutation campaign (`docs/reports/mutation.md`).

## D-037: Reopen architecture exploration against broader communication workloads
- **Date:** 2026-09-28 · **Status:** Accepted (user direction; exploration only)
- **Context:** G1 is the measured baseline: an 88-LUT4 fabric with two timers and two shift registers. It runs six protocol personalities sequentially, while the G1/G0 comparison measured fit and timing rather than simultaneous independent links. The user wants the eFPGA architecture itself made as capable and distinctive as possible for general communication, without protocol-specific hard blocks.
- **Decision:** reopen phase 3 architecture exploration. Preserve G1 and `hw-freeze` as the known-good baseline; the tag records the previous candidate and does not prohibit a separately versioned successor. Do not change silicon RTL, `arch/`, `macro/`, `info.yaml`, or the architecture contract until candidate designs have a written spec and comparative measurements.
- **Method:** compare alternatives at the same total chip area and clock target (D-004), using a workload matrix that includes supported roles, throughput, response latency/jitter, concurrent operation, host servicing, routed fit, and timing. Keep protocol behavior in programs or user fabric; hard resources must remain reusable across unrelated communication tasks (D-002). The already-revealed held-out set is training data for this revision; choose and seal a fresh held-out set before tuning the successor.
- **Candidates to screen:** (1) G1 unchanged baseline; (2) FABulous-specific configuration/interface remapping and a smaller 5 × 3-grid tile; (3) shared-program, independently paced event lanes connected to the LUT fabric; (4) a small pure sequencer fabric as a control architecture; (5) rebalanced routing graphs; (6) generic CRC/LFSR datapaths. `docs/reports/architecture_screen.md` and `docs/reports/architecture_research.md` contain the initial measurements and research; none selects a successor. Any sequencers expose generic pin wait/read/write, relative or absolute timing, shift/data movement, capture, and bounded queues, never UART/SPI/I2C opcodes.
- **Acceptance:** a successor is preferred only if exact-area, routable results improve a stated objective across the training suite and do not regress the sealed suite beyond an explicit tradeoff. Demonstrate at least one useful simultaneous communication/monitoring behavior, not only sequential reconfiguration. Run full chip hardening and end-to-end tests before replacing G1 as the submission candidate.
- **Evidence and limits:** `docs/design/ARCHITECTURE_EXPLORATION.md`; first shared-image two-lane RTL and 8-/16-word RAM/configuration-image area screen are in `spikes/event_lanes/` and `docs/reports/architecture_screen.md` (simulation and SG13G2 synthesis only; not routed or integrated). Baseline evidence remains `docs/reports/architecture_comparison.md`, `g1_results.md`, `g1_limits.md`, and `heldout_results.md`. This decision authorizes design-space exploration, not selection of a new architecture.
