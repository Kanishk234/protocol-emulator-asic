# Worklog

Newest entry at the top. One entry per session: what was done, boxes ticked (with evidence), next step.

---

## 2026-09-25 (session 3)
**Done:**
- Nix 2.35.2 installed by the user; FOSSi cache configured (`/etc/nix/nix.conf`). LibreLane 3.0.0 + FABulous plugin environment builds in 2.5 min (Nix store 6.9 GB). CMOS5L PDK at TT's revision in `~/.cache/warp/pdk-full`. CI LibreLane version recorded (3.1.0.dev3).
- `fabric` CI run 36196784852 green (FABulous demo in CI).
- **First FABulous tile on CMOS5L** (`spikes/tile_cmos5l`, patch D-010): `LUT4x8_ha` routes at the SG13G2 size/density: 40.7K µm² per 8 LUT4s (~5.1K µm² per LUT4), 97 % utilisation, 0 routing and antenna violations. `docs/reports/tile_cmos5l.md`. Capacity at 6x4: ~96 LUT4s with margin (the synthesis estimate was 60–90). D-008 updated; still stands (UART ~215 cells).
- Magic stream-out hung (BUGS #2); stopped by hand, so no GDS/DRC/STA yet.

**Boxes ticked:** none new (tile hardening is phase 1 evidence; `fab_demo` got its CI run ID).

**Next step:** KLayout stream-out + DRC + STA for the tile (BUGS #2). Close phase 0: organizer email (user), `fpga` workflow run (user clicks), `unit` workflow, phase 0 summary. D-008 decision (user).

## 2026-09-25 (session 2, part 3)
**Done:** `fabric` workflow (`.github/workflows/fabric.yaml`) runs `spikes/fab_demo/run.sh` in CI with the pinned tools (Ubuntu Python 3.12, OSS CAD Suite 2026-06-29, cached). PRISM prior-art notes (`docs/notes/prior_art.md`): Verilog → Yosys → bitstream on IHP already exists there, with a fixed datapath close to our hard-block candidates; our claims must rest on the parallel fabric model and the measured method.
**Boxes ticked:** PRISM notes.
**Next step:** push; record the first `fabric` run ID. Waiting on the user: Nix install (tile hardening), D-008, organizer email. The `main` gate is resolved: every "green on `main`" rule (CLAUDE.md, phase checklists) now says `efpga` (user decision, 2026-09-25).

## 2026-09-25 (session 2, continued)
**Done:**
- `gds` 36170807513 on a63877d fully green: hardening 35.1 min, precheck 12.3 min, `gl_test` pass. Recorded in `PHYSICAL_DESIGN_AND_CI.md`. Cell stats and the CI LibreLane version need the `GDS_logs` artifact (login required).
- Tiny FABulous study: `docs/notes/tiny_fabulous.md`. Tiles → fabric → top, three LibreLane runs, submitted via `custom_gds`. Phase 0 decision point answered: D-009 (yes; our plan: fabric macro integrated by the template `gds` job, as TRIPWIRE's R3 did with the SRAM).
- Early capacity estimate: `docs/reports/capacity_early.md`. ~4.5K µm² per LUT4 (stock LUT4AB tile, cmos5l synthesis), so a generic 6x4 fabric holds ~60–90 LUT4s; a scratch UART needs ~215. Proposed D-008 (the fallback becomes G0 + minimal hard primitives).

**Boxes ticked:** template design green on `test`/`gds`/precheck/`gl_test`; hardening time; Tiny FABulous read + written down; phase 0 decision point (D-009).

**Open in phase 0:** PRISM notes; `unit` workflow (waits for the first Python tool); the template `fpga` workflow has never run (manual); `VERSIONS.md` CI LibreLane version; "all CI green on `main`" (`main` is TRIPWIRE: the gate needs retargeting to `efpga` or a separate repo; the user decides); organizer email; phase 0 summary.

**Next step:** the user decides D-008. Then harden one LUT4AB tile on cmos5l with `FABulousTile` (needs OpenROAD/KLayout/Magic: Nix or the LibreLane container) to replace the synthesis estimate with a real one.

## 2026-09-25 (session 2)
**Done:**
- Fixed the `gds` docs check failure (empty title/author/description/pinout, missing `info.md` sections): filled `info.yaml` (WARP, 6x4, 50 MHz, `tt_um_warp`) and `docs/info.md`. Pinout is provisional (D-006).
- Renamed the placeholder top to `tt_um_warp` (`src/tt_um_warp.v`, `test/tb.v`, `test/Makefile`).
- Took the template `gl_test` UDP fix preemptively (BUGS #1).
- Added `scripts/setup_venv.sh`, `check_all.sh`, `gl_local.sh`, `requirements-dev.txt`, the `lint` workflow, and the `gds` paths filter + non-cancelling concurrency.
- Installed OSS CAD Suite 2026-09-25 to `~/oss-cad-suite`; FABulous-FPGA 2.2.0 into `.venv` (pinned). PATH order D-007; versions in `docs/VERSIONS.md`.
- Deleted the duplicate `docs/OVERVIEW.md` (the user did this).

**Boxes ticked (phase 0):** repo/info.yaml (local `--check-docs` pass; CI `docs` 36170807355 green on a63877d), sign-up form (done by Kanishk), docs skeleton, setup_venv, OSS CAD Suite + PATH (D-007), check_all (PASS), gl_local (PASS).

**Later in the session:**
- The user installed `python3-tk` and pushed (a63877d): `test` 36170807382, `lint` 36170807369, `docs` 36170807355 all green; `gds` 36170807513 still running at session end.
- FABulous demo: OSS CAD Suite 2026-09-25 breaks `synth_fabulous`; switched to 2026-06-29, the release FABulous 2.2 pins. `check_all` and `gl_local` re-passed on it.
- `spikes/fab_demo/run.sh`: stock fabric, two bitstreams (stock counter; our `lfsr_down`), each matches its source for 100 cycles, and B mismatches A's source. Report `docs/reports/fab_demo.md`. Ticked: reference fabric, reference design, second design, FABulous pin, and the exit item "two different bitstreams".
- Found: FABulous's wrapper generator only wires its own demo design (see the report); our compile flow needs its own.

**Next step:** check `gds` 36170807513 (precheck, `gl_test`, hardening time, LibreLane version). Then the Tiny FABulous study (how the fabric went through the TT flow), which answers the phase 0 decision point, and the LUT4AB area / config-bit measurement on cmos5l for the early capacity estimate. The organizer email is still open (the user will send it; low priority). `unit` workflow waits for the first Python tool with tests.

## 2026-09-25
**Done:** Project plan, CLAUDE.md and phase docs created (drafted in a Claude chat, not yet checked against a working repo).
**Boxes ticked:** none.
**Next step:** Phase 0, first task: create the repo from the CMOS5L template.
