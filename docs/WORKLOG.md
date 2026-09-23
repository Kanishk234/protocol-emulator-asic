# TRIPWIRE work log

Newest entry at the top. One entry per work session.
- Keep entries short.
- Evidence means a CI run ID, a test command and its result, or a file path.
- Raw logs are not committed; link to them instead.

Template:

```
## YYYY-MM-DD: <who> (phase N)
Done:
- ...
Checklist boxes ticked (evidence):
- [x] <item>: <CI run #/command/file>
Problems / decisions:
- ... (DECISIONS D-xxx, BUGS #x)
Next:
- ...
```

---

## 2026-09-23: Krithik + Claude (phase 0)
Done:
- Top module renamed to `tt_um_tripwire` (`src/tt_um_tripwire.v`); trivial design = 8-bit counter on `uo_out`, enabled by `ui_in[0]`.
- `info.yaml` filled (title, authors Kanishk and Krithik, 50 MHz, 6x4, placeholder pinout); `test/Makefile` and `test/tb.v` updated.
- `test/test.py`: 4 pin-level tests (reset, count, hold, wrap), gate-level safe (relative counts only).
- `gds.yaml` trigger: `paths` filter (`src/**`, `info.yaml`, `macro/**`, the workflow) + `concurrency` cancel-in-progress. Template jobs untouched.
- Folder skeleton created, then removed at the team's request: folders now appear with their first real file (D-005).
- `docs/DECISIONS.md` (D-001..D-005 + open spec questions Q1–Q6 for the P1 freeze), `BUGS.md`, `CLAIMS.md`, `docs/reports/AREA.md`.
- Local loop: `.venv` via `scripts/setup_venv.sh` (versions pinned in `requirements-dev.txt`); OSS CAD Suite 20260914 appended to PATH in `~/.bashrc`; `scripts/check_all.sh` (L0-TT source sync, Verilator lint, Yosys synth/no-latch, cocotb suite).
- CLAUDE.md: venv rule added.

Checklist boxes ticked (evidence):
- [x] Ledgers exist and `.gitignore` excludes build/sim/formal output: files in `docs/`.
- [x] `docs` workflow green: run 35822749773 (bff60b5).
- [x] gds paths filter works: docs/scripts-only push (bff60b5) started no `gds` run; `gds` 35821375890 kept running.
- [x] `check_all.sh` passes and sigrok decodes a UART VCD: `check_all: PASS` (4/4 tests; an injected "ignore enable" bug made 1 test fail), `sigrok_smoke.py` ok.

- After the first push (commit 0786358): `test` green (run 35821375912); `docs` red on every push so far (run 35821375894). Cause: TT `--check-docs` rejects the template placeholder text in `docs/info.md`. Filled in `docs/info.md` for the placeholder counter; `tt_tool.py --check-docs` now passes locally.
- `scripts/sigrok_smoke.py`: writes a UART 8N1 VCD and checks that `sigrok-cli`'s `uart` decoder returns "TRIPWIRE"; added to `check_all.sh`. `check_all.sh` → PASS.

- `docs/design/ISA.md` written early (D-006 exception): research on PIO, PRU, Loom, FlexIO, P2 smart pins, XMOS, PSoC UDB and Triggered Instructions; one shared op table, implicit readiness checks, flag result from every op, K constants, head-bit test (D-007); Q1–Q6 given proposed resolutions. `ARCHITECTURE.md` §5.2/5.3/6.1 now point to it.
- Phase 1 reordered to model-first (D-008); phase 1 doc updated.
- Honesty fixes: V1 relabelled `[OURS]` (a Hardcaml entry already bounds pin timing statically); survey count marked stale; Loom's utilisation corrected to 78.8% (was ~51%).

Problems / decisions:
- D-002 keeps `tt_um_tripwire` despite TT's uniqueness advice; rename path noted.
- `sigrok-cli` not installed yet (needs sudo).

Next:
- User: `sudo apt install sigrok-cli`; commit and push (triggers first `test`, `docs`, `gds`); enable Pages (Source = GitHub Actions); run `fpga` once by hand; confirm the repo is public.
- User: Jane Street sign-up form + email (D-003); assign roles (then Claude writes them into the README).
- Claude: sigrok UART VCD decode check in `check_all.sh`; record CI results and AREA row 1.

## 2026-09-22: team (phase 0, not started)
Done:
- Research and idea selection (TRIPWIRE).
- Design docs written: `docs/design/` (overview, architecture, verification, physical design & CI, phase 0–7 docs).
- `CLAUDE.md` created.
- Template (cmos5l branch) cloned locally in WSL.

Checklist boxes ticked (evidence):
- none yet

Next:
- Phase 0, task 1: create the GitHub repo from the local template clone, rename the top module to `tt_um_tripwire`, commit the docs.