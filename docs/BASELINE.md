# Qualified Phase 2 baseline

Phase 2 completed on the full design: **8×4 CMOS5L tiles, two reflex lanes, four timed pin units, 512×16 SRAM, 20 ns clock period**.

[Official run 44189196098](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44189196098) built source `e19556e1df1e2f87d4c195af618adb67a8063852`. GDS, precheck (10/10), gate-level tests (3/3), and viewer succeeded. The exact final netlist also passed the complete 22-case protocol replay in run 44123392388. Closure CI on 7f3ae9a passed unit, test, lint and docs.

| Measurement | Qualified result |
|---|---:|
| Slow functional setup reserve | +0.163304 ns |
| Fast hold slack | +0.150773287 ns |
| Aggregate setup worst slack | 0 ns (not a positive reserve measurement) |
| Final route / KLayout / LVS / antenna violations | 0 |
| Timing / electrical violations | 0 |

D-185 explicitly excludes unsupported SRAM Magic DRC and abstract overlap fatality. Ten reviewed abstract overlap markers remain. **Raw Magic zero is not claimed.** Full-GDS CMOS5L KLayout DRC must pass with zero violations.

The GDS job took 2 h 58 min 43 s; the full workflow took 3 h 7 min 50 s. This is historical evidence, not a runtime guarantee.

| Artifact | SHA-256 |
|---|---|
| Final netlist | `537f41adee4320df81a0b7e907f011510cc578ab3c2a17105e00a80e0bacbcc9` |
| GDS | `2a16d4e6d8dc12d60ce355153b3e4c30fc58cdc7610dafe895a3224b299f28f8` |
| Routed ODB | `357f01366aea053ca83db4b035625033424378aecc5ff17addaf4711421b00d4` |

Toolchain: LibreLane 3.1.0.dev4; CMOS5L PDK 89d42ee6d2fd9b50b86a1aada6fee6673c3e6008; Tiny Tapeout Icarus 13. Macro source provenance remains the revision documented in macro/; it is distinct from the signoff PDK revision.

[Detailed official evidence](reports/PHASE2_OFFICIAL_GREEN_44189196098.md) · [Warning review and limitations](reports/PHASE2_WARNING_REVIEW_44189196098.md) · [Phase 2 summary](summaries/PHASE2.md) · [Viewer](https://kanishk234.github.io/protocol-emulator-asic/)

This cleanup preserves the qualified hardware, constraints, generated encodings and official workflow jobs. Future hardware changes require fresh qualification. Simulation is not real-hardware validation; USB/Ethernet support is not claimed.
