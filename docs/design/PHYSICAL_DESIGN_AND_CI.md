# TRIPWIRE: physical design and CI

A reference for everything between "the RTL simulates" and "every workflow is green and the GDS is submittable":
- the Tiny Tapeout flow on IHP CMOS5L
- the SRAM macro
- latch arrays
- routing-time limits
- each CI workflow
- the FPGA build
- the freeze procedure

Phase docs link here instead of repeating it.

Companions: `OVERVIEW_TRIPWIRE.md`, `ARCHITECTURE.md`, `VERIFICATION.md`.

---

## 1. Platform facts

| Item | Value | Notes |
|---|---|---|
| Template | `TinyTapeout/ttihp-verilog-template`, branch **cmos5l** | Linked from the Jane Street post |
| Build action | `TinyTapeout/tt-gds-action@ihp-cmos5l`, `pdk: ihp-sg13cmos5l` | Used by the template's `gds` workflow |
| Tile size | **6x4** (1289.28 × 710.64 µm die; core ≈ 902K µm²) | 8x4 is "being worked on" by Jane Street and Tiny Tapeout; not designed for until confirmed in writing |
| Routing layers | Metal1–Metal4 for the project (TopMetal1 belongs to the Tiny Tapeout top level) | One fewer layer than SG13G2, so congestion matters more |
| Clock | `CLOCK_PERIOD` 20 ns (50 MHz); `CLOCK_PORT` `clk` | Sign-off corner is typical; slow-corner results are reported honestly |
| Pads | Specified to ~66 MHz, up to ~10 ns insertion delay | Do not claim sub-ns timing at the pins |
| Top module | `tt_um_tripwire` with the template's ports | All outputs assigned; unused inputs in a `_unused` wire; `ena` ignored |
| Hardening time (6x4, macro design) | ~4–5 h per `gds` run in comparable public designs | GitHub kills jobs at **6 h** |

---

## 2. `src/config.json` rules
- Start from the template's file.
- Change only these, each with a `docs/DECISIONS.md` entry:
  - `CLOCK_PERIOD`
  - `PL_TARGET_DENSITY_PCT`
  - the SRAM macro block (§3)
- Never edit the part the template marks "do not change".
- Keep a comment next to every changed key saying why.

---

## 3. SRAM macro integration

The chosen macro is the IHP `RM_IHPSG13_1P_512x16_c2_bm_bist` (1024x16 is optional). The recipe below follows two public, working examples:
- the Tiny Tapeout SRAM test project (`tt_um_urish_sram_test`, SG13G2);
- the cmos5l integration published by the Loom entry (Apache-2.0).

Credit both in `macro/README.md`.

**Checklist for a macro-clean hardening:**
- [ ] Vendor the macro views into `macro/<name>/`: GDS, LEF, three `.lib` corners, CDL, behavioural Verilog. Record the IHP-Open-PDK commit.
- [ ] A port-only blackbox Verilog in `src/` for the `MACROS` `nl` entry. The behavioural model is used only in simulation.
- [ ] `MACROS` block in `config.json` keyed by the macro name:
  - `instances` keyed by the **flattened instance path** Yosys produces;
  - `location` and `orientation`;
  - `gds`, `lef`, `lib` per corner, `nl`, `spice`.
- [ ] `PDN_MACRO_CONNECTIONS` hooks VDD!/VDDARRAY!/VSS! to VPWR/VGND.
- [ ] A custom `PDN_CFG` so that the Metal4 power stripes line up with the macro's Metal4 power pins, with stripe pitch and offset derived from the macro LEF. On cmos5l the default macro grid (Metal4↔TopMetal1) is empty.
- [ ] `MAGIC_EXT_ABSTRACT_CELLS` for the macro, because the IHP macros are not LVS-clean internally. Magic DRC errors inside the macro are not fatal; the precheck's KLayout DRC is the real gate.
- [ ] Orientation keeps the signal pins facing the logic and the power columns vertical.
- [ ] First try it in a **2x2 smoke project** (phase 1), then move to 6x4.
- [ ] Ask Jane Street / Tiny Tapeout whether macros are accepted on the target shuttle. Record the answer.

**Fallback if the macro fails precheck:** a flop or latch store behind the same `trw_sram` wrapper interface (`addr`, `rdata` one cycle later, `we`/`wdata`). It holds fewer routine words (e.g. 128x16).

---

## 4. Latch arrays (reflex slots)
- Use them only inside `trw_slots.v`, generated from one template, one integrated clock gate per word (Ibex-style).
- Slots are written only while the lane is halted. Treat the write path as a normal synchronous register write into a clock-gated latch word, with the data held stable around the gate pulse.
- Add lint waivers only for intentional latches in that file, each with a comment.
- STA must see latch timing. Check the hold and setup reports for the slot array in the first hardening.
- **Fallback:** flop slots (8 per lane).

---

