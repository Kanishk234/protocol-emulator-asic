# TRIPWIRE: verification plan

This document covers:
- what is new in how TRIPWIRE is verified;
- the tools and why each was chosen;
- the models and testbench structure;
- every verification layer, with check IDs;
- the formal property list, coverage goals and CI integration;
- the rules that keep the evidence trustworthy.

Companions: `OVERVIEW_TRIPWIRE.md` (overview and schedule) and `ARCHITECTURE.md` (the design being verified; section numbers below refer to it).

**Constraint:** the team has **no lab hardware**. Everything is verified in simulation and formal proof, and the write-up says so plainly. The TT `fpga` workflow only builds a bitstream.

---

## 1. Novelties in verification

| # | Technique | Status in the field | What it gives us |
|---|---|---|---|
| V1 | **Checking programs before they load.** The compiler checks every program: routine worst-case length, reaction bound for every urgent reflex, slot/SRAM usage, and **no deadlock / no overrun** for fixed-rate channel graphs. | Timing bounds alone are not new: a Hardcaml entry bounds pin-edge timing by abstract interpretation. Graph-level deadlock/overrun checking across the fabric is ours | Guarantees about the *firmware*, not only the chip. Only possible because a TRIPWIRE program is an explicit graph |
| V2 | **Formal proofs of the channel fabric**: no loss, duplication or reordering on blocking paths; multicast consistency; taps never block | New (the fabric itself is new) | The multicast network is trustworthy by proof |
| V3 | **Formal proofs of the reflex scheduler**: 7-clock pin-to-pin bound, pending-flag rule, rotation fairness, lane isolation | New to the competition (others prove ISA decode/ISA semantics) | The headline timing claim is proven, not just measured |
| V4 | **Program-specific formal checks**: the RTL is checked *with each shipped protocol program loaded*, confirming the compiler's V1 report on real hardware | Our method | Closes the gap between "the compiler says" and "the chip does" |
| V5 | **Independent oracles**: sigrok protocol decoders on every waveform; real-world captures from `sigrok-dumps` replayed into our receivers; third-party RTL cores as the other device | New to the competition | Catches misreadings of a spec that our own model shares with our RTL |
| V6 | **Metamorphic testing**: relations that must hold (loopback identity, time scaling, lane permutation, idle insertion) | New to the competition | Finds bugs without needing a correct expected answer |
| V7 | **Measured AI-assisted verification**: AI-written tests and code are logged; a separate verification author (human or agent) who never saw the RTL writes the model; test quality is scored by mutation kill rate | Several entries use AI; none measure it | Answers Jane Street's explicit interest in AI-assisted verification with evidence |

