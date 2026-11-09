# Official toolchain inspection — 2026-11-09

This is a source/package inspection, not physical qualification. No official workflow, main hardware, config or info.yaml was changed, and no new hardening was launched.

## Retrieved revisions

- Template main: `4b1204ab387b5ab94db1d57067051d8d89a2f83c`.
- GDS action ttihp27a: `e7a50f8f46f9f8df4b2c9935bfeb1cbc6b6ae4f6`.
- Support tools main: `9d13ff3e3e6202090740110438c6a10c1d62ca0f`.
- CMOS5L default LibreLane: `3.1.0.dev4`, versus our controlled screen's `3.1.0.dev3`.
- LibreLane wheel's IHP family PDK hash: `89d42ee6d2fd9b50b86a1aada6fee6673c3e6008`, versus our manually installed `2bbec755dc67ca3db0261c3d6163e15735d66710`.

Snapshots and downloaded wheel are under `/tmp/tripwire-official-nov9/`. Dependencies for the local generator probe were placed there too; project venv packages were not changed. Upstream moving refs must be resolved again when launching and the actual engine/container/PDK identities recorded.

## Findings

The [official template jobs](https://github.com/TinyTapeout/ttihp-verilog-template/blob/4b1204ab387b5ab94db1d57067051d8d89a2f83c/.github/workflows/gds.yaml) select ttihp27a for GDS, precheck, GL and viewer. Its [action](https://github.com/TinyTapeout/tt-gds-action/blob/e7a50f8f46f9f8df4b2c9935bfeb1cbc6b6ae4f6/action.yml) defaults to support-tools main, uses `--pdk ihp-sg13cmos5l`, and relies on LibreLane/Ciel PDK management instead of our older separate installer/manual-PDK path. The wheel requires Ciel >=3.2,<4. This is more than a branch-name change.

The [tile table](https://github.com/TinyTapeout/tt-support-tools/blob/9d13ff3e3e6202090740110438c6a10c1d62ca0f/tech/ihp-sg13cmos5l/tile_sizes.yaml) specifies:

| Geometry | Die size in micrometres |
|---|---|
| 6x4 | 1289.28 by 710.64 |
| 8x4 | 1724.16 by 710.64 |

The official 8x4 DEF exists and agrees with the table. Actual die area increases about 33.7%; this is not a measured usable-cell-area or timing gain. The old pinned support-tools revision already contains the same tile dimensions. Its 6x4 DEF and the new main 6x4 DEF are byte-identical, SHA256 `b46d9a0ee8352160e48dbc8312f092f985629061df736c7f46d58686535a76f4`. Thus organizer confirmation resolves availability/finality rather than introducing an entirely new floorplan to our tools.

The [CMOS5L tech class](https://github.com/TinyTapeout/tt-support-tools/blob/9d13ff3e3e6202090740110438c6a10c1d62ca0f/tech.py) still caps project routing at Metal4 and reserves TopMetal1 for chip-level power. Do not copy the PDK's broader default routing maximum into project config: generated TT user config supplies the project cap. The new PDK keeps nominal fast1.32V/-40C, typical1.20V/25C and slow1.08V/125C timing corners. Its LibreLane configs changed; SRAM macro compatibility and final resolved PDN settings still need native validation. Matching corner names do not establish matching timing results.

An isolated full-source generator probe reached the official YoWASP port checker but failed to open existing absolute source paths under /tmp. Disposable dependencies/cache and an unsandboxed retry did not resolve this local WASI file-access issue. No generated 8x4 config success is claimed; the copied old user_config.json is stale and is not new-flow evidence. No synthesis, PDK installation, routing or timing with dev4 has been performed locally. The machine has no Docker executable, so native container validation belongs in CI.

## Recommended comparison

Prepared `gds-official-nov9-preflight.yaml`: two independent jobs select 6x4/8x4 on the exact measured clock75 RTL, retain the same project configuration, fetch the same hash-verified SRAM views, and use the retrieved official support-tools snapshot plus LibreLane3.1.0.dev4/Ciel. No installer override or manual-PDK option. Capture actual container identity/OpenROAD version and verify the expected default PDK hash. The unchanged stock Classic sequence stops at OpenROAD.GeneratePDN, after native macro checks, pre-PNR STA, floorplan, manual SRAM placement and PDN generation. This is a bounded compatibility check, not a timing screen; timing/electrical/antenna/overflow qualification remains a subsequent step.

Local validation: exact 187-line source preparation passes in an isolated archive; both geometry preparations pass and all declared RTL bytes match the measured clock75 control. Input inventories match between the two geometries, wrong starting geometry is rejected, 26 existing portable-profile tests pass, actionlint passes, and all workflow shell blocks/embedded Python parse. The new generated/native audits have not executed successfully locally because the official generator's WASI access issue remains; CI must exercise them before any compatibility claim. Main official jobs/source/config/info remain untouched.

1. Prepare a separate CI diagnostic using the new stock action's tools, LibreLane and Ciel-managed PDK, without editing official jobs. Validate source ports, SRAM views, generated config, all corners, Metal4 cap and actual engine identity before spending hours on PNR.
2. Keep the proven 2-lane/4-unit hardware and 20ns clock. Use a same-toolchain 6x4 control and an 8x4 arm differing only in tile selection; record final generated DEF/config and macro legality. Do not add 3/6 resources at the same time.
3. Apply unchanged setup, >=50ps fast hold, zero electrical/antenna/overflow screening gates. Only a passing arm proceeds to completed DRT, extraction and final-netlist protocol replay.
4. Review main source/config integration and the official upstream-template version transition separately. Current official jobs remain untouched; the running constant-storage 6x4 screen remains a useful control but cannot establish dev4/8x4 closure.
