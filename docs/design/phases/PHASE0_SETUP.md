# Phase 0: setup

| | |
|---|---|
| **Dates** | Sep 23 → Oct 4, 2026 |
| **Goal** | A repository that builds a trivial design through *every* CI workflow, including GitHub Pages; a working local toolchain; questions to Jane Street sent; roles agreed. |
| **Devices needed** | None |
| **References** | `../OVERVIEW_TRIPWIRE.md`, `../PHYSICAL_DESIGN_AND_CI.md` |

---

## 1. Entry criteria
- The cmos5l template cloned locally (done, in WSL).

## 2. Tasks

### 2.1 Repository
1. Create the GitHub repo (public; the competition requires open source), e.g. `tt_um_tripwire`, from the local clone of `ttihp-verilog-template` branch `cmos5l`. Keep the licence (Apache-2.0).
2. Rename the top module `tt_um_example` → **`tt_um_tripwire`** in `src/project.v` (rename the file to `src/tt_um_tripwire.v`), `info.yaml` and `test/tb.v`.
3. Fill in `info.yaml`:
   - title, author(s), description;
   - `tiles: "6x4"`, `clock_hz: 50000000`;
   - `top_module`, `source_files`;
   - a placeholder pinout.
4. Replace the example logic with a **trivial but real design**, e.g. an 8-bit counter on `uo_out` enabled by `ui_in[0]`, with all outputs assigned and unused inputs in `_unused`.
5. Update the cocotb test in `test/` to check the counter through the pins only, so it is gate-level safe.
6. The folder layout below is the target. Each folder is created when its first real file lands, not as an empty placeholder (DECISIONS D-005):

```
src/                 RTL (tt_um_tripwire.v + trw_*.v later)
test/                pin-level cocotb tests (run in RTL + gl_test)
test_internal/       white-box tests (RTL only)
formal/              SymbiYosys jobs and properties
spec/tripwire.yaml   the single source of formats/ISA (phase 1)
tools/               gen/, tripsim/, tripc/, host/
programs/            protocol sources (.trw)
macro/               SRAM macro views (phase 1)
docs/design/         OVERVIEW_TRIPWIRE, ARCHITECTURE, VERIFICATION, PHYSICAL_DESIGN_AND_CI, phases/
docs/reports/        AREA.md, VERIFICATION_REPORT.md (later)
docs/BUGS.md  docs/DECISIONS.md  docs/CLAIMS.md  docs/WORKLOG.md
```

7. Append the TRIPWIRE lines to `.gitignore`: local build, simulation and formal output, and waveforms are never committed.
8. Add the gds trigger `paths` filter and `concurrency` block (`../PHYSICAL_DESIGN_AND_CI.md` §6). Leave the template's jobs untouched.
9. Enable **GitHub Pages**: Settings → Pages → Source = **GitHub Actions**.

### 2.2 First CI run
10. Push and watch:
   - `test`
   - `docs`
   - `gds` (gds, precheck, gl_test, viewer)
11. Trigger `fpga` manually once to see whether the trivial design builds.
12. Record the first row in `docs/reports/AREA.md`: cells, utilisation, slack and gds wall time.

### 2.3 Local toolchain (WSL)
13. Install the OSS CAD Suite (Icarus, Verilator 5, Yosys, SymbiYosys with Yices/Boolector) and Python 3.11+ with `cocotb`, `pytest`, `pyuvm`, `cocotb-coverage`, `hypothesis`, `pyyaml`.
14. Install `sigrok-cli` (with libsigrokdecode). Check that `sigrok-cli -L` lists the `uart`, `spi` and `i2c` decoders.
15. Write `scripts/check_all.sh`. It runs lint, the pin-level tests and the internal tests locally in one command.
16. Optional: pull the iic-osic-tools Docker image for local LibreLane runs later.