**Table stakes we also do** (match the field, don't claim as new):
- golden-model lockstep
- constrained-random stimulus
- unit tests
- gate-level tests
- lint
- mutation testing
- a bug ledger
- a claims table

---

## 2. Tools

| Purpose | Tool | Why |
|---|---|---|
| RTL simulation (default, and what TT CI runs) | **Icarus Verilog** | The template's `test` workflow uses it; gate-level `gl_test` uses it |
| Fast simulation for long random runs | **Verilator 5** | ~10–100× faster for million-cycle lockstep and fuzzing |
| Testbench language | **cocotb** (Python) | The template's standard; Python lets the golden model, compiler and decoders live in the same process |
| Testbench structure | **pyuvm** (UVM in Python on cocotb) for the system-level environment; plain cocotb for unit tests | UVM gives agents, sequences and scoreboards. SystemVerilog UVM needs a commercial simulator (Icarus cannot run it, and Verilator's UVM support is too partial to rely on in CI), so pyuvm keeps UVM's structure on the free toolchain |
| Functional coverage | **cocotb-coverage** (covergroups/crosses in Python) | Coverage closure without commercial tools |
| Code coverage | Verilator `--coverage` (line/toggle) | |
| Property-based testing | **Hypothesis** (Python) | Random structured inputs with automatic shrinking to a minimal failing case |
| Formal | **SymbiYosys** + Yosys; engines `smtbmc` (Yices/Boolector) for BMC and cover, `abc pdr` for unbounded proofs | Open source; runs in CI |
| Mutation testing | **mcy** (YosysHQ) or a small in-house mutator | Measures whether the test suite would notice a broken RTL |
| Lint | Verilator `--lint-only -Wall`, Yosys `check` | |
| Protocol oracles | **sigrok-cli** + libsigrokdecode | Community decoders for UART, SPI, I2C, 1-Wire, CAN, PS/2, JTAG, SWD and more |
| Real-world stimulus | **sigrok-dumps** repository | Captures from real devices, replayed into our receivers |
| Third-party peers | Open-source Verilog cores, e.g. an I2C controller/target core and the OpenCores CAN controller (selection finalised in P1; licences checked) | Independent implementations of the same protocol |
| Waveforms | GTKWave / Surfer | |

---

## 3. What gets verified, as a map

```
          compiler (tripc)  ──V1 static checks──►  report: bounds, deadlock/overrun, usage
               │ images
               ▼
 ┌──────── golden model (tripsim, Python) ─────────┐        ┌──────── RTL (Verilog) ────────┐
 │ token-level, cycle-accurate, written from SPEC  │◄─L2───►│ lockstep compare every clock  │
 └─────────────────────────────────────────────────┘        └───────────────────────────────┘
                                                                   ▲         ▲         ▲
                        L1 unit tests (per block) ─────────────────┘         │         │
         L3/L3b protocol tests: pin agents + sigrok + third-party peers ─────┘         │
                     L5 formal (fabric, scheduler, isolation, program-specific) ───────┘
```

---

## 4. Models and tools we build

### 4.1 One ISA/format table, many outputs
The reflex slot format, routine ISA, token tags, pin-unit commands and host register map live in **one machine-readable table** (`spec/tripwire.yaml`). A generator produces:
- Verilog decode constants and field extractors;
- the compiler's encoder;
- the golden model's decoder;
- the tables in `ARCHITECTURE.md`;
- the formal decode properties.

Spec and implementation cannot drift silently. CI regenerates the outputs and fails on any diff.

### 4.2 Golden model: `tripsim`
- Python, **cycle-accurate at the token level**. It models every producer register, consumer port, lane EVAL/EXEC stage, the SRAM rotation, the pin-unit cursors and the pad synchronisers.
- Written from `ARCHITECTURE.md` and the YAML **by someone who does not read the RTL** (see §9).
- Exposes the same host API as the RTL testbench, so any test runs on both.
- Also serves as the fast "simulator" for firmware development before RTL exists.

### 4.3 Compiler: `tripc`
Compiles the TRIPWIRE language (channel graph, reflexes, routines, pin config) into slot images, SRAM contents and config writes. It emits the **V1 report**:
- worst-case routine steps;
- reaction bound for each urgent reflex, from the §5.5 latency and the priority structure;
- slot/SRAM usage;
- deadlock and overrun analysis for fixed-rate graphs: rates and buffer occupancy computed statically. Graphs with data-dependent rates get a warning, not a false guarantee.

### 4.4 Protocol reference models
Independent Python models of UART, SPI, I2C, 1-Wire, PS/2, WS2812, DShot (and CAN if built). Used as the other side of the wire in simulation. Written from the protocol specs, not from our firmware.

---

## 5. Testbench structure (pyuvm environment)

```
 tb_top (Verilog: DUT = tt_um_tripwire, pads looped to agents)
   └── pyuvm env
        ├── host_agent        SPI-slave driver/monitor: load images, run/halt/step, read debug, FIFOs
        ├── pin_agents[]      one per protocol under test: UART, SPI, I2C (controller & target),
        │                     1-Wire, PS/2, WS2812/DShot; each = driver + monitor + reference model
        ├── impairment        optional layer between agents and pads: clock skew (ppm), jitter,
        │                     glitches, slow open-drain rise (delayed release), contention
        ├── sigrok_checker    dumps pad activity to VCD, runs sigrok-cli decoders, parses results
        ├── model_scoreboard  runs tripsim in lockstep with the same stimulus; compares all
        │                     architectural state every clock (via debug taps in RTL sim only)
        └── coverage          cocotb-coverage covergroups (see §7)
```

**Two classes of tests**, because the TT `gl_test` runs the test suite on the gate-level netlist, where internal signals no longer exist:
- **Pin-level tests** (`test/`): drive and observe *only* the top-level ports (host SPI + protocol pins). These run in both RTL and gate-level CI.
- **White-box tests** (`test_internal/`): may probe internal signals (lockstep scoreboard, unit tests). RTL only, run by our own workflow.

---

## 6. Verification layers and check IDs

Every test and proof names the check ID it covers. A script lists which IDs have evidence (§8).

### L0: static
- **L0-LINT:** Verilator `-Wall` clean; latches only inside slot arrays (waived with reasons).
- **L0-SYNTH:** Yosys synth sanity: no undriven nets, no unintended latches, no combinational loops.
- **L0-GEN:** generated files match `spec/tripwire.yaml`.
- **L0-TT:** `info.yaml` source list matches `test/Makefile`; all outputs assigned.

### L1: unit (cocotb, white-box)

| ID | Block | Checks |
|---|---|---|
| L1-ALU | ALU | All 16 ops against a Python reference over random operands and edge cases (0, 0xFFFF, 0x8000, shift amounts 0–15) |
| L1-EVAL | Lane EVAL | Condition logic for every field combination; priority encoder picks the lowest true slot; pending-flag masking |
| L1-PIPE | Lane pipeline | Static STATE update visible next clock; dynamic flag +1 clock; output reservation prevents overflow |
| L1-CHAN | Producer/consumer | Handshake at every combination of 0–4 blocking + 0–2 tap subscribers; seq toggling; DROPPED counting |
| L1-OVR | Pin RX overrun | New token dropped, old kept, OVERRUN sticky |
| L1-PIN-TX | Pin TX | LEVEL/OE/GAP/SYNC/CLK/SETN; cursor arithmetic; LATE flag; fractional period mean and jitter (≤ 1 clock) over 4096 bits; PULSE t0/t1; open-drain never drives high; ownership |
| L1-PIN-RX | Pin RX | SHIFT_RX sample position, AUTOREARM back-to-back; LINKED_RX on rise/fall; EDGE_TS timestamps; COND_EDGE START/STOP |
| L1-CRC | CRC | ≥ 20 catalogued CRC-8/16 parameter sets vs a reference library, random messages |
| L1-MEM | MEM, CAPTURE | Address auto-increment, READ n; rotation slot usage; capture ring wrap |
| L1-ROT | SRAM rotation | Each requester gets exactly its slot; host writes only while halted |
| L1-HOST | Host SPI | Framing, auto-increment, CS abort mid-byte, dummy byte, every address space |

### L2: model lockstep (white-box, Verilator for long runs)
- **L2-RAND:** random legal programs (random slots, routines, fabric configs, pin configs) plus random pin stimulus. RTL and `tripsim` compared **every clock** on registers, STATE/FLAGS/PEND, RPC, producer registers and pad outputs. Target: 10⁸ compared clocks before freeze, zero divergences.
- **L2-INJECT:** deliberately injected bugs (a flipped priority, an off-by-one cursor) must be caught within the first seed; this checks the checker.
- **L2-HYP:** Hypothesis-driven programs with shrinking, so a failure becomes a minimal program.

### L3: protocol tests (pin-level; run in RTL and gate-level)

| ID | Protocol | Checks | Oracles |
|---|---|---|---|
| L3-UART | UART TX/RX 9600–1 Mbaud, 8N1/8E1 | Bytes round-trip; framing/parity errors reported; back-to-back frames | Reference model **and** sigrok `uart` |
| L3-SPI-C | SPI controller, modes 0–3, 8/16-bit | Full-duplex bytes; CS timing | Model + sigrok `spi` |
| L3-I2C-C | I2C controller 100k/400k/1M | Writes/reads, NACK, repeated START, clock stretching, arbitration loss | Model + sigrok `i2c` |
| L3-I2C-T | I2C target (EEPROM emulation) | Address match/ignore, pointer, sequential read/write, ACK deadline at 400k and 1M | Model + sigrok `i2c` + **third-party I2C controller RTL** |
| L3-SPI-T | SPI target (flash emulation) | READ/FAST_READ with dummy cycles, max SCK | Model + sigrok `spi`/`spiflash` |
| L3-1W | 1-Wire master (standard, overdrive) | Reset/presence, ROM commands | Model + sigrok `onewire_link`/`onewire_network` |
| L3-PS2 | PS/2 receive | Frames, parity | Model + sigrok `ps2` |
| L3-PULSE | WS2812/DShot | Pulse widths within spec tolerance | Timing checker |
| L3-CAN | CAN (stretch) | Frames, stuffing, CRC, arbitration between two nodes | Model + sigrok `can` + **OpenCores CAN RTL** |

### L3b: independent peers and real captures
- **L3B-PEER:** third-party RTL cores in the same simulation as the other device. Our traffic must be accepted by them, and theirs by us.
- **L3B-DUMPS:** `sigrok-dumps` captures (real devices, real timing imperfections) replayed onto our RX pins. Our decoded output must equal sigrok's decode of the same capture.

### L4: metamorphic

| ID | Relation |
|---|---|
| L4-LOOP | TX → RX loopback on two lanes returns the identical byte stream (every protocol that has both halves) |
| L4-SCALE | Doubling PERIOD, PRESC and delays yields a waveform exactly 2× longer with identical decoded data |
| L4-PERM | Assigning the same programs to different lanes / pin units gives identical pad waveforms (modulo pin mapping) |
| L4-IDLE | Inserting random idle time between frames never changes decoded data |
| L4-TAP | Adding or removing tap subscribers never changes any blocking-path behaviour, cycle for cycle |

### L4-IMP: impairment sweeps (robustness numbers for the report)
Clock mismatch (±ppm), jitter, glitches shorter than one sample, and slow open-drain rise. The result is a **tolerance envelope per receiver** (success rate vs impairment), plotted in the report. These are simulation-only numbers, labelled as such.

### L5: formal (SymbiYosys, white-box)

| ID | Property | Scope / engine |
|---|---|---|
| F-CHAN-1 | A token loaded into a producer is delivered **exactly once** to every enabled blocking subscriber | 1 producer, 4 consumers, abstract tokens; `abc pdr` (unbounded) |
| F-CHAN-2 | Blocking subscribers of one producer see the **same sequence** in the same order | Same |
| F-CHAN-3 | Tap subscribers never delay the producer (release time independent of tap state) | Same |
| F-CHAN-4 | Pin RX overrun keeps the old token and sets OVERRUN; nothing is silently reordered | Pin RX + channel |
| F-SCHED-1 | If slot *s* is ready and no lower-index slot is ready, *s* fires this clock | One lane; unbounded |
| F-SCHED-2 | A dynamic-flag write delays dependent slots by exactly one clock, no more | One lane |
| F-SCHED-3 | Pin-edge → pad-response ≤ 7 clocks when the reacting slot is the highest-priority ready slot and its output is free | Lane + pin unit + channel; BMC depth ≥ 16 plus induction |
| F-ROT-1 | Each SRAM requester is granted exactly on its rotation slot, independent of all other activity | Rotation arbiter; unbounded |
| F-ISO-1 | Lane isolation: the behaviour of lane *i* (its registers and outputs) is independent of lane *j*'s program, except through channels *i* subscribes to | Two copies with different j-programs (non-interference); bounded, depth stated |
| F-OWN-1 | A pad is driven only by its owner unit; open-drain pads never drive high | Pin mux; unbounded |
| F-PIN-1 | TX cursor: an action scheduled at cursor + d happens at that exact clock, or immediately with LATE set if already past | Pin TX; unbounded |
| F-HOST-1 | Host writes to slots/SRAM/config happen only while the targeted lane is halted | Host controller |
| F-DEC-1 | Every encodable slot/routine word decodes to exactly the fields the YAML defines (generated properties) | Decoder |

### L5b: program-specific formal (V4)
The formal harness loads a shipped program (slot images via `$readmemh` into the slot arrays, bypassing the host) and constrains the pins to a legal protocol environment written as assumptions. It then proves:
- **I2C target:** the ACK is driven before the next SCL fall at the configured speed; no drive on SDA while SCL is high except the intended START/STOP.
- **UART RX:** no OVERRUN at the configured baud rate with back-to-back frames.
- **SPI target:** MISO bit *n* is valid at the SCK edge where the controller samples it.

Each result must match the compiler's V1 report. Any mismatch is a bug in one of the two, logged in `BUGS.md`.

### L6: compiler checks (V1)
- **L6-STATIC:** every shipped program's report is committed and CI-checked (bounds must not regress).
- **L6-FUZZ:** random programs through `tripc` → `tripsim`. Any program the compiler calls deadlock-free must never deadlock in simulation, and every urgent reflex must meet its reported bound. This cross-checks the static analysis.

### L7: test quality
- **L7-MUT:** mutation testing (mcy or in-house) on lane, fabric and pin units. Report the kill rate per block; every surviving mutant is either explained as equivalent or leads to a new test.

### L8: gate level and physical
- **L8-GL:** the TT `gl_test` runs the pin-level suite on the hardened netlist (in the `gds` workflow).
- **L8-SDF:** timing-annotated gate-level run of the L3 suite, if the gds artefacts include SDF (to check).
- **L8-STA:** setup/hold clean at the typical sign-off corner; slow-corner status reported honestly.

---

## 7. Coverage goals (closure before RTL freeze)

| Covergroup | Bins | Goal |
|---|---|---|
| Slot fields | Every OP × DST × ASRC × BSEL; every TE/HE combination; implicit input/output/CALL checks; urgent vs normal, with and without a waiting routine step | 100% |
| Scheduler | 1–12 ready slots at once; priority winner = each index; pending-flag stall; firing during a routine | 100% |
| Channels | Blocking subscribers 0–4 × taps 0–2; producer stall; tap drop; overrun | 100% |
| Pin units | Every TX op and RX mode; LATE; STRETCH wait; AUTOREARM back-to-back; linked on rise and fall | 100% |
| Rotation | Every requester active/idle combination | 100% |
| Protocols | Each L3 protocol × speed × error case | 100% of the listed matrix |
| Code coverage | Line/toggle (Verilator) | ≥ 95% line, gaps explained |

---

## 8. Evidence and bookkeeping
- **`docs/BUGS.md`:** every bug found by any layer: date, symptom, root cause, the check ID that caught it, the check that now covers it.
- **`docs/CLAIMS.md`:** every claim in the README with its evidence and blind spot. Evidence is one of:
  - proven unbounded;
  - proven bounded to depth N;
  - tested;
  - simulated only.
- **`tools/vplan_status.py`:** lists every check ID and whether a passing test or proof exists; run in CI and published in the report.
- **`docs/VERIFICATION_REPORT.md`:** the final write-up. Numbers, the bug ledger, coverage, the mutation table, tolerance envelopes, and what was *not* verified.

---

## 9. Independence and AI-assistance rules
1. **Model and RTL are written independently** from `ARCHITECTURE.md` and the YAML. The model author does not read `src/`; the RTL author does not read `tripsim`. Tests may look at both.
2. **Protocol reference models are written from the protocol specs**, not from our firmware.
3. **Oracles we did not write** (sigrok decoders, third-party RTL, real captures) are required for every protocol claim.
4. **AI use is logged:** which files or tests were AI-drafted, who reviewed them, and which bugs AI-written tests found vs missed. The mutation kill rate (L7) is the objective score of test quality, whoever wrote the tests.
5. **A spec ambiguity found by any layer** becomes a `DECISIONS.md` entry and a spec change, never a silent RTL fix.

---

## 10. CI integration

| Workflow | Contents | Trigger |
|---|---|---|
| `test` (template, unchanged) | Pin-level cocotb suite under Icarus; fails on any failure in `results.xml` | Every push |
| `gds` (template) → `gds`, `precheck`, `gl_test`, `viewer` | Hardening, TT precheck, pin-level suite on the netlist, GitHub Pages viewer | Only when `src/`, `info.yaml` or `macro/` change (one hardware change per run) |
| `docs` (template) | Datasheet build | Every push |
| `fpga` (template, manual) | iCE40UP5K bitstream of a reduced build | Manual |
| `lint` (ours) | L0 checks, generated-file freshness | Every push |
| `unit` (ours) | L1 + L2 short seeds + L4 + L6 under Verilator | Every push |
| `formal` (ours) | L5 proofs; L5b for shipped programs | Push to `src/` or `spec/` |
| `nightly` (ours) | Long L2 lockstep, L4-IMP sweeps, L7 mutation | Scheduled |

The template's own jobs are never edited, apart from the `gds` trigger paths. Our workflows are added as separate files.

---

## 11. Exit criteria per phase

| Phase | Verification exit criteria |
|---|---|
| P1 (spec + model) | YAML + generator in place; `tripsim` runs UART/SPI/I2C programs; compiler emits V1 reports; sigrok pipeline works on model waveforms |
| P2 (RTL core) | L0, L1 green; L2 lockstep ≥ 10⁶ clocks clean; L3 UART/SPI/I2C-controller green in RTL and gate level |
| P3 (showcase) | L3 targets, 1-Wire, PS/2, pulse; L3b peers + dumps; L4 metamorphic; F-CHAN, F-SCHED, F-ROT, F-OWN proven |
| P4 (freeze) | L5b for shipped programs; coverage goals met; L2 ≥ 10⁸ clocks clean; all CI workflows green on the freeze commit |
| P5 (evidence) | L7 mutation table; L4-IMP envelopes; VERIFICATION_REPORT and CLAIMS complete |

---

## 12. Honest limits (to state in the report)
- No silicon or bench testing. All protocol behaviour is verified in simulation against independent decoders, captures and third-party RTL.
- Some formal results will be **bounded** (F-ISO-1, F-SCHED-3), with the depth stated.
- V1's deadlock/overrun guarantee covers **fixed-rate** graphs only; data-dependent graphs get warnings.
- Impairment tolerance numbers come from simulation models of real-world imperfections, not measurements.
- Gate-level simulation without SDF checks function, not timing; timing is covered by STA.