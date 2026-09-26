# RM_IHPSG13_1P_512x16_c2_bm_bist (vendored for R3)

IHP's 512 × 16 single-port SRAM macro with bit mask and BIST, vendored so that the `gds` workflow hardens against a fixed copy.

- **Source:** https://github.com/IHP-GmbH/IHP-Open-PDK at commit `2bbec755dc67ca3db0261c3d6163e15735d66710` (the revision `tt-gds-action@ihp-cmos5l` and `scripts/gl_local.sh` pin), path `ihp-sg13g2/libs.ref/sg13g2_sram/{gds,lef,lib,cdl,verilog}/`.
- **Why sg13g2:** the cmos5l PDK has no SRAM of its own; `ihp-sg13cmos5l/libs.ref/sg13cmos5l_sram` links to the SG13G2 directory.
- **Fetched and checked by** `spikes/r3_sram/fetch_macro.sh` (byte counts per file). No file is modified.
- **Licence:** Apache-2.0 (IHP PDK Authors).

| File | Use |
|---|---|
| `.gds`, `.lef` | layout and abstract (`SIZE 236.8 BY 191.34`; Metal1–Metal4 only) |
| `_typ/_fast/_slow` `.lib` | timing, per corner |
| `.cdl` | LVS netlist (the macro is abstracted in extraction: `MAGIC_EXT_ABSTRACT_CELLS`) |
| `.v`, `RM_IHPSG13_1P_core_behavioral_bm_bist.v` | simulation model only (`test/Makefile`); synthesis uses the blackbox in `src/` |

## Credits
The integration recipe (instance placement, PDN stripe alignment, `pdn_cfg.tcl`, the Magic and LVS settings) comes from two public projects:
- **Loom** (Thomas Gilbert, Apache-2.0), https://github.com/thomasgilbert481/tt_um_loom, branch `sram-smoke`: the first cmos5l hardening of this macro. We use its `src/pdn_cfg.tcl` verbatim and its `config.json` settings.
- **`tt_um_urish_sram_test`** (Uri Shaked), https://www.tinytapeout.com/chips/ttihp0p2/tt_um_urish_sram_test: the SG13G2 reference for the blackbox + `MACROS` arrangement.
