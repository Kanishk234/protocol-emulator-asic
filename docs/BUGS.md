# Bugs

Format for each entry: number, date, symptom, root cause, the check that caught it, the check that now covers it, fix commit.

---

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

## 1: Template gate-level source list omits the flip-flop UDPs
- **Date:** 2026-09-25
- **Symptom:** `gl_test` fails at elaboration with `Unknown module type: ihp_dff_r` as soon as the design has flip-flops. (Seen on the TRIPWIRE branch, gds run 35821375890; carried over preemptively since WARP uses the same template.)
- **Root cause:** in the IHP-Open-PDK revision the CMOS5L action pins, the flip-flop UDPs live in `sg13cmos5l_stdcell/verilog/sg13cmos5l_udp.v`, which the upstream `cmos5l` template's `test/Makefile` does not list.
- **Caught by:** `gl_test` (CI).
- **Now covered by:** `gl_test` on every `gds` run, and `scripts/gl_local.sh` once added.
- **Fix:** add the UDP file to the gate-level `VERILOG_SOURCES` in `test/Makefile`. Fix commit: pending.
