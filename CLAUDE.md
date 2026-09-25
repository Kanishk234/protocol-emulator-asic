# CLAUDE.md: WARP

> Project name: WARP (in weaving, the warp is the set of lengthwise threads a fabric is woven on). RTL prefix `wp_`, top module `tt_um_warp`.

## Project goal
WARP is our entry to the **Jane Street Protocol Emulator ASIC Competition**. It is an open-source, reprogrammable chip that emulates hardware protocols (UART, SPI and I2C required; more as stretch goals) on **Tiny Tapeout, IHP 130 nm CMOS5L, 6x4 tiles**. **Deadline: 2027-01-18** (we target Jan 11).

Architecture in one line: a small **embedded FPGA fabric specialized for protocol emulation**, built on FABulous, behind a fixed management shell. Users write synthesizable Verilog, compile it to a bitstream on a host computer, and load it through the shell. Every soft and hard resource (LUT size, flip-flops per cell, hard blocks, I/O cells, configuration storage, routing) is chosen from **measurements of real protocol workloads**, and generality is tested on a **sealed held-out protocol set**.

## Key sources
- Competition brief: https://blog.janestreet.com/protocol-emulator-asic-competition/
- Template (our starting point): https://github.com/TinyTapeout/ttihp-verilog-template/tree/cmos5l
- Tiny Tapeout docs: https://tinytapeout.com
- FABulous docs: https://fabulous.readthedocs.io/ and repo: https://github.com/FPGA-Research/FABulous
- Tiny FABulous (eFPGA on Tiny Tapeout, SKY130; reference and prior art): https://github.com/mole99/tt-fabulous-sky-26a
- PRISM (Verilog-programmed protocol engine on IHP; prior art): https://tinytapeout.com/chips/ttihp26b/tt_um_pettit_prism_lite
- SRAM on IHP (reference project): https://www.tinytapeout.com/chips/ttihp0p2/tt_um_urish_sram_test
- Contact: asic-competition@janestreet.com

## Read before working
0. `docs/WORKLOG.md`: the latest entries, to see where the last session stopped.
1. `docs/design/OVERVIEW.md`: what we're building and why, protocols, schedule, decision points.
2. The current phase doc in `docs/design/phases/`: find the first unchecked box.
3. `docs/design/ARCHITECTURE.md`: the hardware contract (shell, host interface, fabric resources). RTL, fabric definition and models all follow it.
4. `docs/design/VERIFICATION.md`: layers, check IDs, tools.
5. `docs/design/PHYSICAL_DESIGN_AND_CI.md`: TT flow, fabric hardening, routing limits, workflows.
6. The latest entries in `docs/DECISIONS.md` and `docs/BUGS.md`.

