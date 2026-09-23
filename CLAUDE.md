# CLAUDE.md: TRIPWIRE

## Project goal
TRIPWIRE is our entry to the **Jane Street Protocol Emulator ASIC Competition**. It is an open-source, firmware-programmable chip that emulates hardware protocols (UART, SPI and I2C required; more as stretch goals) on **Tiny Tapeout, IHP 130 nm CMOS5L, 6x4 tiles**. **Deadline: 2027-01-18** (we target Jan 11).

Architecture in one line: lanes of **triggered "reflex" instructions** (no program counter on the fast path), plus bounded **routines** in SRAM, connected by a **multicast channel fabric**, with **timed pin units** at the pads.

## Key sources
- Competition brief: https://blog.janestreet.com/protocol-emulator-asic-competition/
- Template (our starting point): https://github.com/TinyTapeout/ttihp-verilog-template/tree/cmos5l
- Tiny Tapeout docs: https://tinytapeout.com
- SRAM on IHP (reference project): https://www.tinytapeout.com/chips/ttihp0p2/tt_um_urish_sram_test
- Contact: asic-competition@janestreet.com

## Read before working
0. `docs/WORKLOG.md`: the latest entries, to see where the last session stopped.
1. `docs/design/OVERVIEW_TRIPWIRE.md`: what we're building and why, protocols, schedule.
2. The current phase doc in `docs/design/phases/`: find the first unchecked box.
3. `docs/design/ARCHITECTURE.md`: the hardware contract. RTL and model both follow it.
4. `docs/design/VERIFICATION.md`: layers, check IDs, tools.
5. `docs/design/PHYSICAL_DESIGN_AND_CI.md`: TT flow, SRAM macro, routing limits, workflows.
6. The latest entries in `docs/DECISIONS.md` and `docs/BUGS.md`.

## Phase gates (hard rules)
- Work in phase order: 0 setup → 1 spec/model/risks → 2 RTL core → 3 showcase protocols → 4 stretch + freeze → 5 evidence/docs → 6 submission. Phase 7 (hardware) is optional and off the critical path.
- **A phase is complete only when every item in its "Phase exit checklist" passes.** Do not start the next phase's tasks until then. If an item cannot pass, stop and explain why, then propose a fix or a fallback. Never tick a box that hasn't actually passed.
- Tick checklist boxes only with evidence (a test run, a CI run ID, a proof log, or a file) noted next to the box.
- Every phase ends with all CI workflows green on `main`.
- **End every session with a `docs/WORKLOG.md` entry**: what was done, which boxes were ticked (with evidence), and the next step.

## Engineering rules
- **The spec wins.** If the RTL and `ARCHITECTURE.md` disagree, fix the RTL. If the spec is wrong, propose the change in `docs/DECISIONS.md` and ask before implementing.
- **One source for encodings:** `spec/tripwire.yaml`. Generated files are regenerated, never hand-edited.
- **Keep model and RTL independent:** when writing `tools/tripsim`, don't read `src/`; when writing RTL, don't read `tools/tripsim`. Tests may use both.
- **Verilog:** Verilog-2005 subset that Icarus, Verilator, Yosys and LibreLane all accept.
  - `default_nettype none`; synchronous active-low reset; no `initial` in synthesisable code.
  - Latches only in `trw_slots.v`; one module per file; `trw_` prefix; top level `tt_um_tripwire`.
- **Tests in `test/` touch only top-level ports.** They also run on the gate-level netlist (`gl_test`). White-box tests go in `test_internal/`.
- **Logs:** don't commit raw logs, waveforms or build/formal output (they're in `.gitignore`; CI keeps them as artifacts). Commit summaries with CI run IDs in `docs/reports/`.
- **Log every bug** in `docs/BUGS.md`: symptom, root cause, the check that caught it, the check that now covers it.
- **Honesty:** claims go in `docs/CLAIMS.md` with their evidence. Never claim zero latency, sub-ns timing, USB/Ethernet support, real-hardware testing (we have none yet), or "formally verified" without naming the property and its bound.

## CI rules
- Workflows: `test`, `gds` (gds, precheck, gl_test, viewer → GitHub Pages), `docs`, `fpga` (manual), plus our own `lint`, `unit`, `formal`, `nightly`.
- Never edit the template's jobs. Only the `gds` trigger block (paths filter, concurrency) is ours. Add new workflows as separate files.
- Edit `src/config.json` only for `CLOCK_PERIOD`, `PL_TARGET_DENSITY_PCT` and the SRAM macro block, each with a DECISIONS entry.
- Hardening takes ~4–5 h and GitHub's limit is 6 h. Make **one hardware change per hardening**, and judge changes by global-routing overflow, not cell count. A push touching `src/`, `info.yaml` or `macro/` cancels a running hardening.
- Keep `info.yaml` `source_files` and `test/Makefile` `PROJECT_SOURCES` in sync.

## Git rules
- **Claude never runs `git commit`, `git push` or any other command that changes the repository history or the remote.** Claude may *provide* the exact commands; **the user runs them**.
- Commit per file group (e.g. RTL, tests, docs, tools, CI), not everything at once.
- Commit messages: short, imperative, one line, scoped. Examples:
  - `rtl: add channel producer/port`
  - `test: uart pin-level tests`
  - `docs: phase 1 checklist updates`
  - `ci: gds trigger paths filter`
- Before suggesting a push during a hardening run, remind the user to check `git log origin/main..main -- src info.yaml macro`.

## Environment
- Development in **WSL (Ubuntu)** with the OSS CAD Suite (Icarus, Verilator 5, Yosys, SymbiYosys) and Python 3.11+ (cocotb, pyuvm, cocotb-coverage, hypothesis, pyyaml, pytest), plus `sigrok-cli`.
- **Python always runs in the project venv.** Activate `.venv` (`source .venv/bin/activate`) before running any Python, pip, pytest, cocotb or `make` in `test/`. Never install packages into the system Python. Create or refresh the venv with `scripts/setup_venv.sh`; pin new packages in `requirements-dev.txt` (or `test/requirements.txt` if CI's `test` job needs them).
- OSS CAD Suite lives at `~/oss-cad-suite`; its `bin` is **appended** to PATH so the system Icarus (the one CI uses) stays first (DECISIONS D-004).
- One local command runs lint and all simulation tests: `scripts/check_all.sh`.
- No lab hardware is available at the moment. Everything is verified in simulation and formal.