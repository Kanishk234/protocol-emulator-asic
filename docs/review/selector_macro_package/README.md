# SRAM provenance package for selector integration review

Review-only companion files for `RM_IHPSG13_1P_512x16_c2_bm_bist`. They are
not installed under `macro/` and do not change the active physical candidate.
At integration, package these alongside the eight vendor views after reviewing
the coherent source bundle. Keep every vendor header and file byte unchanged.

The eight views come from [IHP-Open-PDK revision2bbec755](https://github.com/IHP-GmbH/IHP-Open-PDK/tree/2bbec755dc67ca3db0261c3d6163e15735d66710/ihp-sg13g2/libs.ref/sg13g2_sram).
`PROVENANCE.json` records each upstream path, byte count and SHA256 from the
independently verified170-input selector reconstruction. This is the SRAM
source pin; the active standard-cell/toolchain PDK pin is89d42ee6. They are
intentionally recorded separately.

`LICENSE` is an exact copy of the upstream repository's
[license at the SRAM source revision](https://github.com/IHP-GmbH/IHP-Open-PDK/blob/2bbec755dc67ca3db0261c3d6163e15735d66710/LICENSE).
All seven text views carry Apache-2.0 license headers. The macro LEF/CDL/timing
views and wrapper credit2025IHP PDK Authors; the shared behavioral core credits
2023IHP PDK Authors. The GDS is binary; no embedded copyright-header claim is
made. Root and SRAM-directory listings contain no standalone NOTICE file;
this package does not invent an upstream NOTICE or replace source headers.

| Views | Role |
| --- | --- |
| GDS / LEF | Layout / routing abstract |
| Three Liberty files | Typical, fast and slow macro timing |
| CDL | LVS netlist |
| Two Verilog files | Simulation models; synthesis uses the separate blackbox |

Integration references retained from the existing R3 overlay README:

- [Loom](https://github.com/thomasgilbert481/tt_um_loom), Thomas Gilbert,
  `sram-smoke` branch: reference for the CMOS5L SRAM recipe and PDN Tcl.
- [Uri Shaked's SRAM test](https://www.tinytapeout.com/chips/ttihp0p2/tt_um_urish_sram_test):
  reference for the blackbox/MACROS arrangement.

PDN Tcl is outside this SRAM-view package. Its existing provenance header must
also be retained when applying the integration bundle. No source count,
physical-config adoption or final signoff decision is made here.
