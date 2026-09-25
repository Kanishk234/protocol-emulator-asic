# Tiny FABulous (tt-fabulous-sky-26a): how it was built

Source: https://github.com/mole99/tt-fabulous-sky-26a at d4e2d9f (2026-05-04), tile library `mole99/fabulous-tiles` at 7999e5a. Read 2026-09-25.

## What it is
- 128 LUT4+FF logic cells (16 `LUT4x8_ha` tiles in an 8x2 block, vertical carry chain), 26 IOBUFs, 4 global buffers, SYS_RESET. The fabric grid is 10x4 FABulous tiles including IO and terminator tiles.
- Tiny Tapeout **8x4 tiles on SKY130** (die 1378 x 511 µm = 705K µm²). Clock target 10 ns.
- Pins look like a TT project (`clk`, `rst_n`, `ui`, `uo`, `uio`), so existing TT designs can be dropped onto the fabric.

## How it gets through Tiny Tapeout (answers the phase 0 question)
It is **hierarchical and hardened outside the template's `gds` job**:
1. **Tiles:** each tile type is hardened on its own with LibreLane's `FABulousTile` flow (from `mole99/librelane_plugin_fabulous`, via Nix). Tile config disables the resizer/repair steps (they would resize the switch-matrix buffers) and timing-driven placement; `SYNTH_STRATEGY: AREA 2`.
2. **Fabric:** the `FABulousFabric` flow stitches the hardened tiles by abutment (`FABULOUS_TILE_SPACING: 0`) into one macro and generates a **physical timing model** for nextpnr (`FABULOUS_TIMING_MODEL: PHYSICAL`, pips per corner). Antenna repair is off (no top-level cells); `GRT_ALLOW_CONGESTION` "unfortunately needed".
3. **Top:** a normal LibreLane Classic run places the fabric macro (`MACROS:` block) beside a small shell (`fabric_bitbang` + `fabric_config`), density 44 %, custom PDN config, `Odb.FABulousPower` to promote power pins.
4. **Submission:** the GDS/LEF are committed; CI uses TT's **`custom_gds`** action, which only packages the committed files. `info.yaml` lists a stubs file. Precheck is commented out in the push workflow and runs in a separate manual `gds-with-precheck` workflow.
5. User designs: Yosys + nextpnr **forks** at that time ("will be upstreamed"); FABulous 2.2 + OSS CAD Suite 2026-06-29 worked for us with upstream nextpnr on the stock demo fabric (`docs/reports/fab_demo.md`).

The tile library also has a `classic` set with `E_IHP_BRAM` / `E_IHP_SRAM` tiles and an `ihp-sg13*` section in the fabric config, so this flow has been pointed at IHP before.

## Configuration loading
- Frame-based config: 32 frame bits per row, up to 20 frames per column (same as the FABulous default we ran).
- Shell: `fabric_bitbang` samples `ui[1]` (data) on rising edges of `ui[0]` (sample) while `rst_n` is **low**; `fabric_config` looks for the sync word `0xFAB0FAB1`, then header words (frame select + column) and data words; a header with bit 20 set ends the load and sets `configured`. While loading, `SYS_RESET` holds the user design in reset.
- No checksum, no architecture-version tag, no output parking: outputs are wired straight to the fabric. Our shell adds these (ARCHITECTURE §3–4).

## Tests
cocotb: `tb/fabric_tb.py` (fabric alone) and `tb/top_tb.py` (whole chip), one test case per user design (counter, addition, passthrough, sys_reset, ...). Two modes: "emulation" (config bits pre-initialized from the bitstream, fast, one design per run) and real upload through the config port. GL mode uses the hardened netlist with the PDK cells.

## What we take
- The three-level flow (tile → fabric → top) and the `FABulousTile`/`FABulousFabric` LibreLane plugin.
- Emulation mode for fast protocol tests; full upload for pin-level and GL tests.
- Frame-based loading through a small FSM; our loader adds length, checksum and version.

## What we do differently / must decide
- **Integration:** either (a) Tiny FABulous's way (local hardening + `custom_gds`), which replaces the template's `gds` job and needs a DECISIONS entry and the organizers' OK, or (b) harden the fabric as a macro, commit it under `macro/`, and let the template's `gds` job integrate it with a `MACROS` block, the way the TRIPWIRE R3 spike integrated the IHP SRAM macro (precheck + `gl_test` passed there). (b) keeps the template jobs, precheck and `gl_test` untouched, so it is the first choice.
- Tile hardening needs OpenROAD/KLayout/Magic locally (Nix, as they do, or the LibreLane container).
