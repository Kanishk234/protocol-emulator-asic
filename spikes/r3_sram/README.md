# R3 risk spike: the IHP 512x16 SRAM macro through the TT cmos5l flow

Phase 1 task 15 (R3). Question: does `RM_IHPSG13_1P_512x16_c2_bm_bist` pass the real Tiny Tapeout flow (`gds`, `precheck`, `gl_test`) on cmos5l? Decision: macro, or the flop-store fallback behind the same `trw_sram` interface (PHYSICAL_DESIGN_AND_CI.md §3). DECISIONS D-031.

The hardening runs on the branch **`spike/r3-sram`**, which is never merged. `main` keeps only this folder. The macro views are downloaded when the branch is made, never committed to `main`, because a `macro/**` change on `main` would start a 6x4 hardening.

## What is here

| Path | What |
|---|---|
| `overlay/` | Files that replace or add to the repo on the branch: `info.yaml` (2x2), `src/tt_um_tripwire.v` (the test top), `src/trw_sram.v` (the wrapper), `src/RM_...v` (blackbox), `src/config.json` (MACROS + PDN keys), `src/pdn_cfg.tcl` (Loom's, verbatim), `test/Makefile`, `test/test.py`, `macro/.../README.md`, `.gitattributes` |
| `fetch_macro.sh` | Downloads the 8 macro views from IHP-Open-PDK at the pinned revision and checks their sizes |
| `check_local.sh` | Verilator lint, the cocotb suite on the RTL, and on a Yosys gate-level netlist with TT's Icarus 13 (works from `main`) |
| `apply_to_branch.sh` | Copies `overlay/` into the checkout and vendors the macro; refuses to run anywhere but `spike/r3-sram` |

## The test design
- **Direct access:** write or read any word from the pins, through byte registers.
- **BIST:** 18 passes over all 512 words:
  - 16 walking-ones passes, so every word holds every single-bit value;
  - an address-unique pattern;
  - its complement, which is left in the memory.
- **Tests** (pin-level, so they also run in `gl_test`):
  - reset state;
  - every address line and data bit, with no aliasing;
  - the BIST passes, and an independent read-back of the pattern it leaves.
- **Mutation checks** (local): a wrong BIST write in one pass is caught (BIST fails); aliased address lines are caught by both the direct test and the BIST.

## Steps

```
# on main, after committing spikes/r3_sram:
spikes/r3_sram/check_local.sh                    # expect: check_local: PASS
git checkout -b spike/r3-sram
spikes/r3_sram/apply_to_branch.sh
git add -A && git commit -m "spike: R3 SRAM macro smoke project (2x2)"
git push -u origin spike/r3-sram                 # starts gds on the branch; main is not affected
git checkout main
```

Then read the `gds` run: `gds`, `precheck` and `gl_test` must pass. The `viewer` job may fail on a branch (GitHub Pages usually only deploys from `main`); that does not matter for R3. Record the run ID and numbers in `docs/reports/AREA.md` and D-031 on `main`.
