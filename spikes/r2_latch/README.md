# R2 risk spike: one lane with its latch slot array through the TT cmos5l flow

Phase 1 task 14 (R2). **Question:** does the latch slot array (Ibex-style, one library clock gate per 16-bit word) survive the Tiny Tapeout flow: hardening, `precheck` and `gl_test`? **Decision:** latches, or 8 flop slots per lane. The run also gives post-route timing for the whole lane, which is the recheck D-030 asks for. DECISIONS D-032.

It hardens on the branch **`spike/r2-latch`**, which is never merged. It can run at the same time as R3's `spike/r3-sram`, because each ref has its own `gds` concurrency group.

## What is on the chip (3x2)
- **The R1 lane, unchanged** (copied from `spikes/r1_lane/` by `apply_to_branch.sh`, so there is one source): `trw_lane`, `trw_alu`, `trw_slots`, `trw_cport`.
  - In synthesis, `trw_slots` uses the library ICG `sg13cmos5l_lgcp_1` (`ifdef SYNTHESIS`).
  - It has a debug read port, so every latch word can be read back from the pins.
- **Pin-driven stand-ins for the rest of the chip:**
  - a producer register feeding I0 through a real consumer port;
  - blocking subscribers for O0 and O1 that take a token on a strobe;
  - a routine instruction register, loaded from the pins.
- **`src/config.json`:** the template's, plus `PNR_SDC_FILE` / `SIGNOFF_SDC_FILE` (added after run 1, D-032) and, for run 3 (D-034), `PL_TARGET_DENSITY_PCT` 52 and `DRT_OPT_ITERS` 20. `pnr.sdc` stops the post-CTS resizer chasing the latch data pins; they borrow time, so STA reports slack 0.000. `signoff.sdc` is the plain default. This is a 3x2 tile, not the 2x2 in the phase doc: the lane is about 79K µm² before layout, which would be tight on a 2x2 core (~150K µm²) with four metal layers.

## Tests (pin-level, so they also run in `gl_test`)
- `test_latch_array_holds_two_patterns`: all 52 words (636 slot bits + 64 K bits) with a pattern and its complement, read back.
- `test_lane_runs_a_program`: loads a program and runs it. It covers:
  - ISA.md §7.1 (forward 3 bytes, then an EVENT);
  - a routine step pair (LDI r1, then SETF f1), which a slot waits for and then forwards;
  - a K constant sent as a CTRL token;
  - checks that slot writes are ignored while running.

## Local results (`check_local.sh`)
- Lint as the `lint` workflow runs it: clean.
- RTL: 2/2. Gate level (Yosys netlist with 700 latches and 52 `lgcp` cells, TT Icarus 13): 2/2.
- OpenSTA on the Yosys netlist (no wires, ideal clock): flop endpoints +14.0 ns (typ) and +10.8 ns (slow) setup slack. Latch D pins show 0 slack because they borrow time into the transparent phase (expected).

## Steps

```
# on main, after committing spikes/r2_latch (and the updated spikes/r1_lane):
spikes/r2_latch/check_local.sh                   # expect: check_local: PASS
git checkout -b spike/r2-latch
spikes/r2_latch/apply_to_branch.sh
git add -A && git commit -m "spike: R2 lane + latch slot array smoke project (3x2)"
git push -u origin spike/r2-latch
git checkout main
```

**Pass criteria:** `gds`, `precheck` and `gl_test` green. From the gds logs, also record:
- setup and hold slack at typ/slow/fast, with latch checks present in the STA report;
- utilisation and Metal3 overflow.

That gives the post-route EVAL slack for D-030 (revisit if it falls below 2 ns at the slow corner).