## 5. Routing time is the binding constraint
- Detailed routing time grows faster than linearly with congestion. In a comparable public 6x4 design, +2% cells in one corner tripled Metal3 overflow and pushed the run past 6 h.
- **Judge every RTL change by global-routing overflow** (in the gds logs), not by cell count. Record it in `docs/reports/AREA.md`.
- **One hardware change per hardening run** after the first full hardening.
- **Targets:**
  - Metal3 overflow well below the level where previous runs blew up; set the concrete number after the first two runs;
  - detailed routing < 4 h;
  - utilisation ≈ 50–58%.
- **Knobs, in order:**
  1. shrink the change;
  2. restrict fabric connectivity;
  3. `PL_TARGET_DENSITY_PCT`;
  4. drop to 2 lanes or 8 slots.
- Optional: run LibreLane locally (the iic-osic-tools Docker image) up to global routing to pre-check congestion without waiting for CI.

---

## 6. CI workflows

| Workflow | Source | Trigger | Green when |
|---|---|---|---|
| `test` | Template (unchanged) | Every push | Pin-level cocotb suite passes under Icarus (`! grep failure results.xml`) |
| `gds` → `gds` | Template jobs; trigger block ours | Push touching `src/**`, `info.yaml`, `macro/**`, the workflow itself; manual dispatch | LibreLane completes; DRC/LVS/antenna clean; timing met at the typical corner |
| `gds` → `precheck` | Template | After `gds` | Tiny Tapeout precheck passes |
| `gds` → `gl_test` | Template | After `gds` | Pin-level suite passes on the netlist |
| `gds` → `viewer` | Template | After `gds` | 3D viewer deployed to GitHub Pages |
| `docs` | Template | Every push | `info.yaml` valid, `docs/info.md` builds |
| `fpga` | Template (manual; `branches: none`) | Manual dispatch | iCE40UP5K bitstream builds (§8) |
| `lint`, `unit`, `formal`, `nightly` | Ours (separate files) | See `VERIFICATION.md` §10 | Their checks pass |

**Rules:**
- **Never edit the template's jobs.** Only `gds.yaml`'s trigger block is ours:
  - a `paths` filter so docs/tools/test-only pushes don't reharden;
  - `concurrency` with cancel-in-progress.
- A push touching `src/`, `info.yaml` or `macro/` **cancels a hardening in progress**. Before pushing during a run, check `git log origin/main..main -- src info.yaml macro` is empty.
- **GitHub Pages:** repository Settings → Pages → Source = **GitHub Actions**. The `viewer` job needs `pages: write` and `id-token: write`, which the template already sets.
- Keep `info.yaml` `source_files` and `test/Makefile` `PROJECT_SOURCES` in sync. The flow fails otherwise.

---

## 7. Gate-level test rules (`gl_test`)
- `gl_test` runs `test/` against the netlist. Tests there may only use **top-level ports**: host SPI plus protocol pins.
- No `initial` blocks in synthesisable code. Every register that matters is reset (synchronous, active-low `rst_n`), so there are no X's after reset.
- No dependence on simulation-only delays.
- If a test passes in RTL but fails at gate level, treat it as an RTL bug until proven otherwise, and log it in `BUGS.md`.

---

## 8. FPGA build (`fpga` workflow)
- The template's action builds the project for an iCE40UP5K (the Tiny Tapeout "ASIC simulator" board).
  - The UP5K has ~5.3K LUT4s, 30 × 4 Kbit block RAMs and 1 Mbit of single-port RAM.
  - The full TRIPWIRE build will likely not fit.
- **Plan (phase 3):**
  1. Add a synthesis-time parameter set for a **reduced build**: 1 lane, 8 slots, 2 pin units, SRAM mapped to FPGA RAM.
  2. Check whether the template's action can select it. If it cannot, add our own `fpga_reduced` workflow (Yosys + nextpnr-ice40 with a define), and record the decision.
  3. Goal: a bitstream builds in CI.
- A physical board is only needed in the optional hardware phase.

---

## 9. Freeze procedure (phase 4)
1. Announce the freeze commit. After this, RTL changes are only for bugs found by verification, each logged and each re-hardened.
2. Run `gds` by hand on the exact freeze commit. It must finish all four jobs (`gds`, `precheck`, `gl_test`, `viewer`) inside the time limit.
3. Record area, timing (typ/slow/fast), overflow, power and run times in `docs/reports/AREA.md`.
4. Tag `freeze-rtl`. Archive the gds artefacts as a release asset.
5. Firmware, tests, tools and docs may continue; they do not trigger hardening.

---

## 10. Measurement log (`docs/reports/AREA.md`)

One row per hardening:

| Column | What goes in it |
|---|---|
| Date, commit, config | |
| Cells, flops, latch bits | |
| Utilisation | |
| Timing | WNS at typ/slow/fast |
| Routing | Metal3/total overflow; detailed routing time; total gds time |
| Checks | DRC/LVS/antenna; precheck; gl_test |
| Notes | |