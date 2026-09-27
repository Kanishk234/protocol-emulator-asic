# src/fabric_gen: generated and upstream fabric RTL (never hand-edited)

| File | Origin | License |
|---|---|---|
| `ConfigFSM.v`, `Frame_Data_Reg.v` | FABulous 2.2.0 project template (`fabulous/fabric_files/FABulous_project_template_verilog/Fabric/`), copied unmodified | Apache-2.0 (FABulous, https://github.com/FPGA-Research/FABulous) |

These are FABulous's standard configuration path, minus its bit-bang receiver (WARP's shell, `src/wp_shell.v`, delivers the words since phase 2) and its per-column `Frame_Select` decoder (replaced by `src/wp_frame_select.v`, which decodes a frame number per column so fewer wires cross the chip, D-025): the frame-based configuration state machine (sync word `0xFAB0FAB1`) and the per-row frame-data registers. `src/wp_fabric_cfg.v` wires them to the fabric macro.

They use asynchronous active-low resets (upstream style); WARP's own RTL uses synchronous resets (CLAUDE.md). Regenerate by copying them again from the pinned FABulous release (`docs/VERSIONS.md`).
