# Loader-inclusive mapped experiment — 2026-09-28

The management wrapper, pinned configuration loader and 14 row registers
now pass a **fully mapped control-path test** with both counter and LFSR
configuration images. The programmable fabric is still excluded.

Retained successful run: `build/warp-loader-cost.AXvDP6i0/`.
Both CRC modes pass 12,129 steps per image: 15 busy cancellation cases,
3,006 accepted words and exact address/payload checks at all 200 frame
writes. There are four successful mapped simulations in this run.

## Measured boundary and area

Same pinned CMOS5L typical 1.20 V / 25 C library, IHP PDK
`2bbec755dc67ca3db0261c3d6163e15735d66710`, Yosys 0.66+179.
Figures are direct sums of standard-cell Liberty areas, with each instance
counted once.

| Block | Word CRC cells / µm² | Byte CRC cells / µm² |
|---|---:|---:|
| Validator, guard, pacing, pad/reset muxes | 974 / 14,791.3290 | 883 / 13,878.0810 |
| Configuration loader and row registers | 2,617 / 54,751.2966 | 2,609 / 54,658.5732 |
| **Total measured** | **3,591 / 69,542.6256** | **3,492 / 68,536.6542** |

Byte CRC saves 1,005.9714 µm², or **1.45% of this larger boundary**.
The loader is approximately 79.8% of the byte-mode total. The same loader
source is mapped in both whole-design runs, but its cell mapping differs
slightly; use these measured totals rather than adding older isolated costs.

The loader boundary includes unmodified `eFPGA_Config`, `ConfigFSM`,
`Frame_Data_Reg`, `config_UART` and `bitbang` modules. Fourteen 32-bit
row registers account for 448 observable bits. A fixture connects them to
`wp_loader_boundary`, which synthesis reads as an empty black box.
It cannot know the fixture's constant user outputs or discard row data.

The loader hierarchy is deliberately retained for repeatable diagnostics.
Consequently, tied-inactive serial interfaces are **not assumed to be
optimized away across that boundary**. This is a reproducible reference
cost, not a minimum-cost word-only loader. It also uses the large
14-row reference dimensions, not a frozen tapeout fabric size.

Excluded: programmable fabric and configuration latches, column
frame-select decoders, RAM/DSP resources, future host/CDC logic, placement,
clock/control buffers and routing. The result is not a complete shell or
chip area estimate and establishes no frequency or physical fit.

## What is mapped and tested

Management logic **and loader/row registers** are mapped standard cells.
Only the fabric-side output stand-in remains behavioral. This improves on
the earlier management experiment, whose loader was RTL. No programmable
counter/LFSR circuit is executed here; those binary images supply loader
test data, while prior full-fabric RTL runs check user behavior.

The test keeps valid asserted across stalls, exercises begin/reset/abort
priorities during busy work, rejects early release and compares all captured
frame payloads. For mapped-loader tests, optimized private mux wires are
replaced by loader input-port observations; frame-register contents still
check actual downstream delivery. Diagnostic state is never forced.

The runner verifies exactly one loader instance and one empty fabric-side
black box, 448 distinct nonconstant row-data nets, and only supported
standard-cell types elsewhere. Yosys pre/post-mapping checks report zero
problems. TT Icarus 13 uses the pinned cell/UDP models. Existing unsupported
edge-sensitive `ifnone` model warnings remain; there is no SDF or timing
signoff. Reset phase/skew and subcycle hazards are not covered.

Twenty-three Python tests pass, including three new area-accounting checks.
The original RTL handshake mode is rechecked separately after fixture/TB
changes. Production RTL and the fabric generator remain unchanged.

## Accounting and testbench fixes

- `warp-loader-cost.BdPJ8rhn`: mapping passed, but GL elaboration failed
  because two private loader mux wires were optimized away. The test now
  observes mapped loader input ports plus captured frame payloads
  (ANISH-FAB-6).
- `warp-loader-cost.2wpvyEF9`: both mapped counter tests passed, but the
  first reporter added an inclusive parent area to its child area, counting
  the loader twice. Its erroneous output is retained as
  `summary-double-counted-do-not-use.json`. The corrected reporter computes
  direct cell-count × Liberty-area sums, then independently checks their sum
  against Yosys's inclusive top area. New regression tests reject inconsistent
  totals and pruned row bits (ANISH-FAB-7).
- `warp-loader-cost.AXvDP6i0`: final runner includes the corrected reporter,
  both images, both CRC modes and all source/hash snapshots. This is the
  authoritative end-to-end result.

## Reproduction and next step

Follow-up: the [word-only candidate](ANISH_WORD_ONLY_LOADER.md) tests direct
management ownership of configuration, preserving this all-frontend result
as a baseline and keeping the same row-bank size.

With the project venv and supported June 29 tools active:

```bash
bash scripts/fabric_loader_cost.sh build/fabric-reference-warp-reference.OBUfXfus
```

Before optimizing CRC further, measure the cost of a deliberate word-only
reference loader and examine sensitivity to row-register sizing. Do not
treat either as a production contract until the final fabric/host interface
is specified. Review transferable physical-flow fixes from updated main
without importing unrelated architecture work. Broader routing/DSP/RAM
isolation and physical validation remain open; no phase gate is closed.