### 2.4 Competition and team
17. Submit the Jane Street sign-up form.
18. Email asic-competition@janestreet.com asking:
    - (a) is 8x4 available, or should we design for 6x4;
    - (b) are IHP SRAM macros accepted on the target shuttle.

    Log the answers in `DECISIONS.md`.
19. Assign roles. The verification lead **does not write RTL**.
    - architecture/RTL
    - verification
    - compiler/tools
    - physical/CI
20. Start `docs/DECISIONS.md` (entry D-001: the chosen architecture, TRIPWIRE) and `docs/BUGS.md`.
21. Commit the four design docs to `docs/design/`.

---

## 3. Deliverables
- Public repo with the layout above and the trivial design.
- A green run of every workflow, and a working Pages viewer URL.
- `docs/reports/AREA.md` row 1; `DECISIONS.md` D-001 and the Jane Street questions.
- `scripts/check_all.sh` working locally.

---

## 4. Phase exit checklist (all must pass)
- [x] Repo public; top module is `tt_um_tripwire`; `info.yaml` says `tiles: "6x4"`, 50 MHz. *(Evidence: GitHub API `private: false` for Kanishk234/protocol-emulator-asic; `info.yaml` and `src/tt_um_tripwire.v` at 0786358.)*
- [x] `test` workflow green on the trivial design. *(Evidence: run 35821375912 on 0786358, and every push since.)*
- [x] `docs` workflow green. *(Evidence: run 35822749773 on bff60b5, 2026-09-23.)*
- [ ] `gds` workflow: `gds`, `precheck`, `gl_test` and `viewer` all green.
- [x] **GitHub Pages shows the GDS viewer** at the repo's Pages URL. *(Evidence: https://kanishk234.github.io/protocol-emulator-asic/ serves the TT 3D viewer; deployed by `viewer` in gds run 35821375890, 2026-09-23.)*
- [x] `fpga` workflow has been run once manually; result recorded (green, or the reason it isn't). *(Evidence: run 35823310537 on 9fdcf93, green, 2026-09-23.)*
- [x] gds trigger `paths` filter in place: a docs-only push does **not** start a hardening. *(Evidence: the push ending at bff60b5 touched only `docs/` and `scripts/`; it ran `test` 35822749744 and `docs` 35822749773, and no `gds` run. The running `gds` 35821375890 was not cancelled.)*
- [x] Local `scripts/check_all.sh` passes in WSL; `sigrok-cli` decodes a UART test VCD. *(Evidence: `scripts/check_all.sh` → `check_all: PASS`, 4/4 tests, 2026-09-23; `scripts/sigrok_smoke.py` → sigrok `uart` decoded "TRIPWIRE".)*
- [x] Jane Street sign-up form submitted; tile-size and SRAM questions emailed, **or deferred with a `DECISIONS.md` entry** (wording changed 2026-09-23, team decision). *(Evidence: form submitted 2026-09-23; D-003 records the deferral: design for 6x4, SRAM settled by risk spike R3.)*
- [x] Roles assigned and written in the README. *(Evidence: README "Contributors" lists Kanishk and Krithik. Team decision 2026-09-23: contributors only, no per-role split for now.)*
- [x] `DECISIONS.md`, `BUGS.md`, `CLAIMS.md`, `WORKLOG.md`, `docs/reports/AREA.md` exist; `.gitignore` excludes build/sim/formal output. *(Evidence: files in `docs/` and `docs/reports/`, 2026-09-23; `.gitignore` covers `build/`, `sim_build/`, `logs/`, `*.vcd`, `*.fst`, `formal/*/`, `.venv/`.)*

## 5. Risks in this phase
| Risk | Response |
|---|---|
| The first `gds` run fails on template settings | Compare against the untouched template; don't change `config.json` yet |
| Pages deploy fails | Check the Source setting and the workflow permissions; re-run `viewer` |
| Tool versions differ between WSL and CI | Pin the Python package versions in `test/requirements.txt`; note the OSS CAD Suite date |