## Phase gates (hard rules)
- Work in phase order: 0 setup → 1 profile/specify/de-risk → 2 baseline fabric + shell → 3 specialize, compare, hardware freeze → 4 protocols, showcase, held-out evaluation → 5 evidence/docs → 6 submission. Phase 7 (hardware prototyping) is optional and off the critical path.
- **A phase is complete only when every item in its "Phase exit checklist" passes.** Do not start the next phase's tasks until then. If an item cannot pass, stop and explain why, then propose a fix or a fallback. Never tick a box that hasn't actually passed.
- Tick checklist boxes only with evidence (a test run, a CI run ID, a proof log, a report, or a file) noted next to the box.
- Every phase ends with all CI workflows green on `efpga` (WARP's branch; `main` holds the separate TRIPWIRE design).
- **End every session with a `docs/WORKLOG.md` entry**: what was done, which boxes were ticked (with evidence), and the next step.
- **End every phase with a plain-language summary** in `docs/summaries/PHASE<N>.md` (goal, what we did, what we found, what's left, one-line takeaway), written for someone who wasn't there. Keep in-progress summaries current at major milestones.

## Architecture rules
- **Domain-specific, protocol-agnostic (DECISIONS D-002).** No dedicated protocol blocks (no hard UART, SPI or I2C controller). Hard blocks and special cells must be general primitives (e.g. timers, shift chains, CRC/LFSR, edge detectors, FIFOs) that help more than one protocol. Protocol behavior lives in the user bitstream. Every hard block or cell change needs a DECISIONS entry stating: the profiling data behind it, which protocols benefit, its area cost, and what it costs protocols that don't use it.
- **The held-out set stays sealed (D-003).** The list is in `docs/design/HELDOUT.md`. Until the hardware freeze at the end of phase 3, do not write RTL for, profile, or tune the architecture against held-out protocols. If one is touched early, log it in DECISIONS and move it to the design set.
- **Compare at equal area (D-004).** Any claim that one variant beats another must compare them at equal total area (fabric, configuration storage, routing and shell included) and the same clock target.
- **A block is done only when the tools can use it.** Yosys must map to it, place-and-route must place and route it, the bitstream must configure it, and a test must show a compiled user design using it after loading through the real interface.
- **Configuration survives synthesis.** Never tie configuration bits to constants in the chip build. Gate-level tests load real bitstreams.

## Engineering rules
- **The spec wins.** If the RTL and `ARCHITECTURE.md` disagree, fix the RTL. If the spec is wrong, propose the change in `docs/DECISIONS.md` and ask before implementing.
- **One source for the fabric:** `arch/` holds the fabric definition and our primitive definitions. Generated fabric RTL (`src/fabric_gen/`) and generated tool files are regenerated, never hand-edited.
- **Upstream code:** pinned versions live in `third_party/` (or are pinned in requirements) and are never edited in place. Our changes go in `patches/`, each with a DECISIONS entry. Keep upstream license files and attribution.
- **Keep models and RTL independent:** when writing a reference model in `tools/refmodels/`, don't read the RTL it checks; when writing RTL, don't read its reference model. Tests may use both.
- **Verilog:** Verilog-2005 subset that Icarus, Verilator, Yosys and LibreLane all accept.
  - `default_nettype none`; synchronous active-low reset; no `initial` in synthesisable code.
  - Latches only in configuration storage (generated, or `wp_cfg_*` modules); one module per file; `wp_` prefix; top level `tt_um_warp`.
- **Protocol user designs** (the Verilog users compile to bitstreams) live in `protocols/<name>/`, with a README stating the scope, rates and known limits.
- **Tests in `test/` touch only top-level ports.** They also run on the gate-level netlist (`gl_test`). White-box tests go in `test_internal/`.
- **Logs:** don't commit raw logs, waveforms, bitstreams from CI, or build/formal output (they're in `.gitignore`; CI keeps them as artifacts). Commit summaries with CI run IDs in `docs/reports/`.
- **Log every bug** in `docs/BUGS.md`: symptom, root cause, the check that caught it, the check that now covers it.
- **Honesty:** claims go in `docs/CLAIMS.md` with their evidence. Never claim:
  - USB or Ethernet support, real-hardware testing (we have none yet), or "formally verified" without naming the property and its bound;
  - any area, timing, clock or protocol-rate number without the run ID that produced it;
  - that the fabric beats a CPU/PIO-style design, or a generic fabric, without an equal-area measurement;
  - that the architecture is "general" beyond what the held-out results show;
  - "first" or "novel" without checking prior art (Tiny FABulous, PRISM, FABulous IHP tapeouts).

## CI rules
- Workflows: `test`, `gds` (gds, precheck, gl_test, viewer → GitHub Pages), `docs`, `fpga` (manual) from the template, plus our own `lint`, `unit`, `fabric` (compile every protocol to a bitstream and run it on the fabric simulation), `formal` and `nightly`.
- Never edit the template's jobs. Only the `gds` trigger block (paths filter, concurrency) is ours. Add new workflows as separate files.
- Edit `src/config.json` only with a DECISIONS entry for each change.
- Hardening can take hours and GitHub stops any single job at 6 h. Record our actual hardening time in `docs/design/PHYSICAL_DESIGN_AND_CI.md` and update it when it changes. Make **one hardware change per hardening**, and judge changes by global-routing overflow and congestion, not cell count (an FPGA fabric is routing-heavy).
- If the `gds` workflow uses cancel-in-progress concurrency, a push touching `src/`, `info.yaml`, `arch/` or `macro/` cancels a running hardening.
- Keep `info.yaml` `source_files` and `test/Makefile` `PROJECT_SOURCES` in sync.

## Git rules
- **Claude never runs `git commit`, `git push` or any other command that changes the repository history or the remote.** Claude may *provide* the exact commands; **the user runs them**.
- Commit per file group (e.g. RTL, arch, protocols, tests, docs, tools, CI), not everything at once.
- Commit messages: short, imperative, one line, scoped. Examples:
  - `rtl: add loader checksum`
  - `arch: add timer primitive`
  - `protocols: uart rx user design`
  - `test: uart bitstream pin-level tests`
  - `docs: phase 1 checklist updates`
  - `ci: gds trigger paths filter`
- Before suggesting a push during a hardening run, remind the user to check `git log origin/efpga..efpga -- src info.yaml arch macro`.

## Environment
- Development in **WSL (Ubuntu)** with the OSS CAD Suite (Icarus, Verilator 5, Yosys, nextpnr, SymbiYosys) and Python 3.11+ (cocotb, pytest, pyyaml, hypothesis), plus `sigrok-cli`. FABulous and its tool dependencies are pinned to the versions recorded in `docs/VERSIONS.md`.
- **Python always runs in the project venv.** Activate `.venv` (`source .venv/bin/activate`) before running any Python, pip, pytest, cocotb, FABulous or `make` in `test/`. Never install packages into the system Python. Create or refresh the venv with `scripts/setup_venv.sh`; pin new packages in `requirements-dev.txt` (or `test/requirements.txt` if CI's `test` job needs them).
- Local simulator versions must match the ones CI uses; the PATH order that achieves this is recorded in DECISIONS during phase 0.
- One local command runs lint and all simulation tests: `scripts/check_all.sh`.
- Gate-level locally, the way CI's `gl_test` does it: `scripts/gl_local.sh`.
- No lab hardware is available at the moment. Everything is verified in simulation and formal.