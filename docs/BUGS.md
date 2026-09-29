# Bugs

Format for each entry: number, date, symptom, root cause, the check that caught it, the check that now covers it, fix commit.

---

## ANISH-FAB-10: Small-grid test assumed wrong external enable polarity
- **Date:** 2026-09-29; **Status:** test corrected.
- First cold-load test expected external T=0011 and failed at check zero
  with T=1100. The compiled user's io_oeb is active-low, while the generated
  I/O primitive explicitly inverts T on its external T_top port.
- Pin order was verified against both wrappers and was already correct.
  Changed only the oracle's expected external enable to 1100; no RTL repair.
- Covered by all 1,074 checks in both RTL and mixed-level runs listed in
  `reports/ANISH_SMALL_COLD.md`. Wrong-result control still fails at zero.


## ANISH-FAB-1: Reference synthesis tool mismatch and paths containing spaces
- **Date:** 2026-09-25
- **Symptom:** FABulous 2.2 with OSS CAD Suite 2026-09-25 fails on missing
  primitive definitions or leaves unmapped LUT/FF cells; the bundled Icarus
  helper invocation also splits the Windows installation path at a space.
- **Root cause:** changed `synth_fabulous` interface and missing legacy
  technology maps; Icarus launches helpers through shell command strings.
- **Caught by:** the local full reference-flow experiment, retained under
  `build/fabric-reference-*`; also independently reported on `origin/efpga`
  in `docs/reports/fab_demo.md` at `b45a1d8` for the synthesis mismatch.
- **Fix:** use the supported June 29 release from a Linux path without
  spaces; build generated Taskfiles under a fresh `/tmp` directory. Remove
  the exploratory replacement maps, including an unsafe direct mapping
  between FF types with different reset/enable priorities.
- **Coverage:** `scripts/fabric_reference.sh` rejects the wrong Yosys
  version and runs independent reset/enable and persistent reload checks.
  Changes remain uncommitted on `anish_branch`.

## ANISH-FAB-2: Persistent reference reload stalls
- **Date:** 2026-09-25 · **Status:** open, reproducible locally.
- **Symptom:** replacing a working counter with an
  LFSR configuration fails to finish. A shortened reproduction stalls
  at byte 1996 (column 1/frame 12) of the second upload. The LFSR from
  startup passes 1,157 checks.
- **Root cause evidence:** mixed old/new configuration introduces LUT
  feedback absent from both final images. Static frame snapshots identify
  X1Y8/LC with `Y = Y ? 0 : A`; a read-only live probe observes A=1 and 64
  output transitions at the same simulation timestamp. This demonstrates
  RTL-model oscillation; no physical frequency/current claim is made.
- **Caught by / coverage:** independent public-port A/B/A test in
  `experiments/fabric_reference/reload_tb.v`, bounded by the runner's wall
  timeout. Wrong-bitstream negative control also fails as intended.
- **Evidence:** `docs/reports/ANISH_REFERENCE.md`; raw local run
  `warp-reference.OBUfXfus`; cached rechecks `warp-recheck.EAQHpix8` and
  `warp-recheck.GJ42Zo6F`, plus four SCC snapshots listed in the report.
  No fix is claimed. Safe load ordering or fabric
  isolation must be tested before closing the reconfiguration gate.

## ANISH-FAB-3: Editing a live experiment runner corrupts later shell parsing
- **Date:** 2026-09-26 · **Status:** runner snapshot fix implemented.
- **Symptom:** after timing out the intended simulator subprocesses, two
  exploratory ordering runs produced shell syntax errors; one repeated a
  status line. Individual simulation logs remain useful, but the aggregate
  runner result is not a clean regression result.
- **Root cause:** Bash was reading a script that changed during execution.
- **Fix:** `scripts/fabric_order.sh` copies itself into ignored `build/`
  and executes that immutable snapshot. The evidence includes the runner.
- **Coverage:** the hold validation run uses a captured runner while the
  working script receives a later manifest-only edit; its completion is
  recorded in `ANISH_RELOAD_EXPERIMENTS.md`. No synthesis/RTL bug is implied.

## ANISH-FAB-4: Area reporter rejects valid CMOS5L mappings
- **Date:** 2026-09-26 · **Status:** fixed in the local cost runner.
- **Symptom:** synthesis and functional gate-level checks passed, but the
  initial area reporter rejected valid cells and later hierarchy metadata.
- **Root cause:** it expected the `sg13g2_` prefix instead of `sg13cmos5l_`,
  and counted Yosys `$scopeinfo` metadata as an unmapped hardware cell.
- **Fix/coverage:** allow the correct library prefix, exclude only that
  metadata type, and still reject any other unmapped type. Successful run
  `warp-guard-cost.3TVEQJRI` records all three area summaries and both
  functional gate-level checks. Failed attempts remain separate evidence.

