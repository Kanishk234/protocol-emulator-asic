# Compact shell: shared-word CRC experiment

Date: 2026-10-05. Decision: D-039, scratch exploration under D-037.
Frozen G1 remains the submission fallback. This experiment changes the shell,
with the same compact 5 × 3 macro, resource graph, configuration format,
20 ns clock target and 0.1 ns extra post-CTS hold margin.

The baseline CRC captures a second 32-bit copy of each configuration word and
shifts it during 32 processing cycles. The scratch helper instead selects each
bit from the shell's existing `cfg_word` register, in big-endian byte order and
LSB-first within each byte. Its input must remain stable until processing ends.
The shell's byte-assembly wire is unsuitable: it changes on the word-complete
edge. The initial integration found that mistake through a real SPI load
(BUGS #25); the corrected variant reads `cfg_word` beginning on the next edge.

## Functional checks

- Stable-word unit test: 40 deterministic streams containing zero, all-one,
  sync, byte-order-sensitive and randomized words; every cycle compared with
  the original CRC, final values compared with zlib. Includes mid-word clear
  and changes to the input while idle. PASS:
  `build/arch_explore/compact_edges/shared_crc_unit/results.xml`.
- Real 842-word SPI load, UART transmit/receive and STOP parking: PASS,
  `build/arch_explore/compact_edges/simulation_chip_shared_crc/results.xml`.
  The input-stability monitor checked all 26,944 processing cycles. This test
  uses the actual RTL fabric and CRC loader, without initializing user state.
- Baseline post-CTS mapped shell with RTL fabric: PASS, 23.70 s,
  `simulation_chip_mask_narrow_rows_mapped_shell/results.xml` under the same
  work directory. This checks the baseline, not a mapped shared-CRC shell.
- F2 BMC: PASS at the existing 84-cycle bound (591 s),
  `f2_shared_crc_bmc/status`. F2 cover reaches a checked load and RUN at step
  52 within the 60-cycle cover bound (`f2_shared_crc_cover/engine_0/trace0.vcd`).
  These checks cut the SPI receiver and retain its existing no-byte-while-CRC-
  busy assumption; they do not prove unbounded behavior or the SPI receiver.
- Scratch CRC Verilator `-Wall`, Verilog-2005 compilation, Python/shell syntax
  and whitespace checks pass.

## Matched physical screens

All paths below are under `build/arch_explore/compact_edges/`.
Both use masked unconsumed strobes, early region release, Metal1 routing,
21.12 µm middle-row fences, macro y=15.12 µm and the same physical macro.

| Metric | Baseline `chip_mask_narrow_rows` | Shared CRC `chip_shared_crc_physical` |
|---|---:|---:|
| Macro footprint (µm², rounded flow metric) | 758,031 | 758,031 |
| Pre-PDN mapped standard-cell area (µm²) | 46,753.5 | 44,443.7 |
| Pre-PDN standard-cell count | 2,796 | 2,647 |
| Post-CTS inserted hold buffers | 605 | 512 |
| GRT final total overflow | 67 | 93 |
| GRT estimated wirelength (µm) | 314,294 | 285,645 |

Sources: each directory's `runs/compact_local_pdn/final/metrics.json`;
`runs/compact_local_grt/09-openroad-resizertimingpostcts/openroad-resizertimingpostcts.log`;
`runs/compact_local_grt/11-openroad-globalrouting/openroad-globalrouting.log`.
Mapped area excludes later CTS/repair additions; estimated wirelength is a
global-routing result. Neither is final chip area/timing signoff.

The shared variant has lower mapped shell cost and fewer hold buffers but
higher overflow. The zero-overflow guard correctly stops its route driver
with exit 3. A separate bounded detailed-route screen completed under
`chip_shared_crc_physical/runs/shared_crc_drt_screen`: two optimization
iterations, with post-DRT antenna repair disabled for this diagnostic only.
It cannot establish an antenna/signoff pass. Its initial, iteration-1 and iteration-2 markers are 5,010, 3,108 and
2,652, versus the baseline's 6,424, 5,231 and 4,503 at the same stages.
This is an early routing improvement, not a completed physical result. A full
stock-check run is now active as `shared_crc_full_drt_20261005`, restarted
from the screen's preserved pre-DRT state with the original `config.json`.

The lead's full stock-check run `compact_narrow_rows_drt_20261005` finishes
its first DRT pass at 268 markers: 211 Metal2, 50 Metal3, seven Metal4, all
west of the macro. Its post-route antenna-repair/rerouting pass remains active.
No compact candidate has passed full-chip routing, timing, DRC/precheck or
native mapped-fabric protocol simulation.

## Reproduction

Activate the project venv and use the pinned tool PATH from `docs/VERSIONS.md`.
The compact macro and fresh strobe-usage trace must already exist.

```sh
source .venv/bin/activate
python spikes/compact_edges/verify_shared_crc.py \
  --out build/arch_explore/compact_edges/shared_crc_verify_fresh
```

The output directory must be fresh. The driver runs unit checks, stages an
isolated shell, runs F2 at the original bounds and runs SPI/UART/STOP with the
stability monitor. Its `--unit-only` branch has been exercised separately;
the complete checks above were run individually while the driver was added.

Physical screen, with the pinned EDA binaries available:

```sh
WARP_COMPACT_EDA_BIN=/nix/store/wjrb29pislfhs8lh1nmlg5kibhfqydl9-devshell-dir/bin \
WARP_COMPACT_CHIP_DIR=chip_shared_crc_fresh \
WARP_COMPACT_SHARED_CRC=1 WARP_COMPACT_MASK_STROBES=1 \
WARP_COMPACT_EARLY_RELEASE=1 WARP_COMPACT_MIN_LAYER=Metal1 \
WARP_LOCALIZE_ROWS=1 WARP_LOCALIZE_ROW_WIDTH=21120 \
bash spikes/compact_edges/route.sh
```

Keep the default overflow guard. Promoting the shell change requires a full
route/timing result and the complete end-to-end verification gates.
