# TRIPWIRE bug ledger

Every bug found by any layer, newest at the bottom. Nothing is fixed silently.

| # | Date | Block | Symptom | Root cause | Caught by (check ID) | Now covered by | Fix commit |
|---|---|---|---|---|---|---|---|
| 1 | 2026-09-23 | `test/Makefile` (from the TT cmos5l template) | `gl_test` in gds run 35821375890 fails at elaboration: `Unknown module type: ihp_dff_r` (8 refs, one per counter flop) | In the pinned IHP-Open-PDK (rev 2bbec75), the flip-flop UDPs (`ihp_dff_r`, …) live in `sg13cmos5l_stdcell/verilog/sg13cmos5l_udp.v`, which the template's gate-level source list omits. Upstream template `cmos5l` has the same omission | L8-GL (`gl_test`) | L8-GL in CI, plus `scripts/gl_local.sh` (Yosys netlist on `sg13cmos5l_stdcell_typ_1p20V_25C.lib` + TT Icarus 13): without the UDP line it fails with the same error, with it 4/4 pass | pending |

Note on #1: gate-level simulation also needs Tiny Tapeout's Icarus 13 build, which is what CI installs. Stock Icarus 12 leaves the cell models' `delayed_*` timing-check nets undriven, so every flop reads X. Use the TT build for any local gate-level run.