## ANISH-FAB-5: Mapped validator check lacks standard-cell directions
- **Date:** 2026-09-27 · **Status:** fixed in the new validator runner.
- **Symptom:** `warp-validator.RbPFjlt3` passes RTL but Yosys `check -assert`
  flags eight apparently undriven nets after mapping.
- **Cause:** Liberty was provided to mapping but not loaded as cell module
  definitions, so the checker could not resolve mapped output directions.
- **Fix/coverage:** `read_liberty -lib cells.lib` before mapping, keeping
  strict checks both before and after mapping. `warp-validator.x2xpdWlS`
  reports zero check problems and passes all 41 functional GL cases.

## ANISH-FAB-6: Mapped-loader test references optimized private mux wires
- **Date:** 2026-09-28 · **Status:** test adaptation complete.
- **Symptom:** `warp-loader-cost.BdPJ8rhn` maps successfully but GL cannot
  bind `LocalWriteData` / `LocalWriteStrobe`, absorbed during optimization.
- **Fix/coverage:** mapped-loader mode observes input ports and retains
  downstream comparisons of every frame address and all 14 row words.
  `warp-loader-cost.AXvDP6i0` passes both CRC modes and both image payloads.
  No RTL failure or physical-timing repair is implied.

## ANISH-FAB-7: Loader area counted twice in a hierarchical report
- **Date:** 2026-09-28 · **Status:** reporter fixed and regression covered.
- **Symptom:** initial `warp-loader-cost.2wpvyEF9` summary overstated total
  area by adding the loader to a parent area that already included it.
- **Fix:** compute each module's direct standard-cell area from its local
  histogram and Liberty values, sum once, then check the inclusive Yosys
  top area independently. Verify exactly one child at each boundary.
- **Coverage:** three reporter tests cover one-time counting, inconsistent
  hierarchical totals and pruned row data. Final end-to-end run
  `warp-loader-cost.AXvDP6i0` confirms corrected totals and functional GL.
  The original erroneous summary is retained with a do-not-use filename.

## ANISH-FAB-9: Custom demo wrapper produced an empty compilation
- **Date:** 2026-09-29 · **Status:** compilation acceptance repaired.
- `warp-small-compile.kAys0TJS` left the new counter's I/O unconnected.
  FABulous warned that custom designs need manual wrapper connections;
  checking only the binary's existence incorrectly accepted the result.
- Runner now connects each bus explicitly before compiling and rejects
  empty features, absent logic, zero routed arcs and wrong image length.
- Corrected `warp-small-compile.khvqjtBG`: four logic cells, 70 features,
  504 bytes. Behavioral execution remains a separate open gate; see
  `ANISH_SMALL_COMPILE.md`. The original false PASS is retained as invalid.

## ANISH-FAB-8: Flat tile mapping blocked by programmable feedback
- **Date:** 2026-09-28 · **Status:** physical-flow integration open.
- Initial probe omitted MUX8LUT_frame_config_mux.v; hierarchy checking caught
  it before mapping. The corrected source list exposes structural feedback:
  184 stock and 189 held-tile check warnings in `warp-tile-preflight.hbGIhisV`.
- These are programmable graph loops, not a count of runtime oscillations.
  Strict cost mapping stops; no tile area or physical result is reported.
- The new preflight retains both variants and fails the gate visibly.
  Next investigate the pinned tile hardening method and configuration-aware
  checks. See `ANISH_PHYSICAL_PREFLIGHT.md`; no blanket waiver was added.
- Follow-up `ANISH_TILE_MAPPING.md`: the tile maps with storage preserved,
  but zero hierarchy/mapped check counts hide the programmable feedback.
  Expanding Liberty functions exposes loops again. The new measurement
  records every stage; physical/timing/release gates remain open.

## 1: Template gate-level source list omits the flip-flop UDPs
- **Date:** 2026-09-25
- **Symptom:** `gl_test` fails at elaboration with `Unknown module type: ihp_dff_r` as soon as the design has flip-flops. (Seen on the TRIPWIRE branch, gds run 35821375890; carried over preemptively since WARP uses the same template.)
- **Root cause:** in the IHP-Open-PDK revision the CMOS5L action pins, the flip-flop UDPs live in `sg13cmos5l_stdcell/verilog/sg13cmos5l_udp.v`, which the upstream `cmos5l` template's `test/Makefile` does not list.
- **Caught by:** `gl_test` (CI).
- **Now covered by:** `gl_test` on every `gds` run, and `scripts/gl_local.sh` once added.
- **Fix:** add the UDP file to the gate-level `VERILOG_SOURCES` in `test/Makefile`. Fix commit: pending.
