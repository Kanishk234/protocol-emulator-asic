# Bugs

Format for each entry: number, date, symptom, root cause, the check that caught it, the check that now covers it, fix commit.

---

## 1: Template gate-level source list omits the flip-flop UDPs
- **Date:** 2026-09-25
- **Symptom:** `gl_test` fails at elaboration with `Unknown module type: ihp_dff_r` as soon as the design has flip-flops. (Seen on the TRIPWIRE branch, gds run 35821375890; carried over preemptively since WARP uses the same template.)
- **Root cause:** in the IHP-Open-PDK revision the CMOS5L action pins, the flip-flop UDPs live in `sg13cmos5l_stdcell/verilog/sg13cmos5l_udp.v`, which the upstream `cmos5l` template's `test/Makefile` does not list.
- **Caught by:** `gl_test` (CI).
- **Now covered by:** `gl_test` on every `gds` run, and `scripts/gl_local.sh` once added.
- **Fix:** add the UDP file to the gate-level `VERILOG_SOURCES` in `test/Makefile`. Fix commit: pending.

## 2: Magic stream-out hangs on a FABulous tile in CMOS5L
- **Date:** 2026-09-25
- **Symptom:** LibreLane step `Magic.StreamOut` on the `LUT4x8_ha` tile (`spikes/tile_cmos5l`) prints `DEF read, Line 67..70 (Error): No cut layer specified in VIARULE` (4 errors), then runs at 100 % CPU with an empty log for 9+ minutes; stopped by hand. No GDS produced.
- **Root cause:** not yet known. The 4 via rules are the power-grid vias OpenROAD generates for the Metal4/TopMetal1 grid; Magic's CMOS5L tech file (PDK 2bbec75) apparently has no matching via rule.
- **Caught by:** the tile hardening spike (manual).
- **Now covered by:** nothing yet. Next: KLayout stream-out for tiles and the fabric (as Tiny FABulous does), and a check that the flow finishes in bounded time.
- **Update (run 2):** hung again in the same way; skipping the step through the tile's `meta.substituting_steps` had no effect, because `tiles.py` builds the flow from a dict and does not apply them.
- **Fix (workaround):** our patch to the tile driver applies step removals; tiles skip Magic and use KLayout stream-out (run 3: GDS written, KLayout DRC 0). Root cause in Magic still open; Magic LEF writing is also skipped, so the fabric needs another LEF source. Fix commit: pending (spike).
