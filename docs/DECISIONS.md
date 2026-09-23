# TRIPWIRE decisions

Newest at the bottom. Each entry: date, decision, reason, alternatives, status.
A spec change is proposed here first and implemented only after the team agrees.

---

## D-001 (2026-09-22): architecture is TRIPWIRE
- **Decision:** build TRIPWIRE: triggered reflex lanes (no program counter on the fast path), SRAM routines, a multicast channel fabric and timed pin units. See `design/OVERVIEW_TRIPWIRE.md` and `design/ARCHITECTURE.md`.
- **Reason:** novel in the field (triggered execution and the multicast fabric), with a fixed, provable pin-to-pin reaction time and program-level static checks.
- **Alternatives:** PIO-style state machines, a barrel CPU (both well covered by other entries).
- **Status:** accepted.

## D-002 (2026-09-23): top module name `tt_um_tripwire`
- **Decision:** keep `tt_um_tripwire` as the top module.
- **Reason:** team choice; matches the project name.
- **Risk:** Tiny Tapeout asks for a unique name, usually by including the GitHub username. If the shuttle reports a clash, rename to `tt_um_<username>_tripwire` (a mechanical change: `src/`, `info.yaml`, `test/tb.v`).
- **Status:** accepted.

## D-003 (2026-09-23): questions to Jane Street (tile size, SRAM macro)
- **Questions:** (a) is 8x4 available, or should we design for 6x4; (b) are IHP SRAM macros accepted on the target shuttle.
- **Assumption until answered:** 6x4 with the 512x16 SRAM macro, keeping the flop-store fallback (`design/PHYSICAL_DESIGN_AND_CI.md` §3).
- **Status:** Jane Street sign-up form submitted (2026-09-23). Team decision (2026-09-23): **design for 6x4**; the tile question is not being asked for now. The SRAM question is also open. Until answered, the macro is assumed usable, and risk spike R3 (phase 1) proves or disproves it through the real flow, with the flop-store fallback kept.

## D-004 (2026-09-23): local toolchain
- **Decision:**
  - Python always runs from the project venv `.venv` (`scripts/setup_venv.sh`); packages pinned in `requirements-dev.txt` and `test/requirements.txt`.
  - OSS CAD Suite build 20260914 at `~/oss-cad-suite`, its `bin` **appended** to PATH (Verilator 5.053, Yosys 0.69, SymbiYosys, Yices, Boolector, Bitwuzla, mcy).
  - Icarus Verilog is the system package (12.0), the same one the CI `test` job installs from apt; appending the suite keeps it first on PATH.
- **Reason:** local results should match CI; the venv keeps the system Python clean.
- **Status:** accepted.

## D-005 (2026-09-23): no placeholder folders
- **Decision:** `spec/`, `tools/`, `programs/`, `test_internal/`, `formal/` and `macro/` are created when their first real file is added, not up front with placeholder READMEs. The target layout stays as listed in `design/phases/PHASE0_SETUP.md` task 6.
- **Reason:** keep the repo free of empty scaffolding; the layout is not a phase 0 exit item.
- **Note:** `macro/` is in the `gds` trigger paths, so adding it starts a hardening.
- **Status:** accepted.

## D-006 (2026-09-23): phase-gate exception for `ISA.md`
- **Decision:** start `docs/design/ISA.md` (a phase 1 spec task) before the phase 0 exit checklist is complete.
- **Reason:** the remaining phase 0 items are waiting on CI (`gds`, `viewer`/Pages), manual steps (`fpga` run, Jane Street form/email, roles) or a push; none needs design work. Team decision (Krithik).
- **Scope:** design documentation only. No RTL, model, compiler or `spec/tripwire.yaml` work until phase 0 exits. Phase 0 boxes are still ticked only with evidence.
- **Status:** accepted.

