# src/fabric_gen: generated and upstream fabric RTL (never hand-edited)

| File | Origin | License |
|---|---|---|
| `bitbang.v`, `ConfigFSM.v`, `Frame_Data_Reg.v`, `Frame_Select.v` | FABulous 2.2.0 project template (`fabulous/fabric_files/FABulous_project_template_verilog/Fabric/`), copied unmodified | Apache-2.0 (FABulous, https://github.com/FPGA-Research/FABulous) |

These are FABulous's standard configuration path: a two-pin bit-bang receiver and the frame-based configuration state machine (sync word `0xFAB0FAB1`), plus per-row frame-data registers and per-column frame-select decoders. `src/wp_fabric_cfg.v` wires them to the fabric macro.

They use asynchronous active-low resets (upstream style); WARP's own RTL uses synchronous resets (CLAUDE.md). Regenerate by copying them again from the pinned FABulous release (`docs/VERSIONS.md`).