## D-007 (2026-09-23): ISA revision in `docs/design/ISA.md`
- **Decision (draft, to be confirmed by the model, D-008):**
  1. **One operation table for reflexes and routines.** Routines keep only sequencing, memory, output and flag instructions of their own. Drops the separate LC-3-style routine op set; resolves Q5.
  2. **Implicit readiness checks.** Reading an input head implies "available", writing an output implies "free", and CALL implies "RB = 0" (as in Triggered Instructions). Removes the `IN`/`OUT` condition fields and the read-without-check bug class.
  3. **Every op produces a flag result** (zero, or the compare/parity/less-than result), written when `DFE` is set. `CMPEQ` and `TSTZ` become `XOR`/`AND` with a zero result; the freed codes go to `LTU` and a reserved OP 15.
  4. **Per-lane constants K0–K3** (host-written while halted, usable as B and as CMPM operands).
  5. **Head `data[15]` test in conditions** (`HE/HV`). EVENT tokens carry their kind/polarity in `data[15]` (START vs STOP, rising vs falling).
  6. Slot grows from 51 to 52 bits; separate `OT`/`KT` tag fields; DST 7 reserved; `MKCTL` passes `A[11:0]`.
- **Reason:** research on PIO, PRU, Loom, FlexIO, Propeller 2 smart pins, XMOS, PSoC UDB and Triggered Instructions (sources in `ISA.md` §10). The protocol-specific work belongs in pin units, conditions and the fabric; the op table should be small and shared.
- **Also resolves:** Q1 (urgent slots pre-empt a waiting routine step; non-urgent ones wait at most 1 clock), Q2, Q3, Q4, Q6. See `ISA.md` §8.
- **Status:** accepted as the working draft (team: "make the best choices for now").

## D-008 (2026-09-23): phase 1 is model-first
- **Decision:** reorder phase 1: `ISA.md` draft → `tripsim` (parameterized, cycle-accurate from the start) + a minimal assembler → protocol kernels → measure and ablate (`ISA.md` §9) → freeze `spec/tripwire.yaml`. The same `tripsim` then becomes the golden model for lockstep.
- **Reason:** slot count, register count, OP 15 and the D-007 features are questions only numbers from real protocol programs can answer; freezing first would lock in guesses. Writing the model cycle-accurate from day one avoids a second model, and RTL independence is unaffected (no RTL exists yet).
- **Scope:** still phase 1 work; it starts when phase 0 exits (D-006 covers only `ISA.md`).
- **Status:** accepted (team).

---

## Open questions for the phase 1 spec freeze
Q1–Q6 below have **proposed resolutions** in `design/ISA.md` §8 (D-007). They close at the spec freeze once the model confirms them.

Found while reading the design docs; to be settled in `ARCHITECTURE.md` during P1.
- **Q1: routine steps vs. reflexes.** §6.2 says a routine step runs only on a clock when *no* reflex fires; §6.3 and the overview say *urgent* reflexes interrupt routines. What exactly does `U=0` block while RB is set?
- **Q2: CALL is encoded twice**, as `OP=15` and as `DST=7`. Keep one.
- **Q3: `MKCTL` cannot build `LEVEL 1` / `OE 1`.** MKCTL (§5.3) produces `{IMM[7:4], 0, A[10:0]}`, forcing data bit 11 to 0, but the pin-unit `LEVEL` and `OE` ops (§7.3) take their value from bit 11. Options: pass `A[11:0]` through, or take bit 11 from an IMM bit.
- **Q4: routine B format is too narrow.** `cond[11:9]` is 3 bits, but `BF f` / `BNF f` need a branch kind plus a 2-bit flag index, and `DJNZ r` needs a 2-bit register (§6.1). Needs at least 4 bits, or fewer branch kinds / flags.
- **Q5: routines have no compare or bitfield ops.** §4.4 of the overview says routines use the same operations as reflexes, but the R format only covers ops 0–7. There is no `CMPEQ`/`CMPM`/`TSTZ`/`PAR`/`EXT`/`SHOR` in routines, so a routine cannot set a flag from data. The 16 routine opcodes are all used, so adding these needs a sub-opcode field or dropping something.
- **Q6: `OTAG` shares bits with the immediate.** With `OTAG=1` the output tag comes from `IMM[7:6]`, so a slot that emits a CTRL/EVENT/ERR token with `BSEL=1` is limited to immediates 0–63. Decide whether that is acceptable or give the tag its own bits (the slot is 51 bits in a 64-bit host word space, so there is room).
